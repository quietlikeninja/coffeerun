"""Tests for membership management endpoints."""

import uuid

from sqlalchemy import select

from app.models.team import Team, TeamRole

from tests.conftest import (
    add_team_member,
    create_authenticated_client,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_team_with_roles(app, session_factory, db):
    """Create a team with owner, manager, and member. Return clients + team_id."""
    owner_client, owner = await create_authenticated_client(
        app, session_factory, f"mo_{uuid.uuid4().hex[:8]}@example.com"
    )

    resp = await owner_client.post("/api/v1/teams", json={"name": "Roles Team"})
    team_id = resp.json()["id"]

    team = (await db.execute(select(Team).where(Team.id == uuid.UUID(team_id)))).scalar_one()

    mgr_client, mgr = await create_authenticated_client(
        app, session_factory, f"mm_{uuid.uuid4().hex[:8]}@example.com"
    )
    await add_team_member(db, team, mgr, TeamRole.manager)

    mem_client, mem = await create_authenticated_client(
        app, session_factory, f"mb_{uuid.uuid4().hex[:8]}@example.com"
    )
    await add_team_member(db, team, mem, TeamRole.member)

    return team_id, owner_client, owner, mgr_client, mgr, mem_client, mem


# ---------------------------------------------------------------------------
# List Members
# ---------------------------------------------------------------------------


async def test_list_members_sorted(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await oc.get(f"/api/v1/teams/{tid}/members")
    assert resp.status_code == 200
    roles = [m["role"] for m in resp.json()]
    assert roles[0] == "owner"
    assert "manager" in roles
    assert "member" in roles


async def test_list_members_includes_email(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await oc.get(f"/api/v1/teams/{tid}/members")
    emails = {m["email"] for m in resp.json()}
    assert owner.email in emails
    assert mgr.email in emails
    assert mem.email in emails


# ---------------------------------------------------------------------------
# Update Member Role — Happy paths
# ---------------------------------------------------------------------------


async def test_owner_promotes_member_to_manager(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await oc.put(f"/api/v1/teams/{tid}/members/{mem.id}", json={"role": "manager"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "manager"


async def test_owner_demotes_manager_to_member(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await oc.put(f"/api/v1/teams/{tid}/members/{mgr.id}", json={"role": "member"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "member"


async def test_owner_transfers_ownership(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await oc.put(f"/api/v1/teams/{tid}/members/{mem.id}", json={"role": "owner"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "owner"

    # Old owner should now be manager
    members_resp = await oc.get(f"/api/v1/teams/{tid}/members")
    owner_entry = next(m for m in members_resp.json() if m["user_id"] == str(owner.id))
    assert owner_entry["role"] == "manager"


async def test_manager_promotes_member_to_manager(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await mc.put(f"/api/v1/teams/{tid}/members/{mem.id}", json={"role": "manager"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "manager"


# ---------------------------------------------------------------------------
# Update Member Role — Constraint enforcement
# ---------------------------------------------------------------------------


async def test_manager_cannot_promote_to_owner(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await mc.put(f"/api/v1/teams/{tid}/members/{mem.id}", json={"role": "owner"})
    assert resp.status_code == 403


async def test_manager_cannot_demote_another_manager(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    mgr2_client, mgr2 = await create_authenticated_client(
        app, session_factory, f"mgr2_{uuid.uuid4().hex[:8]}@example.com"
    )
    team = (await db.execute(select(Team).where(Team.id == uuid.UUID(tid)))).scalar_one()
    await add_team_member(db, team, mgr2, TeamRole.manager)

    resp = await mc.put(f"/api/v1/teams/{tid}/members/{mgr2.id}", json={"role": "member"})
    assert resp.status_code == 403


async def test_manager_cannot_modify_owner(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await mc.put(f"/api/v1/teams/{tid}/members/{owner.id}", json={"role": "member"})
    assert resp.status_code == 403


async def test_cannot_change_own_role(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await oc.put(f"/api/v1/teams/{tid}/members/{owner.id}", json={"role": "member"})
    assert resp.status_code == 400


async def test_invalid_role_value(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await oc.put(f"/api/v1/teams/{tid}/members/{mem.id}", json={"role": "superadmin"})
    assert resp.status_code == 400


async def test_update_nonexistent_member(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    fake_id = uuid.uuid4()
    resp = await oc.put(f"/api/v1/teams/{tid}/members/{fake_id}", json={"role": "manager"})
    assert resp.status_code == 404


async def test_member_cannot_update_roles(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    mem2_client, mem2 = await create_authenticated_client(
        app, session_factory, f"mem2_{uuid.uuid4().hex[:8]}@example.com"
    )
    team = (await db.execute(select(Team).where(Team.id == uuid.UUID(tid)))).scalar_one()
    await add_team_member(db, team, mem2, TeamRole.member)

    resp = await memc.put(f"/api/v1/teams/{tid}/members/{mem2.id}", json={"role": "manager"})
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Remove Member
# ---------------------------------------------------------------------------


async def test_owner_removes_member(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await oc.delete(f"/api/v1/teams/{tid}/members/{mem.id}")
    assert resp.status_code == 200


async def test_owner_removes_manager(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await oc.delete(f"/api/v1/teams/{tid}/members/{mgr.id}")
    assert resp.status_code == 200


async def test_cannot_remove_owner(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await mc.delete(f"/api/v1/teams/{tid}/members/{owner.id}")
    assert resp.status_code == 400


async def test_manager_removes_member(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    resp = await mc.delete(f"/api/v1/teams/{tid}/members/{mem.id}")
    assert resp.status_code == 200


async def test_manager_cannot_remove_another_manager(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    mgr2_client, mgr2 = await create_authenticated_client(
        app, session_factory, f"rmgr2_{uuid.uuid4().hex[:8]}@example.com"
    )
    team = (await db.execute(select(Team).where(Team.id == uuid.UUID(tid)))).scalar_one()
    await add_team_member(db, team, mgr2, TeamRole.manager)

    resp = await mc.delete(f"/api/v1/teams/{tid}/members/{mgr2.id}")
    assert resp.status_code == 403


async def test_member_cannot_remove_anyone(app, session_factory, db):
    tid, oc, owner, mc, mgr, memc, mem = await _setup_team_with_roles(app, session_factory, db)
    mem2_client, mem2 = await create_authenticated_client(
        app, session_factory, f"rmem2_{uuid.uuid4().hex[:8]}@example.com"
    )
    team = (await db.execute(select(Team).where(Team.id == uuid.UUID(tid)))).scalar_one()
    await add_team_member(db, team, mem2, TeamRole.member)

    resp = await memc.delete(f"/api/v1/teams/{tid}/members/{mem2.id}")
    assert resp.status_code == 403
