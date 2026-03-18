import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu import DrinkType, MilkOption, Size
from app.models.team import TeamInvite
from app.services.auth import generate_magic_token, hash_token

SEED_DRINK_TYPES = [
    ("Flat White", 1),
    ("Long Black", 2),
    ("Cappuccino", 3),
    ("Latte", 4),
    ("Mocha", 5),
    ("Espresso", 6),
    ("Macchiato", 7),
    ("Hot Chocolate", 8),
    ("Chai Latte", 9),
    ("Piccolo", 10),
]

SEED_SIZES = [
    ("Small", "Sm", 1),
    ("Regular", "Reg", 2),
    ("Large", "Lrg", 3),
]

SEED_MILK_OPTIONS = [
    ("Full Cream", 1),
    ("Skim", 2),
    ("Soy", 3),
    ("Oat", 4),
    ("Almond", 5),
]


async def seed_team_menu(db: AsyncSession, team_id: uuid.UUID) -> None:
    """Seed default drink types, sizes, and milk options for a new team."""
    for name, order in SEED_DRINK_TYPES:
        db.add(DrinkType(team_id=team_id, name=name, display_order=order, is_active=True))

    for name, abbr, order in SEED_SIZES:
        db.add(
            Size(
                team_id=team_id,
                name=name,
                abbreviation=abbr,
                display_order=order,
                is_active=True,
            )
        )

    for name, order in SEED_MILK_OPTIONS:
        db.add(MilkOption(team_id=team_id, name=name, display_order=order, is_active=True))

    await db.flush()


def generate_invite_token() -> tuple[str, str]:
    """Generate a raw invite token and its SHA-256 hash."""
    return generate_magic_token()


async def verify_invite_token(db: AsyncSession, token: str) -> TeamInvite | None:
    """Look up a valid (unaccepted, unexpired) invite by raw token."""
    token_hash_val = hash_token(token)
    result = await db.execute(
        select(TeamInvite).where(
            TeamInvite.token_hash == token_hash_val,
            TeamInvite.accepted == False,  # noqa: E712
            TeamInvite.expires_at > datetime.now(timezone.utc),
        )
    )
    return result.scalar_one_or_none()
