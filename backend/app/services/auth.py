import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import MagicLinkToken, User, UserRole

ALGORITHM = "HS256"


def generate_magic_token() -> tuple[str, str]:
    """Generate a raw token and its SHA-256 hash."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_jwt(user_id: uuid.UUID, email: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expiry_days)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError:
        return None


async def get_or_create_user(db: AsyncSession, email: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        return user

    role = UserRole.admin if email.lower() == settings.admin_email.lower() else UserRole.viewer
    user = User(email=email.lower(), role=role)
    db.add(user)
    await db.flush()
    return user


async def create_magic_link_token(db: AsyncSession, user: User) -> str:
    raw_token, token_hash_val = generate_magic_token()
    magic_token = MagicLinkToken(
        user_id=user.id,
        token_hash=token_hash_val,
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=settings.magic_link_expiry_minutes),
    )
    db.add(magic_token)
    await db.flush()
    return raw_token


async def verify_magic_token(db: AsyncSession, token: str) -> User | None:
    token_hash_val = hash_token(token)
    result = await db.execute(
        select(MagicLinkToken).where(
            MagicLinkToken.token_hash == token_hash_val,
            MagicLinkToken.used == False,  # noqa: E712
            MagicLinkToken.expires_at > datetime.now(timezone.utc),
        )
    )
    magic_token = result.scalar_one_or_none()
    if not magic_token:
        return None

    magic_token.used = True

    result = await db.execute(select(User).where(User.id == magic_token.user_id))
    return result.scalar_one_or_none()
