"""Tests for team-scoped menu endpoints."""

import uuid

from tests.conftest import (
    add_team_member,
    create_authenticated_client,
    create_team_with_owner,
    create_test_user,
)

from app.models.team import TeamRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup(app, session_factory, db):
    owner_client, owner = await create_authenticated_client(
        app, session_factory, f"menu_{uuid.uuid4().hex[:8]}@example.com"
    )
    async with session_factory() as s:
        owner_u = await create_test_user(s, owner.email)
        team = await create_team_with_owner(s, owner_u, "Menu Team")
    return owner_client, owner, team, str(team.id)


# ---------------------------------------------------------------------------
# Drink Types
# ---------------------------------------------------------------------------


async def test_list_drink_types(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    resp = await oc.get(f"/api/v1/teams/{tid}/menu/drink-types")
    assert resp.status_code == 200
    # Seeded with 10 drink types
    assert len(resp.json()) == 10


async def test_create_drink_type(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    resp = await oc.post(
        f"/api/v1/teams/{tid}/menu/drink-types",
        json={"name": "Affogato", "display_order": 99},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Affogato"


async def test_update_drink_type(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    # Get first drink type
    items = (await oc.get(f"/api/v1/teams/{tid}/menu/drink-types")).json()
    item_id = items[0]["id"]
    resp = await oc.put(
        f"/api/v1/teams/{tid}/menu/drink-types/{item_id}",
        json={"name": "Renamed Drink"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Drink"


async def test_deactivate_drink_type(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    items = (await oc.get(f"/api/v1/teams/{tid}/menu/drink-types")).json()
    item_id = items[0]["id"]
    resp = await oc.delete(f"/api/v1/teams/{tid}/menu/drink-types/{item_id}")
    assert resp.status_code == 200

    # Should have one fewer
    items_after = (await oc.get(f"/api/v1/teams/{tid}/menu/drink-types")).json()
    assert len(items_after) == len(items) - 1


async def test_member_cannot_create_drink_type(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    mem_client, mem = await create_authenticated_client(
        app, session_factory, f"mmenu_{uuid.uuid4().hex[:8]}@example.com"
    )
    await add_team_member(db, team, mem, TeamRole.member)
    resp = await mem_client.post(
        f"/api/v1/teams/{tid}/menu/drink-types",
        json={"name": "Nope"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Sizes
# ---------------------------------------------------------------------------


async def test_list_sizes(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    resp = await oc.get(f"/api/v1/teams/{tid}/menu/sizes")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


async def test_create_size(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    resp = await oc.post(
        f"/api/v1/teams/{tid}/menu/sizes",
        json={"name": "Extra Large", "abbreviation": "XL"},
    )
    assert resp.status_code == 201
    assert resp.json()["abbreviation"] == "XL"


# ---------------------------------------------------------------------------
# Milk Options
# ---------------------------------------------------------------------------


async def test_list_milk_options(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    resp = await oc.get(f"/api/v1/teams/{tid}/menu/milk-options")
    assert resp.status_code == 200
    assert len(resp.json()) == 5


async def test_create_milk_option(app, session_factory, db):
    oc, owner, team, tid = await _setup(app, session_factory, db)
    resp = await oc.post(
        f"/api/v1/teams/{tid}/menu/milk-options",
        json={"name": "Coconut"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Coconut"


# ---------------------------------------------------------------------------
# Cross-team isolation
# ---------------------------------------------------------------------------


async def test_menu_cross_team_isolation(app, session_factory, db):
    oc1, _, team1, tid1 = await _setup(app, session_factory, db)
    oc2, _, team2, tid2 = await _setup(app, session_factory, db)

    # Add a unique drink to team1
    await oc1.post(
        f"/api/v1/teams/{tid1}/menu/drink-types",
        json={"name": "UniqueTeam1Drink"},
    )

    # Shouldn't appear in team2
    items2 = (await oc2.get(f"/api/v1/teams/{tid2}/menu/drink-types")).json()
    names = [i["name"] for i in items2]
    assert "UniqueTeam1Drink" not in names
