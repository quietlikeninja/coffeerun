"""Tests for team-scoped colleague endpoints."""

import uuid

from tests.conftest import (
    add_team_member,
    create_authenticated_client,
    create_colleague,
    create_team_with_owner,
    create_test_user,
)

from app.models.team import TeamRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup(app, session_factory, db):
    """Create owner + team, return (owner_client, owner, team, team_id)."""
    owner_client, owner = await create_authenticated_client(
        app, session_factory, f"co_{uuid.uuid4().hex[:8]}@example.com"
    )
    async with session_factory() as s:
        owner_u = await create_test_user(s, owner.email)
        team = await create_team_with_owner(s, owner_u, "Colleague Team")
    return owner_client, owner, team, str(team.id)


# ---------------------------------------------------------------------------
# List Colleagues
# ---------------------------------------------------------------------------


async def test_list_colleagues_empty(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    resp = await oc.get(f"/api/v1/teams/{tid}/colleagues")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_colleagues_returns_team_scoped(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    await create_colleague(db, team, "Alice")
    await create_colleague(db, team, "Bob")
    resp = await oc.get(f"/api/v1/teams/{tid}/colleagues")
    assert resp.status_code == 200
    names = {c["name"] for c in resp.json()}
    assert "Alice" in names
    assert "Bob" in names


async def test_list_colleagues_filter_by_type(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    await create_colleague(db, team, "RegularPerson")
    await create_colleague(db, team, "VisitorPerson", colleague_type="visitor")

    resp = await oc.get(f"/api/v1/teams/{tid}/colleagues?colleague_type=visitor")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "VisitorPerson" in names
    assert "RegularPerson" not in names


async def test_list_colleagues_includes_type_and_user_id(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    await create_colleague(db, team, "TypedColleague", user_id=owner.id)
    resp = await oc.get(f"/api/v1/teams/{tid}/colleagues")
    assert resp.status_code == 200
    c = next(x for x in resp.json() if x["name"] == "TypedColleague")
    assert c["colleague_type"] == "colleague"
    assert c["user_id"] == str(owner.id)


# ---------------------------------------------------------------------------
# Create Colleague
# ---------------------------------------------------------------------------


async def test_create_colleague(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    resp = await oc.post(f"/api/v1/teams/{tid}/colleagues", json={"name": "New Colleague"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "New Colleague"
    assert resp.json()["colleague_type"] == "colleague"


async def test_create_visitor(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    resp = await oc.post(
        f"/api/v1/teams/{tid}/colleagues",
        json={"name": "Visitor", "colleague_type": "visitor"},
    )
    assert resp.status_code == 201
    assert resp.json()["colleague_type"] == "visitor"


async def test_member_cannot_create_colleague(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    mem_client, mem = await create_authenticated_client(
        app, session_factory, f"cmem_{uuid.uuid4().hex[:8]}@example.com"
    )
    await add_team_member(db, team, mem, TeamRole.member)
    resp = await mem_client.post(f"/api/v1/teams/{tid}/colleagues", json={"name": "Fail"})
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Update Colleague
# ---------------------------------------------------------------------------


async def test_update_colleague_name(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    c = await create_colleague(db, team, "OldName")
    resp = await oc.put(f"/api/v1/teams/{tid}/colleagues/{c.id}", json={"name": "NewName"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "NewName"


async def test_promote_visitor_to_colleague(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    v = await create_colleague(db, team, "TempVisitor", colleague_type="visitor")
    resp = await oc.put(
        f"/api/v1/teams/{tid}/colleagues/{v.id}",
        json={"colleague_type": "colleague"},
    )
    assert resp.status_code == 200
    assert resp.json()["colleague_type"] == "colleague"


# ---------------------------------------------------------------------------
# Delete Colleague (soft-delete)
# ---------------------------------------------------------------------------


async def test_delete_colleague_soft_delete(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    c = await create_colleague(db, team, "ToDelete")
    resp = await oc.delete(f"/api/v1/teams/{tid}/colleagues/{c.id}")
    assert resp.status_code == 200

    # Should not appear in list
    list_resp = await oc.get(f"/api/v1/teams/{tid}/colleagues")
    names = [x["name"] for x in list_resp.json()]
    assert "ToDelete" not in names


# ---------------------------------------------------------------------------
# Cross-team isolation
# ---------------------------------------------------------------------------


async def test_cross_team_colleague_not_visible(app, session_factory, db):
    oc1, owner1, team1, tid1 = await _setup(app, session_factory, db)
    await create_colleague(db, team1, "Team1Only")

    oc2, owner2, team2, tid2 = await _setup(app, session_factory, db)
    resp = await oc2.get(f"/api/v1/teams/{tid2}/colleagues")
    names = [c["name"] for c in resp.json()]
    assert "Team1Only" not in names


async def test_cross_team_update_returns_404(app, session_factory, db):
    oc1, owner1, team1, tid1 = await _setup(app, session_factory, db)
    c = await create_colleague(db, team1, "IsolatedColleague")

    oc2, owner2, team2, tid2 = await _setup(app, session_factory, db)
    resp = await oc2.put(f"/api/v1/teams/{tid2}/colleagues/{c.id}", json={"name": "Hacked"})
    assert resp.status_code == 404
