"""Unit tests for pure service functions."""

import uuid
from datetime import datetime, timedelta, timezone

from app.services.auth import (
    create_jwt,
    decode_jwt,
    generate_magic_token,
    hash_token,
)
from app.services.order import consolidate_order_items, format_order_line
from app.services.team import seed_team_menu

from sqlalchemy import select

from app.models.menu import DrinkType, MilkOption, Size


# ---------------------------------------------------------------------------
# Token utilities
# ---------------------------------------------------------------------------


def test_generate_magic_token_returns_pair():
    raw, hashed = generate_magic_token()
    assert isinstance(raw, str)
    assert isinstance(hashed, str)
    assert raw != hashed
    assert len(hashed) == 64  # SHA-256 hex digest


def test_hash_token_matches_generated():
    raw, hashed = generate_magic_token()
    assert hash_token(raw) == hashed


def test_hash_token_deterministic():
    raw, _ = generate_magic_token()
    assert hash_token(raw) == hash_token(raw)


def test_different_tokens_different_hashes():
    raw1, hash1 = generate_magic_token()
    raw2, hash2 = generate_magic_token()
    assert hash1 != hash2
    assert raw1 != raw2


# ---------------------------------------------------------------------------
# JWT utilities
# ---------------------------------------------------------------------------


def test_create_jwt_returns_string():
    user_id = uuid.uuid4()
    token = create_jwt(user_id, "test@example.com")
    assert isinstance(token, str)


def test_decode_jwt_extracts_fields():
    user_id = uuid.uuid4()
    token = create_jwt(user_id, "jwt@example.com")
    payload = decode_jwt(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["email"] == "jwt@example.com"


def test_decode_jwt_expired():
    from jose import jwt as jose_jwt

    from app.config import settings
    from app.services.auth import ALGORITHM

    payload = {
        "sub": str(uuid.uuid4()),
        "email": "expired@example.com",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    token = jose_jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)
    assert decode_jwt(token) is None


def test_decode_jwt_tampered():
    token = create_jwt(uuid.uuid4(), "tamper@example.com")
    # Modify a character in the token
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
    assert decode_jwt(tampered) is None


# ---------------------------------------------------------------------------
# Order consolidation
# ---------------------------------------------------------------------------


def _make_item(drink="Flat White", size="Regular", abbr="Reg", milk=None, sugar=0, notes=None):
    return {
        "drink_type_name": drink,
        "size_name": size,
        "size_abbreviation": abbr,
        "milk_option_name": milk,
        "sugar": sugar,
        "notes": notes,
    }


def test_consolidate_identical_items():
    items = [_make_item(), _make_item(), _make_item()]
    result = consolidate_order_items(items)
    assert len(result) == 1
    assert result[0].count == 3
    assert result[0].drink_type_name == "Flat White"


def test_consolidate_different_items():
    items = [
        _make_item(drink="Flat White"),
        _make_item(drink="Latte"),
        _make_item(drink="Cappuccino"),
    ]
    result = consolidate_order_items(items)
    assert len(result) == 3
    assert all(c.count == 1 for c in result)


def test_consolidate_sorting():
    items = [
        _make_item(drink="Latte"),
        _make_item(drink="Flat White"),
        _make_item(drink="Flat White"),
        _make_item(drink="Flat White"),
    ]
    result = consolidate_order_items(items)
    assert len(result) == 2
    # Higher count first
    assert result[0].count == 3
    assert result[0].drink_type_name == "Flat White"
    assert result[1].count == 1


def test_format_order_line_basic():
    line = format_order_line(2, "Reg", "Flat White", None, 0, None)
    assert line == "2x Reg Flat White"


def test_format_order_line_with_milk():
    line = format_order_line(1, "Lrg", "Latte", "Oat", 0, None)
    assert line == "1x Lrg Oat Latte"


def test_format_order_line_with_sugar():
    line = format_order_line(1, "Sm", "Mocha", None, 2, None)
    assert line == "1x Sm Mocha, 2 sugars"


def test_format_order_line_with_sugar_singular():
    line = format_order_line(1, "Sm", "Mocha", None, 1, None)
    assert line == "1x Sm Mocha, 1 sugar"


def test_format_order_line_with_notes():
    line = format_order_line(1, "Reg", "Cappuccino", "Soy", 0, "extra hot")
    assert line == "1x Reg Soy Cappuccino (extra hot)"


def test_format_order_line_full():
    line = format_order_line(3, "Lrg", "Mocha", "Oat", 2, "no cream")
    assert line == "3x Lrg Oat Mocha, 2 sugars (no cream)"


# ---------------------------------------------------------------------------
# Menu seeding
# ---------------------------------------------------------------------------


async def test_seed_team_menu(db):
    from app.models.team import Team
    from app.models.user import User

    # Create a user and team directly
    user = User(id=uuid.uuid4(), email=f"seed_{uuid.uuid4().hex[:8]}@example.com")
    db.add(user)
    await db.flush()

    team = Team(id=uuid.uuid4(), name="Seed Test", created_by=user.id)
    db.add(team)
    await db.flush()

    await seed_team_menu(db, team.id)
    await db.commit()

    drinks = (
        (await db.execute(select(DrinkType).where(DrinkType.team_id == team.id))).scalars().all()
    )
    sizes = (await db.execute(select(Size).where(Size.team_id == team.id))).scalars().all()
    milks = (
        (await db.execute(select(MilkOption).where(MilkOption.team_id == team.id))).scalars().all()
    )

    assert len(drinks) == 10
    assert len(sizes) == 3
    assert len(milks) == 5

    # All items belong to the team and are active
    for d in drinks:
        assert d.team_id == team.id
        assert d.is_active is True
    for s in sizes:
        assert s.team_id == team.id
        assert s.is_active is True
    for m in milks:
        assert m.team_id == team.id
        assert m.is_active is True
