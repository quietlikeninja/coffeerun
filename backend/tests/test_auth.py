"""Tests for auth endpoints: login, verify, me, logout."""

import uuid

from sqlalchemy import select

from app.models.user import MagicLinkToken, User
from app.services.auth import generate_magic_token

from tests.conftest import create_authenticated_client


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


async def test_login_returns_200(client):
    resp = await client.post("/api/v1/auth/login", json={"email": "login_test@example.com"})
    assert resp.status_code == 200
    assert "message" in resp.json()


async def test_login_creates_user(client, db):
    email = f"newuser_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/login", json={"email": email})

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.email == email


async def test_login_reuses_existing_user(client, db):
    email = f"reuse_{uuid.uuid4().hex[:8]}@example.com"

    await client.post("/api/v1/auth/login", json={"email": email})
    result = await db.execute(select(User).where(User.email == email))
    user1 = result.scalar_one()

    await client.post("/api/v1/auth/login", json={"email": email})
    result = await db.execute(select(User).where(User.email == email))
    user2 = result.scalar_one()
    assert user1.id == user2.id


async def test_login_invalid_email_returns_422(client):
    resp = await client.post("/api/v1/auth/login", json={"email": "not-an-email"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------


async def test_verify_valid_token(client, db):
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/login", json={"email": email})

    result = await db.execute(
        select(MagicLinkToken).join(User).where(User.email == email, MagicLinkToken.used == False)  # noqa: E712
    )
    magic = result.scalar_one()

    raw, hashed = generate_magic_token()
    magic.token_hash = hashed
    await db.commit()

    resp = await client.post("/api/v1/auth/verify", json={"token": raw})
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["email"] == email
    assert "teams" in data
    assert "display_name" in data
    assert "created_at" in data
    assert "role" not in data


async def test_verify_sets_cookie(client, db):
    email = f"cookie_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/login", json={"email": email})

    result = await db.execute(
        select(MagicLinkToken).join(User).where(User.email == email, MagicLinkToken.used == False)  # noqa: E712
    )
    magic = result.scalar_one()
    raw, hashed = generate_magic_token()
    magic.token_hash = hashed
    await db.commit()

    resp = await client.post("/api/v1/auth/verify", json={"token": raw})
    assert resp.status_code == 200
    assert "access_token" in resp.cookies


async def test_verify_invalid_token(client):
    resp = await client.post("/api/v1/auth/verify", json={"token": "totally-bogus-token"})
    assert resp.status_code == 400


async def test_verify_used_token(client, db):
    email = f"used_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/login", json={"email": email})

    result = await db.execute(
        select(MagicLinkToken).join(User).where(User.email == email, MagicLinkToken.used == False)  # noqa: E712
    )
    magic = result.scalar_one()
    raw, hashed = generate_magic_token()
    magic.token_hash = hashed
    await db.commit()

    resp1 = await client.post("/api/v1/auth/verify", json={"token": raw})
    assert resp1.status_code == 200

    resp2 = await client.post("/api/v1/auth/verify", json={"token": raw})
    assert resp2.status_code == 400


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------


async def test_me_without_cookie(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_with_valid_cookie(app, session_factory):
    authed_client, user = await create_authenticated_client(
        app, session_factory, f"me_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == user.email
    assert data["teams"] == []


async def test_me_includes_team_after_creation(app, session_factory):
    authed_client, user = await create_authenticated_client(
        app, session_factory, f"meteam_{uuid.uuid4().hex[:8]}@example.com"
    )
    resp = await authed_client.post("/api/v1/teams", json={"name": "Me-Test Team"})
    assert resp.status_code == 200
    team_data = resp.json()

    resp = await authed_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["teams"]) == 1
    assert data["teams"][0]["team_name"] == "Me-Test Team"
    assert data["teams"][0]["role"] == "owner"
    assert data["teams"][0]["team_id"] == team_data["id"]


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


async def test_logout_clears_cookie(client):
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    assert "access_token" in resp.headers.get("set-cookie", "")
