"""Tests for team-scoped stats endpoints."""

import uuid

from tests.conftest import (
    add_team_member,
    create_authenticated_client,
    create_coffee_option,
    create_colleague,
    create_team_with_owner,
    create_test_user,
    get_menu_ids,
)

from app.models.team import TeamRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_stats(app, session_factory, db):
    """Create owner + team + colleague + option + one order."""
    owner_client, owner = await create_authenticated_client(
        app, session_factory, f"stat_{uuid.uuid4().hex[:8]}@example.com"
    )
    async with session_factory() as s:
        owner_u = await create_test_user(s, owner.email)
        team = await create_team_with_owner(s, owner_u, "Stats Team")
    menu = await get_menu_ids(db, team.id)
    colleague = await create_colleague(db, team, f"StatPerson_{uuid.uuid4().hex[:6]}")
    option = await create_coffee_option(
        db,
        colleague.id,
        menu["drink_type_id"],
        menu["size_id"],
        milk_option_id=menu["milk_option_id"],
    )
    tid = str(team.id)

    # Create an order so stats have data
    await owner_client.post(
        f"/api/v1/teams/{tid}/orders",
        json={"items": [{"colleague_id": str(colleague.id), "coffee_option_id": str(option.id)}]},
    )

    return owner_client, owner, team, tid


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------


async def test_stats_overview(app, session_factory, db):
    oc, owner, team, tid = await _setup_stats(app, session_factory, db)
    resp = await oc.get(f"/api/v1/teams/{tid}/stats/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_orders"] >= 1
    assert data["total_coffees"] >= 1
    assert "orders_this_week" in data
    assert "orders_this_month" in data


# ---------------------------------------------------------------------------
# Drinks
# ---------------------------------------------------------------------------


async def test_stats_drinks(app, session_factory, db):
    oc, owner, team, tid = await _setup_stats(app, session_factory, db)
    resp = await oc.get(f"/api/v1/teams/{tid}/stats/drinks")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    assert "drink_name" in resp.json()[0]
    assert "count" in resp.json()[0]


# ---------------------------------------------------------------------------
# Colleagues
# ---------------------------------------------------------------------------


async def test_stats_colleagues(app, session_factory, db):
    oc, owner, team, tid = await _setup_stats(app, session_factory, db)
    resp = await oc.get(f"/api/v1/teams/{tid}/stats/colleagues")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    entry = resp.json()[0]
    assert entry["colleague_name"].startswith("StatPerson_")
    assert entry["order_count"] >= 1


# ---------------------------------------------------------------------------
# Access Control
# ---------------------------------------------------------------------------


async def test_member_cannot_access_stats(app, session_factory, db):
    oc, owner, team, tid = await _setup_stats(app, session_factory, db)
    mem_client, mem = await create_authenticated_client(
        app, session_factory, f"statmem_{uuid.uuid4().hex[:8]}@example.com"
    )
    await add_team_member(db, team, mem, TeamRole.member)

    for endpoint in ["overview", "drinks", "colleagues"]:
        resp = await mem_client.get(f"/api/v1/teams/{tid}/stats/{endpoint}")
        assert resp.status_code == 403, f"Expected 403 for {endpoint}"


async def test_manager_can_access_stats(app, session_factory, db):
    oc, owner, team, tid = await _setup_stats(app, session_factory, db)
    mgr_client, mgr = await create_authenticated_client(
        app, session_factory, f"statmgr_{uuid.uuid4().hex[:8]}@example.com"
    )
    await add_team_member(db, team, mgr, TeamRole.manager)

    resp = await mgr_client.get(f"/api/v1/teams/{tid}/stats/overview")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Cross-team isolation
# ---------------------------------------------------------------------------


async def test_stats_cross_team_isolation(app, session_factory, db):
    oc1, _, team1, tid1 = await _setup_stats(app, session_factory, db)
    oc2, _, team2, tid2 = await _setup_stats(app, session_factory, db)

    # Each team should only see its own stats
    resp1 = await oc1.get(f"/api/v1/teams/{tid1}/stats/colleagues")
    resp2 = await oc2.get(f"/api/v1/teams/{tid2}/stats/colleagues")

    names1 = {e["colleague_name"] for e in resp1.json()}
    names2 = {e["colleague_name"] for e in resp2.json()}
    # They should not overlap (each has unique colleague names)
    assert not names1.intersection(names2)


async def test_unauthenticated_stats_returns_401(client):
    fake_tid = uuid.uuid4()
    resp = await client.get(f"/api/v1/teams/{fake_tid}/stats/overview")
    assert resp.status_code == 401
