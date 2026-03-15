import os
import tempfile
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.models.user import Base
from app.models.team import Team, TeamMembership, TeamRole
from app.models.user import User
from app.services.auth import create_jwt

# Import all models so Base.metadata knows every table
import app.models  # noqa: F401


@pytest.fixture(scope="session")
def db_path():
    """Create a temporary SQLite database file for the test session."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_coffeerun_")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture(scope="session")
def db_url(db_path):
    return f"sqlite+aiosqlite:///{db_path}"


@pytest.fixture(scope="session")
async def engine(db_url):
    eng = create_async_engine(db_url)

    # Enable WAL mode and foreign keys for SQLite
    @event.listens_for(eng.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables from model metadata
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield eng
    await eng.dispose()


@pytest.fixture(scope="session")
def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db(session_factory):
    """Per-test database session."""
    async with session_factory() as session:
        yield session
        await session.commit()


@pytest.fixture(scope="session")
async def app(engine, session_factory):
    """FastAPI application with overridden DB dependency."""
    from app.main import app as _app

    async def _override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    _app.dependency_overrides[get_db] = _override_get_db
    yield _app
    _app.dependency_overrides.clear()


@pytest.fixture(scope="session")
async def client(app):
    """Async HTTP client for the test session."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


async def create_test_user(db: AsyncSession, email: str) -> User:
    """Insert a User row directly and return it."""
    from sqlalchemy import select as _select

    result = await db.execute(_select(User).where(User.email == email.lower()))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    user = User(id=uuid.uuid4(), email=email.lower())
    db.add(user)
    await db.flush()
    return user


async def create_authenticated_client(
    app,
    session_factory,
    email: str,
) -> tuple[AsyncClient, User]:
    """Return an (AsyncClient, User) pair with a valid JWT cookie."""
    async with session_factory() as db:
        user = await create_test_user(db, email)
        await db.commit()

    token = create_jwt(user.id, user.email)
    transport = ASGITransport(app=app)
    client = AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies={"access_token": token},
    )
    return client, user


async def create_team_with_owner(
    db: AsyncSession,
    user: User,
    name: str = "Test Team",
) -> Team:
    """Create a Team with the given user as Owner, seed menu items."""
    from app.services.team import seed_team_menu

    team = Team(id=uuid.uuid4(), name=name, created_by=user.id)
    db.add(team)
    await db.flush()

    membership = TeamMembership(
        id=uuid.uuid4(),
        team_id=team.id,
        user_id=user.id,
        role=TeamRole.owner,
    )
    db.add(membership)
    await db.flush()

    await seed_team_menu(db, team.id)
    await db.commit()
    return team


async def add_team_member(
    db: AsyncSession,
    team: Team,
    user: User,
    role: TeamRole,
) -> TeamMembership:
    membership = TeamMembership(
        id=uuid.uuid4(),
        team_id=team.id,
        user_id=user.id,
        role=role,
    )
    db.add(membership)
    await db.flush()
    await db.commit()
    return membership
