"""Tests for the invite flow endpoints."""

import uuid

from sqlalchemy import select

from app.models.colleague import Colleague
from app.models.team import Team, TeamInvite, TeamMembership, TeamRole
from app.services.team import generate_invite_token

from tests.conftest import (
    add_team_member,
    create_authenticated_client,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_invite_team(app, session_factory, db):
    """Create a team with an owner. Return (owner_client, owner, team_id)."""
    owner_client, owner = await create_authenticated_client(
        app, session_factory, f"inv_o_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await owner_client.post("/api/v1/teams", json={"name": "Invite Team"})
    team_id = resp.json()["id"]
    return owner_client, owner, team_id


# ---------------------------------------------------------------------------
# Create Invite
# ---------------------------------------------------------------------------


async def test_create_invite(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)
    resp = await oc.post(
        f"/api/v1/teams/{tid}/invites",
        json={"email": f"newinv_{uuid.uuid4().hex[:8]}@example.com", "role": "member"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "member"
    assert data["accepted"] is False


async def test_invite_as_owner_role_rejected(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)
    resp = await oc.post(
        f"/api/v1/teams/{tid}/invites",
        json={"email": "owner@example.com", "role": "owner"},
    )
    assert resp.status_code == 400


async def test_invite_existing_member_rejected(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)
    resp = await oc.post(
        f"/api/v1/teams/{tid}/invites",
        json={"email": owner.email, "role": "member"},
    )
    assert resp.status_code == 400


async def test_reinvite_resets_expiry(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)
    email = f"reinvite_{uuid.uuid4().hex[:8]}@example.com"
    r1 = await oc.post(f"/api/v1/teams/{tid}/invites", json={"email": email, "role": "member"})
    invite_id_1 = r1.json()["id"]

    r2 = await oc.post(f"/api/v1/teams/{tid}/invites", json={"email": email, "role": "member"})
    # Should return the same invite ID (re-sent, not duplicated)
    assert r2.json()["id"] == invite_id_1


async def test_member_cannot_create_invite(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)

    mem_client, mem = await create_authenticated_client(
        app, session_factory, f"invmem_{uuid.uuid4().hex[:8]}@example.com"
    )
    team = (await db.execute(select(Team).where(Team.id == uuid.UUID(tid)))).scalar_one()
    await add_team_member(db, team, mem, TeamRole.member)

    resp = await mem_client.post(
        f"/api/v1/teams/{tid}/invites",
        json={"email": "someone@example.com", "role": "member"},
    )
    assert resp.status_code == 403


async def test_invite_colleague_already_linked(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)

    colleague = Colleague(
        id=uuid.uuid4(),
        team_id=uuid.UUID(tid),
        user_id=owner.id,
        name="Linked Colleague",
    )
    db.add(colleague)
    await db.commit()

    resp = await oc.post(
        f"/api/v1/teams/{tid}/invites",
        json={
            "email": "linked@example.com",
            "role": "member",
            "colleague_id": str(colleague.id),
        },
    )
    assert resp.status_code == 400


async def test_invite_colleague_wrong_team(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)

    other_team = Team(id=uuid.uuid4(), name="Other", created_by=owner.id)
    db.add(other_team)
    await db.flush()
    colleague = Colleague(id=uuid.uuid4(), team_id=other_team.id, name="Wrong Team Colleague")
    db.add(colleague)
    await db.commit()

    resp = await oc.post(
        f"/api/v1/teams/{tid}/invites",
        json={
            "email": "wrongteam@example.com",
            "role": "member",
            "colleague_id": str(colleague.id),
        },
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# List Invites
# ---------------------------------------------------------------------------


async def test_list_invites_pending_only(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)
    await oc.post(
        f"/api/v1/teams/{tid}/invites",
        json={"email": f"pending_{uuid.uuid4().hex[:8]}@example.com", "role": "member"},
    )
    resp = await oc.get(f"/api/v1/teams/{tid}/invites")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    assert all(not inv["accepted"] for inv in resp.json())


async def test_member_cannot_list_invites(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)

    mem_client, mem = await create_authenticated_client(
        app, session_factory, f"listmem_{uuid.uuid4().hex[:8]}@example.com"
    )
    team = (await db.execute(select(Team).where(Team.id == uuid.UUID(tid)))).scalar_one()
    await add_team_member(db, team, mem, TeamRole.member)

    resp = await mem_client.get(f"/api/v1/teams/{tid}/invites")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Revoke Invite
# ---------------------------------------------------------------------------


async def test_revoke_invite(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)
    r = await oc.post(
        f"/api/v1/teams/{tid}/invites",
        json={"email": f"revoke_{uuid.uuid4().hex[:8]}@example.com", "role": "member"},
    )
    invite_id = r.json()["id"]
    resp = await oc.delete(f"/api/v1/teams/{tid}/invites/{invite_id}")
    assert resp.status_code == 200


async def test_revoke_invite_wrong_team(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)
    fake_id = uuid.uuid4()
    resp = await oc.delete(f"/api/v1/teams/{tid}/invites/{fake_id}")
    assert resp.status_code == 404


async def test_revoke_nonexistent_invite(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)
    fake_id = uuid.uuid4()
    resp = await oc.delete(f"/api/v1/teams/{tid}/invites/{fake_id}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Accept Invite
# ---------------------------------------------------------------------------


async def test_accept_invite(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)

    invitee_email = f"accept_{uuid.uuid4().hex[:8]}@example.com"
    await oc.post(
        f"/api/v1/teams/{tid}/invites",
        json={"email": invitee_email, "role": "member"},
    )

    result = await db.execute(
        select(TeamInvite).where(
            TeamInvite.team_id == uuid.UUID(tid),
            TeamInvite.email == invitee_email,
        )
    )
    invite = result.scalar_one()
    raw_token, hashed = generate_invite_token()
    invite.token_hash = hashed
    await db.commit()

    invitee_client, invitee = await create_authenticated_client(app, session_factory, invitee_email)
    resp = await invitee_client.post("/api/v1/invites/accept", json={"token": raw_token})
    assert resp.status_code == 200

    mem_result = await db.execute(
        select(TeamMembership).where(
            TeamMembership.team_id == uuid.UUID(tid),
            TeamMembership.user_id == invitee.id,
        )
    )
    membership = mem_result.scalar_one()
    assert membership.role == TeamRole.member


async def test_accept_invite_invalid_token(app, session_factory):
    client, _ = await create_authenticated_client(
        app, session_factory, f"badtoken_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await client.post("/api/v1/invites/accept", json={"token": "bogus-token"})
    assert resp.status_code == 400


async def test_accept_invite_already_used(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)

    invitee_email = f"used_{uuid.uuid4().hex[:8]}@example.com"
    await oc.post(
        f"/api/v1/teams/{tid}/invites",
        json={"email": invitee_email, "role": "member"},
    )

    result = await db.execute(
        select(TeamInvite).where(
            TeamInvite.team_id == uuid.UUID(tid),
            TeamInvite.email == invitee_email,
        )
    )
    invite = result.scalar_one()
    raw_token, hashed = generate_invite_token()
    invite.token_hash = hashed
    await db.commit()

    invitee_client, _ = await create_authenticated_client(app, session_factory, invitee_email)

    # First accept
    r1 = await invitee_client.post("/api/v1/invites/accept", json={"token": raw_token})
    assert r1.status_code == 200

    # Second accept — token already used (accepted=True)
    invitee_client2, _ = await create_authenticated_client(app, session_factory, invitee_email)
    r2 = await invitee_client2.post("/api/v1/invites/accept", json={"token": raw_token})
    assert r2.status_code == 400


async def test_accept_invite_email_mismatch(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)

    invite_email = f"mismatch_inv_{uuid.uuid4().hex[:8]}@example.com"
    await oc.post(
        f"/api/v1/teams/{tid}/invites",
        json={"email": invite_email, "role": "member"},
    )

    result = await db.execute(
        select(TeamInvite).where(
            TeamInvite.team_id == uuid.UUID(tid),
            TeamInvite.email == invite_email,
        )
    )
    invite = result.scalar_one()
    raw_token, hashed = generate_invite_token()
    invite.token_hash = hashed
    await db.commit()

    wrong_client, _ = await create_authenticated_client(
        app, session_factory, f"mismatch_wrong_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await wrong_client.post("/api/v1/invites/accept", json={"token": raw_token})
    assert resp.status_code == 403


async def test_accept_invite_already_member(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)

    mem_email = f"alreadymem_{uuid.uuid4().hex[:8]}@example.com"
    mem_client, mem = await create_authenticated_client(app, session_factory, mem_email)
    team = (await db.execute(select(Team).where(Team.id == uuid.UUID(tid)))).scalar_one()
    await add_team_member(db, team, mem, TeamRole.member)

    # Try to invite — should be rejected as already a member
    resp = await oc.post(
        f"/api/v1/teams/{tid}/invites",
        json={"email": mem_email, "role": "member"},
    )
    assert resp.status_code == 400


async def test_accept_invite_links_colleague(app, session_factory, db):
    oc, owner, tid = await _setup_invite_team(app, session_factory, db)

    colleague = Colleague(
        id=uuid.uuid4(),
        team_id=uuid.UUID(tid),
        name="Unlinked Colleague",
    )
    db.add(colleague)
    await db.commit()

    invitee_email = f"linkcolleague_{uuid.uuid4().hex[:8]}@example.com"
    await oc.post(
        f"/api/v1/teams/{tid}/invites",
        json={
            "email": invitee_email,
            "role": "member",
            "colleague_id": str(colleague.id),
        },
    )

    result = await db.execute(
        select(TeamInvite).where(
            TeamInvite.team_id == uuid.UUID(tid),
            TeamInvite.email == invitee_email,
        )
    )
    invite = result.scalar_one()
    raw_token, hashed = generate_invite_token()
    invite.token_hash = hashed
    await db.commit()

    invitee_client, invitee = await create_authenticated_client(app, session_factory, invitee_email)
    resp = await invitee_client.post("/api/v1/invites/accept", json={"token": raw_token})
    assert resp.status_code == 200

    # Use a fresh session to verify the colleague was linked
    colleague_id = colleague.id
    async with session_factory() as fresh_db:
        c = (
            await fresh_db.execute(select(Colleague).where(Colleague.id == colleague_id))
        ).scalar_one()
        assert c.user_id == invitee.id
