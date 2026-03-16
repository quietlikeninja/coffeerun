"""Tests for team-scoped order endpoints and shared orders."""

import uuid

from tests.conftest import (
    create_authenticated_client,
    create_coffee_option,
    create_colleague,
    create_team_with_owner,
    create_test_user,
    get_menu_ids,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_order_env(app, session_factory, db):
    """Create owner + team + colleague + coffee option. Return everything needed for order tests."""
    owner_client, owner = await create_authenticated_client(
        app, session_factory, f"ord_{uuid.uuid4().hex[:8]}@example.com"
    )
    async with session_factory() as s:
        owner_u = await create_test_user(s, owner.email)
        team = await create_team_with_owner(s, owner_u, "Order Team")
    menu = await get_menu_ids(db, team.id)
    colleague = await create_colleague(db, team, "OrderPerson")
    option = await create_coffee_option(
        db,
        colleague.id,
        menu["drink_type_id"],
        menu["size_id"],
        milk_option_id=menu["milk_option_id"],
    )
    return owner_client, owner, team, str(team.id), colleague, option


# ---------------------------------------------------------------------------
# Create Order
# ---------------------------------------------------------------------------


async def test_create_order(app, session_factory, db):
    oc, owner, team, tid, colleague, option = await _setup_order_env(app, session_factory, db)
    resp = await oc.post(
        f"/api/v1/teams/{tid}/orders",
        json={"items": [{"colleague_id": str(colleague.id), "coffee_option_id": str(option.id)}]},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["colleague_name"] == "OrderPerson"
    assert data["share_token"]
    assert len(data["consolidated"]) == 1


async def test_create_order_denormalizes_drink(app, session_factory, db):
    oc, owner, team, tid, colleague, option = await _setup_order_env(app, session_factory, db)
    resp = await oc.post(
        f"/api/v1/teams/{tid}/orders",
        json={"items": [{"colleague_id": str(colleague.id), "coffee_option_id": str(option.id)}]},
    )
    assert resp.status_code == 201
    item = resp.json()["items"][0]
    assert item["drink_type_name"]
    assert item["size_name"]
    assert item["size_abbreviation"]


# ---------------------------------------------------------------------------
# List Orders
# ---------------------------------------------------------------------------


async def test_list_orders(app, session_factory, db):
    oc, owner, team, tid, colleague, option = await _setup_order_env(app, session_factory, db)
    # Create two orders
    await oc.post(
        f"/api/v1/teams/{tid}/orders",
        json={"items": [{"colleague_id": str(colleague.id), "coffee_option_id": str(option.id)}]},
    )
    await oc.post(
        f"/api/v1/teams/{tid}/orders",
        json={"items": [{"colleague_id": str(colleague.id), "coffee_option_id": str(option.id)}]},
    )
    resp = await oc.get(f"/api/v1/teams/{tid}/orders")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


# ---------------------------------------------------------------------------
# Get Order
# ---------------------------------------------------------------------------


async def test_get_order(app, session_factory, db):
    oc, owner, team, tid, colleague, option = await _setup_order_env(app, session_factory, db)
    create_resp = await oc.post(
        f"/api/v1/teams/{tid}/orders",
        json={"items": [{"colleague_id": str(colleague.id), "coffee_option_id": str(option.id)}]},
    )
    order_id = create_resp.json()["id"]
    resp = await oc.get(f"/api/v1/teams/{tid}/orders/{order_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == order_id


# ---------------------------------------------------------------------------
# Update Order
# ---------------------------------------------------------------------------


async def test_update_order_replaces_items(app, session_factory, db):
    oc, owner, team, tid, colleague, option = await _setup_order_env(app, session_factory, db)
    create_resp = await oc.post(
        f"/api/v1/teams/{tid}/orders",
        json={"items": [{"colleague_id": str(colleague.id), "coffee_option_id": str(option.id)}]},
    )
    order_id = create_resp.json()["id"]

    # Create another colleague + option
    menu = await get_menu_ids(db, team.id)
    c2 = await create_colleague(db, team, "UpdatePerson")
    opt2 = await create_coffee_option(db, c2.id, menu["drink_type_id"], menu["size_id"])

    resp = await oc.put(
        f"/api/v1/teams/{tid}/orders/{order_id}",
        json={"items": [{"colleague_id": str(c2.id), "coffee_option_id": str(opt2.id)}]},
    )
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1
    assert resp.json()["items"][0]["colleague_name"] == "UpdatePerson"


# ---------------------------------------------------------------------------
# Shared Order (no auth)
# ---------------------------------------------------------------------------


async def test_shared_order_no_auth(app, session_factory, db):
    oc, owner, team, tid, colleague, option = await _setup_order_env(app, session_factory, db)
    create_resp = await oc.post(
        f"/api/v1/teams/{tid}/orders",
        json={"items": [{"colleague_id": str(colleague.id), "coffee_option_id": str(option.id)}]},
    )
    share_token = create_resp.json()["share_token"]

    # Use unauthenticated client
    from httpx import ASGITransport, AsyncClient
    from app.main import app as fastapi_app

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as anon:
        resp = await anon.get(f"/api/v1/orders/share/{share_token}")
    assert resp.status_code == 200
    assert resp.json()["share_token"] == share_token


async def test_shared_order_invalid_token(client):
    resp = await client.get("/api/v1/orders/share/nonexistent-token")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Cross-team isolation
# ---------------------------------------------------------------------------


async def test_cross_team_order_not_visible(app, session_factory, db):
    oc1, _, team1, tid1, c1, opt1 = await _setup_order_env(app, session_factory, db)
    create_resp = await oc1.post(
        f"/api/v1/teams/{tid1}/orders",
        json={"items": [{"colleague_id": str(c1.id), "coffee_option_id": str(opt1.id)}]},
    )
    order_id = create_resp.json()["id"]

    # Second team
    oc2, owner2 = await create_authenticated_client(
        app, session_factory, f"ord2_{uuid.uuid4().hex[:8]}@example.com"
    )
    async with session_factory() as s:
        owner2_u = await create_test_user(s, owner2.email)
        team2 = await create_team_with_owner(s, owner2_u, "Other Order Team")

    resp = await oc2.get(f"/api/v1/teams/{team2.id}/orders/{order_id}")
    assert resp.status_code == 404
