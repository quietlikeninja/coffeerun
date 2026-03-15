import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.middleware.auth import (
    CurrentUser,
    TeamMember,
    get_current_user,
    get_team_member,
    require_role,
)
from app.models.colleague import Colleague
from app.models.team import Team, TeamInvite, TeamMembership, TeamRole
from app.models.user import User
from app.schemas.team import (
    InviteAccept,
    InviteCreate,
    InviteResponse,
    TeamCreate,
    TeamMemberResponse,
    TeamMemberUpdate,
    TeamResponse,
    TeamUpdate,
)
from app.services.email import send_team_invite_email
from app.services.team import generate_invite_token, seed_team_menu, verify_invite_token

router = APIRouter(tags=["teams"])


# ---------------------------------------------------------------------------
# Team CRUD
# ---------------------------------------------------------------------------


@router.post("/teams", response_model=TeamResponse)
async def create_team(
    body: TeamCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = Team(name=body.name, created_by=current_user.id)
    db.add(team)
    await db.flush()

    membership = TeamMembership(team_id=team.id, user_id=current_user.id, role=TeamRole.owner)
    db.add(membership)
    await db.flush()

    await seed_team_menu(db, team.id)

    return TeamResponse(
        id=team.id,
        name=team.name,
        created_by=team.created_by,
        is_active=team.is_active,
        member_count=1,
        created_at=team.created_at,
    )


@router.get("/teams", response_model=list[TeamResponse])
async def list_teams(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Subquery for member counts
    member_count_sq = (
        select(
            TeamMembership.team_id,
            func.count().label("member_count"),
        )
        .group_by(TeamMembership.team_id)
        .subquery()
    )

    result = await db.execute(
        select(Team, member_count_sq.c.member_count)
        .join(TeamMembership, Team.id == TeamMembership.team_id)
        .outerjoin(member_count_sq, Team.id == member_count_sq.c.team_id)
        .where(
            TeamMembership.user_id == current_user.id,
            Team.is_active == True,  # noqa: E712
        )
    )
    rows = result.all()
    return [
        TeamResponse(
            id=team.id,
            name=team.name,
            created_by=team.created_by,
            is_active=team.is_active,
            member_count=count or 0,
            created_at=team.created_at,
        )
        for team, count in rows
    ]


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: uuid.UUID,
    team_member: TeamMember = Depends(get_team_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    count_result = await db.execute(select(func.count()).where(TeamMembership.team_id == team_id))
    member_count = count_result.scalar() or 0

    return TeamResponse(
        id=team.id,
        name=team.name,
        created_by=team.created_by,
        is_active=team.is_active,
        member_count=member_count,
        created_at=team.created_at,
    )


@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: uuid.UUID,
    body: TeamUpdate,
    team_member: TeamMember = Depends(require_role(TeamRole.owner)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if body.name is not None:
        team.name = body.name
    await db.flush()

    count_result = await db.execute(select(func.count()).where(TeamMembership.team_id == team_id))
    member_count = count_result.scalar() or 0

    return TeamResponse(
        id=team.id,
        name=team.name,
        created_by=team.created_by,
        is_active=team.is_active,
        member_count=member_count,
        created_at=team.created_at,
    )


@router.delete("/teams/{team_id}", response_model=dict)
async def delete_team(
    team_id: uuid.UUID,
    team_member: TeamMember = Depends(require_role(TeamRole.owner)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    team.is_active = False
    await db.flush()
    return {"message": "Team deleted"}


# ---------------------------------------------------------------------------
# Membership management
# ---------------------------------------------------------------------------


@router.get("/teams/{team_id}/members", response_model=list[TeamMemberResponse])
async def list_members(
    team_id: uuid.UUID,
    team_member: TeamMember = Depends(get_team_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TeamMembership)
        .where(TeamMembership.team_id == team_id)
        .options(selectinload(TeamMembership.user))
    )
    memberships = result.scalars().all()

    # Sort: owner first, then manager, then member; within same role by email
    role_order = {TeamRole.owner: 0, TeamRole.manager: 1, TeamRole.member: 2}
    memberships = sorted(memberships, key=lambda m: (role_order.get(m.role, 3), m.user.email))

    return [
        TeamMemberResponse(
            id=m.id,
            user_id=m.user_id,
            email=m.user.email,
            display_name=m.user.display_name,
            role=m.role.value,
            created_at=m.created_at,
        )
        for m in memberships
    ]


@router.put("/teams/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_member_role(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    body: TeamMemberUpdate,
    team_member: TeamMember = Depends(require_role(TeamRole.owner, TeamRole.manager)),
    db: AsyncSession = Depends(get_db),
):
    # Validate requested role
    try:
        new_role = TeamRole(body.role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(r.value for r in TeamRole)}",
        )

    # Cannot change your own role
    if user_id == team_member.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    # Look up the target membership
    result = await db.execute(
        select(TeamMembership)
        .where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user_id,
        )
        .options(selectinload(TeamMembership.user))
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    # Manager constraints
    if team_member.role == TeamRole.manager:
        if target.role == TeamRole.owner:
            raise HTTPException(status_code=403, detail="Managers cannot modify the Owner's role")
        if target.role == TeamRole.manager:
            raise HTTPException(
                status_code=403, detail="Managers cannot modify other Managers' roles"
            )
        if new_role == TeamRole.owner:
            raise HTTPException(status_code=403, detail="Managers cannot promote to Owner")

    # Ownership transfer: auto-demote current owner
    if new_role == TeamRole.owner:
        current_owner_result = await db.execute(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.role == TeamRole.owner,
            )
        )
        current_owner = current_owner_result.scalar_one_or_none()
        if current_owner:
            current_owner.role = TeamRole.manager

    target.role = new_role
    await db.flush()
    await db.refresh(target)

    return TeamMemberResponse(
        id=target.id,
        user_id=target.user_id,
        email=target.user.email,
        display_name=target.user.display_name,
        role=target.role.value,
        created_at=target.created_at,
    )


@router.delete("/teams/{team_id}/members/{user_id}", response_model=dict)
async def remove_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    team_member: TeamMember = Depends(require_role(TeamRole.owner, TeamRole.manager)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user_id,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    # Cannot remove the owner
    if target.role == TeamRole.owner:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove the Owner. Transfer ownership first.",
        )

    # Managers cannot remove other managers
    if team_member.role == TeamRole.manager and target.role == TeamRole.manager:
        raise HTTPException(status_code=403, detail="Managers cannot remove other Managers")

    await db.delete(target)
    await db.flush()
    return {"message": "Member removed"}


# ---------------------------------------------------------------------------
# Invites
# ---------------------------------------------------------------------------


@router.post("/teams/{team_id}/invites", response_model=InviteResponse)
async def create_invite(
    team_id: uuid.UUID,
    body: InviteCreate,
    team_member: TeamMember = Depends(require_role(TeamRole.owner, TeamRole.manager)),
    db: AsyncSession = Depends(get_db),
):
    # Cannot invite as owner
    if body.role == TeamRole.owner.value:
        raise HTTPException(
            status_code=400,
            detail="Cannot invite directly as Owner. Promote after joining.",
        )

    # Validate role value
    try:
        invite_role = TeamRole(body.role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. Must be one of: manager, member",
        )

    # Check if already a member
    existing_member = await db.execute(
        select(TeamMembership)
        .join(User, TeamMembership.user_id == User.id)
        .where(
            TeamMembership.team_id == team_id,
            User.email == body.email.lower(),
        )
    )
    if existing_member.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"{body.email} is already a member of this team",
        )

    # If colleague_id provided, validate it
    if body.colleague_id:
        colleague_result = await db.execute(
            select(Colleague).where(
                Colleague.id == body.colleague_id,
                Colleague.team_id == team_id,
            )
        )
        colleague = colleague_result.scalar_one_or_none()
        if not colleague:
            raise HTTPException(status_code=400, detail="Colleague not found in this team")
        if colleague.user_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Colleague is already linked to a user",
            )

    # Check for existing unexpired, unaccepted invite
    existing_invite_result = await db.execute(
        select(TeamInvite).where(
            TeamInvite.team_id == team_id,
            TeamInvite.email == body.email.lower(),
            TeamInvite.accepted == False,  # noqa: E712
            TeamInvite.expires_at > datetime.now(timezone.utc),
        )
    )
    existing_invite = existing_invite_result.scalar_one_or_none()

    if existing_invite:
        # Re-send: reset expiry and re-send email
        existing_invite.expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.invite_expiry_days
        )
        await db.flush()

        raw_token, _ = generate_invite_token()
        existing_invite.token_hash = __import__("hashlib").sha256(raw_token.encode()).hexdigest()
        await db.flush()

        # Get team name for email
        team_result = await db.execute(select(Team).where(Team.id == team_id))
        team = team_result.scalar_one()

        await send_team_invite_email(body.email, raw_token, team.name, team_member.email)

        return InviteResponse(
            id=existing_invite.id,
            team_id=existing_invite.team_id,
            email=existing_invite.email,
            role=existing_invite.role.value,
            colleague_id=existing_invite.colleague_id,
            invited_by=existing_invite.invited_by,
            expires_at=existing_invite.expires_at,
            accepted=existing_invite.accepted,
            created_at=existing_invite.created_at,
        )

    # Create new invite
    raw_token, token_hash = generate_invite_token()

    invite = TeamInvite(
        team_id=team_id,
        email=body.email.lower(),
        role=invite_role,
        colleague_id=body.colleague_id,
        token_hash=token_hash,
        invited_by=team_member.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.invite_expiry_days),
    )
    db.add(invite)
    await db.flush()

    # Get team name for email
    team_result = await db.execute(select(Team).where(Team.id == team_id))
    team = team_result.scalar_one()

    await send_team_invite_email(body.email, raw_token, team.name, team_member.email)

    return InviteResponse(
        id=invite.id,
        team_id=invite.team_id,
        email=invite.email,
        role=invite.role.value,
        colleague_id=invite.colleague_id,
        invited_by=invite.invited_by,
        expires_at=invite.expires_at,
        accepted=invite.accepted,
        created_at=invite.created_at,
    )


@router.get("/teams/{team_id}/invites", response_model=list[InviteResponse])
async def list_invites(
    team_id: uuid.UUID,
    team_member: TeamMember = Depends(require_role(TeamRole.owner, TeamRole.manager)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TeamInvite).where(
            TeamInvite.team_id == team_id,
            TeamInvite.accepted == False,  # noqa: E712
            TeamInvite.expires_at > datetime.now(timezone.utc),
        )
    )
    invites = result.scalars().all()
    return [
        InviteResponse(
            id=inv.id,
            team_id=inv.team_id,
            email=inv.email,
            role=inv.role.value,
            colleague_id=inv.colleague_id,
            invited_by=inv.invited_by,
            expires_at=inv.expires_at,
            accepted=inv.accepted,
            created_at=inv.created_at,
        )
        for inv in invites
    ]


@router.delete("/teams/{team_id}/invites/{invite_id}", response_model=dict)
async def revoke_invite(
    team_id: uuid.UUID,
    invite_id: uuid.UUID,
    team_member: TeamMember = Depends(require_role(TeamRole.owner, TeamRole.manager)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TeamInvite).where(
            TeamInvite.id == invite_id,
            TeamInvite.team_id == team_id,
        )
    )
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    await db.delete(invite)
    await db.flush()
    return {"message": "Invite revoked"}


# ---------------------------------------------------------------------------
# Accept invite (not under /teams/{team_id})
# ---------------------------------------------------------------------------


@router.post("/invites/accept", response_model=dict)
async def accept_invite(
    body: InviteAccept,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invite = await verify_invite_token(db, body.token)
    if not invite:
        raise HTTPException(status_code=400, detail="Invalid or expired invite token")

    # Email must match
    if current_user.email.lower() != invite.email.lower():
        raise HTTPException(
            status_code=403,
            detail="This invite was sent to a different email address",
        )

    # Check if already a member
    existing = await db.execute(
        select(TeamMembership).where(
            TeamMembership.team_id == invite.team_id,
            TeamMembership.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        invite.accepted = True
        await db.flush()
        return {"message": "You are already a member of this team"}

    # Create membership
    membership = TeamMembership(
        team_id=invite.team_id,
        user_id=current_user.id,
        role=invite.role,
    )
    db.add(membership)

    # Link colleague profile if specified
    if invite.colleague_id:
        colleague_result = await db.execute(
            select(Colleague).where(Colleague.id == invite.colleague_id)
        )
        colleague = colleague_result.scalar_one_or_none()
        if colleague and colleague.user_id is None:
            colleague.user_id = current_user.id

    invite.accepted = True
    await db.flush()

    # Get team name for response
    team_result = await db.execute(select(Team).where(Team.id == invite.team_id))
    team = team_result.scalar_one()

    return {"message": f"Successfully joined {team.name}"}
