"""Tests for team CRUD endpoints."""

import uuid

from sqlalchemy import select

from app.models.menu import DrinkType, MilkOption, Size
from app.models.team import Team, TeamRole

from tests.conftest import (
    add_team_member,
    create_authenticated_client,
)


# ---------------------------------------------------------------------------
# Create Team
# ---------------------------------------------------------------------------


async def test_create_team(app, session_factory):
    authed, user = await create_authenticated_client(
        app, session_factory, f"ct_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed.post("/api/v1/teams", json={"name": "Alpha Team"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Alpha Team"
    assert data["created_by"] == str(user.id)
    assert data["member_count"] == 1
    assert data["is_active"] is True


async def test_create_team_owner_membership(app, session_factory):
    authed, user = await create_authenticated_client(
        app, session_factory, f"ctm_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed.post("/api/v1/teams", json={"name": "Beta Team"})
    team_id = resp.json()["id"]

    members_resp = await authed.get(f"/api/v1/teams/{team_id}/members")
    assert members_resp.status_code == 200
    members = members_resp.json()
    assert len(members) == 1
    assert members[0]["role"] == "owner"
    assert members[0]["email"] == user.email


async def test_create_team_seeds_menu(app, session_factory, db):
    authed, user = await create_authenticated_client(
        app, session_factory, f"seed_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed.post("/api/v1/teams", json={"name": "Seed Team"})
    team_id = uuid.UUID(resp.json()["id"])

    drinks = (
        (await db.execute(select(DrinkType).where(DrinkType.team_id == team_id))).scalars().all()
    )
    sizes = (await db.execute(select(Size).where(Size.team_id == team_id))).scalars().all()
    milks = (
        (await db.execute(select(MilkOption).where(MilkOption.team_id == team_id))).scalars().all()
    )
    assert len(drinks) == 10
    assert len(sizes) == 3
    assert len(milks) == 5


async def test_create_team_unauthenticated(client):
    resp = await client.post("/api/v1/teams", json={"name": "Nope"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# List Teams
# ---------------------------------------------------------------------------


async def test_list_teams_empty(app, session_factory):
    authed, _ = await create_authenticated_client(
        app, session_factory, f"empty_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed.get("/api/v1/teams")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_teams_returns_own_teams(app, session_factory):
    authed, user = await create_authenticated_client(
        app, session_factory, f"list_{uuid.uuid4().hex[:8]}@example.com"
    )
    await authed.post("/api/v1/teams", json={"name": "Team A"})
    await authed.post("/api/v1/teams", json={"name": "Team B"})
    resp = await authed.get("/api/v1/teams")
    assert resp.status_code == 200
    names = {t["name"] for t in resp.json()}
    assert "Team A" in names
    assert "Team B" in names


async def test_list_teams_excludes_soft_deleted(app, session_factory):
    authed, user = await create_authenticated_client(
        app, session_factory, f"softdel_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed.post("/api/v1/teams", json={"name": "To Delete"})
    team_id = resp.json()["id"]
    await authed.delete(f"/api/v1/teams/{team_id}")

    resp = await authed.get("/api/v1/teams")
    teams = resp.json()
    assert all(t["id"] != team_id for t in teams)


# ---------------------------------------------------------------------------
# Get Team
# ---------------------------------------------------------------------------


async def test_get_team(app, session_factory):
    authed, user = await create_authenticated_client(
        app, session_factory, f"get_{uuid.uuid4().hex[:8]}@example.com"
    )
    create_resp = await authed.post("/api/v1/teams", json={"name": "Get Me"})
    team_id = create_resp.json()["id"]
    resp = await authed.get(f"/api/v1/teams/{team_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Me"
    assert resp.json()["member_count"] == 1


async def test_get_team_non_member(app, session_factory):
    authed_a, _ = await create_authenticated_client(
        app, session_factory, f"getnm_a_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed_a.post("/api/v1/teams", json={"name": "Secret"})
    team_id = resp.json()["id"]

    authed_b, _ = await create_authenticated_client(
        app, session_factory, f"getnm_b_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed_b.get(f"/api/v1/teams/{team_id}")
    assert resp.status_code == 403


async def test_get_team_invalid_id(app, session_factory):
    authed, _ = await create_authenticated_client(
        app, session_factory, f"getinv_{uuid.uuid4().hex[:8]}@example.com"
    )
    fake_id = uuid.uuid4()
    resp = await authed.get(f"/api/v1/teams/{fake_id}")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Update Team
# ---------------------------------------------------------------------------


async def test_update_team_owner(app, session_factory):
    authed, user = await create_authenticated_client(
        app, session_factory, f"upd_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed.post("/api/v1/teams", json={"name": "Old Name"})
    team_id = resp.json()["id"]

    resp = await authed.put(f"/api/v1/teams/{team_id}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


async def test_update_team_manager_forbidden(app, session_factory, db):
    authed_owner, owner = await create_authenticated_client(
        app, session_factory, f"updmgr_o_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed_owner.post("/api/v1/teams", json={"name": "Mgr Test"})
    team_id = resp.json()["id"]

    manager_client, manager = await create_authenticated_client(
        app, session_factory, f"updmgr_m_{uuid.uuid4().hex[:8]}@example.com"
    )
    team = (await db.execute(select(Team).where(Team.id == uuid.UUID(team_id)))).scalar_one()
    await add_team_member(db, team, manager, TeamRole.manager)

    resp = await manager_client.put(f"/api/v1/teams/{team_id}", json={"name": "Nope"})
    assert resp.status_code == 403


async def test_update_team_member_forbidden(app, session_factory, db):
    authed_owner, owner = await create_authenticated_client(
        app, session_factory, f"updmem_o_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed_owner.post("/api/v1/teams", json={"name": "Mem Test"})
    team_id = resp.json()["id"]

    member_client, member = await create_authenticated_client(
        app, session_factory, f"updmem_m_{uuid.uuid4().hex[:8]}@example.com"
    )
    team = (await db.execute(select(Team).where(Team.id == uuid.UUID(team_id)))).scalar_one()
    await add_team_member(db, team, member, TeamRole.member)

    resp = await member_client.put(f"/api/v1/teams/{team_id}", json={"name": "Nope"})
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Delete Team (soft-delete)
# ---------------------------------------------------------------------------


async def test_delete_team_owner(app, session_factory):
    authed, _ = await create_authenticated_client(
        app, session_factory, f"del_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed.post("/api/v1/teams", json={"name": "Bye"})
    team_id = resp.json()["id"]

    resp = await authed.delete(f"/api/v1/teams/{team_id}")
    assert resp.status_code == 200

    resp = await authed.get("/api/v1/teams")
    assert all(t["id"] != team_id for t in resp.json())


async def test_delete_team_manager_forbidden(app, session_factory, db):
    authed_owner, owner = await create_authenticated_client(
        app, session_factory, f"delmgr_o_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed_owner.post("/api/v1/teams", json={"name": "Del Mgr"})
    team_id = resp.json()["id"]

    mgr_client, mgr = await create_authenticated_client(
        app, session_factory, f"delmgr_m_{uuid.uuid4().hex[:8]}@example.com"
    )
    team = (await db.execute(select(Team).where(Team.id == uuid.UUID(team_id)))).scalar_one()
    await add_team_member(db, team, mgr, TeamRole.manager)

    resp = await mgr_client.delete(f"/api/v1/teams/{team_id}")
    assert resp.status_code == 403
