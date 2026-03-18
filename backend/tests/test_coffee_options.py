"""Tests for team-scoped coffee option endpoints and self-service editing."""

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


async def _setup(app, session_factory, db):
    """Create owner + team + colleague + menu ids."""
    owner_client, owner = await create_authenticated_client(
        app, session_factory, f"opt_{uuid.uuid4().hex[:8]}@example.com"
    )
    async with session_factory() as s:
        owner_u = await create_test_user(s, owner.email)
        team = await create_team_with_owner(s, owner_u, "Option Team")
    menu = await get_menu_ids(db, team.id)
    colleague = await create_colleague(db, team, "OptionPerson")
    return owner_client, owner, team, str(team.id), colleague, menu


# ---------------------------------------------------------------------------
# Add coffee option (via colleagues sub-route)
# ---------------------------------------------------------------------------


async def test_add_coffee_option(app, session_factory, db):
    oc, owner, team, tid, colleague, menu = await _setup(app, session_factory, db)
    resp = await oc.post(
        f"/api/v1/teams/{tid}/colleagues/{colleague.id}/coffee-options",
        json={
            "drink_type_id": str(menu["drink_type_id"]),
            "size_id": str(menu["size_id"]),
            "milk_option_id": str(menu["milk_option_id"]),
            "sugar": 1,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["colleague_id"] == str(colleague.id)
    assert data["sugar"] == 1


async def test_first_option_is_auto_default(app, session_factory, db):
    oc, owner, team, tid, colleague, menu = await _setup(app, session_factory, db)
    resp = await oc.post(
        f"/api/v1/teams/{tid}/colleagues/{colleague.id}/coffee-options",
        json={
            "drink_type_id": str(menu["drink_type_id"]),
            "size_id": str(menu["size_id"]),
        },
    )
    assert resp.status_code == 201
    assert resp.json()["is_default"] is True


# ---------------------------------------------------------------------------
# Update coffee option
# ---------------------------------------------------------------------------


async def test_update_coffee_option(app, session_factory, db):
    oc, owner, team, tid, colleague, menu = await _setup(app, session_factory, db)
    opt = await create_coffee_option(db, colleague.id, menu["drink_type_id"], menu["size_id"])
    resp = await oc.put(
        f"/api/v1/teams/{tid}/coffee-options/{opt.id}",
        json={"sugar": 3},
    )
    assert resp.status_code == 200
    assert resp.json()["sugar"] == 3


# ---------------------------------------------------------------------------
# Delete coffee option
# ---------------------------------------------------------------------------


async def test_delete_coffee_option(app, session_factory, db):
    oc, owner, team, tid, colleague, menu = await _setup(app, session_factory, db)
    opt = await create_coffee_option(db, colleague.id, menu["drink_type_id"], menu["size_id"])
    resp = await oc.delete(f"/api/v1/teams/{tid}/coffee-options/{opt.id}")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Set default
# ---------------------------------------------------------------------------


async def test_set_default_unsets_others(app, session_factory, db):
    oc, owner, team, tid, colleague, menu = await _setup(app, session_factory, db)
    await create_coffee_option(
        db, colleague.id, menu["drink_type_id"], menu["size_id"], is_default=True
    )
    opt2 = await create_coffee_option(db, colleague.id, menu["drink_type_id"], menu["size_id"])
    resp = await oc.put(f"/api/v1/teams/{tid}/coffee-options/{opt2.id}/set-default")
    assert resp.status_code == 200
    assert resp.json()["is_default"] is True


# ---------------------------------------------------------------------------
# Self-service editing
# ---------------------------------------------------------------------------


async def test_member_can_edit_own_linked_option(app, session_factory, db):
    oc, owner, team, tid, _, menu = await _setup(app, session_factory, db)

    mem_client, mem = await create_authenticated_client(
        app, session_factory, f"selfserv_{uuid.uuid4().hex[:8]}@example.com"
    )
    await add_team_member(db, team, mem, TeamRole.member)

    # Create colleague linked to this member
    linked = await create_colleague(db, team, "LinkedMember", user_id=mem.id)
    opt = await create_coffee_option(db, linked.id, menu["drink_type_id"], menu["size_id"])

    resp = await mem_client.put(
        f"/api/v1/teams/{tid}/coffee-options/{opt.id}",
        json={"sugar": 2},
    )
    assert resp.status_code == 200
    assert resp.json()["sugar"] == 2


async def test_member_cannot_edit_other_colleague_option(app, session_factory, db):
    oc, owner, team, tid, colleague, menu = await _setup(app, session_factory, db)

    mem_client, mem = await create_authenticated_client(
        app, session_factory, f"noaccess_{uuid.uuid4().hex[:8]}@example.com"
    )
    await add_team_member(db, team, mem, TeamRole.member)

    opt = await create_coffee_option(db, colleague.id, menu["drink_type_id"], menu["size_id"])

    resp = await mem_client.put(
        f"/api/v1/teams/{tid}/coffee-options/{opt.id}",
        json={"sugar": 5},
    )
    assert resp.status_code == 403


async def test_owner_can_edit_any_option(app, session_factory, db):
    oc, owner, team, tid, colleague, menu = await _setup(app, session_factory, db)
    opt = await create_coffee_option(db, colleague.id, menu["drink_type_id"], menu["size_id"])
    resp = await oc.put(
        f"/api/v1/teams/{tid}/coffee-options/{opt.id}",
        json={"notes": "extra hot"},
    )
    assert resp.status_code == 200
    assert resp.json()["notes"] == "extra hot"


async def test_member_can_add_option_to_own_linked_colleague(app, session_factory, db):
    oc, owner, team, tid, _, menu = await _setup(app, session_factory, db)

    mem_client, mem = await create_authenticated_client(
        app, session_factory, f"addself_{uuid.uuid4().hex[:8]}@example.com"
    )
    await add_team_member(db, team, mem, TeamRole.member)
    linked = await create_colleague(db, team, "SelfAdd", user_id=mem.id)

    resp = await mem_client.post(
        f"/api/v1/teams/{tid}/colleagues/{linked.id}/coffee-options",
        json={
            "drink_type_id": str(menu["drink_type_id"]),
            "size_id": str(menu["size_id"]),
        },
    )
    assert resp.status_code == 201


async def test_member_cannot_add_option_to_other_colleague(app, session_factory, db):
    oc, owner, team, tid, colleague, menu = await _setup(app, session_factory, db)

    mem_client, mem = await create_authenticated_client(
        app, session_factory, f"noadd_{uuid.uuid4().hex[:8]}@example.com"
    )
    await add_team_member(db, team, mem, TeamRole.member)

    resp = await mem_client.post(
        f"/api/v1/teams/{tid}/colleagues/{colleague.id}/coffee-options",
        json={
            "drink_type_id": str(menu["drink_type_id"]),
            "size_id": str(menu["size_id"]),
        },
    )
    assert resp.status_code == 403
