import uuid
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.team import TeamMembership, TeamRole
from app.models.user import User
from app.services.auth import decode_jwt


@dataclass
class CurrentUser:
    id: uuid.UUID
    email: str


@dataclass
class TeamMember:
    id: uuid.UUID
    email: str
    team_id: uuid.UUID
    role: TeamRole


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> CurrentUser:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return CurrentUser(id=user.id, email=user.email)


async def get_team_member(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamMember:
    team_id = request.path_params.get("team_id")
    if not team_id:
        raise HTTPException(status_code=400, detail="team_id path parameter required")

    try:
        team_uuid = uuid.UUID(str(team_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid team_id format")

    result = await db.execute(
        select(TeamMembership).where(
            TeamMembership.team_id == team_uuid,
            TeamMembership.user_id == current_user.id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    return TeamMember(
        id=current_user.id,
        email=current_user.email,
        team_id=team_uuid,
        role=membership.role,
    )


def require_role(*roles: TeamRole) -> Callable:
    async def dependency(
        team_member: TeamMember = Depends(get_team_member),
    ) -> TeamMember:
        if team_member.role not in roles:
            role_names = " or ".join(r.value for r in roles)
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient role. Required: {role_names}",
            )
        return team_member

    return dependency
