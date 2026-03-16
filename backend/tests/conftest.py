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


async def create_colleague(
    db: AsyncSession,
    team: Team,
    name: str,
    colleague_type: str = "colleague",
    user_id: uuid.UUID | None = None,
):
    from app.models.colleague import Colleague

    colleague = Colleague(
        id=uuid.uuid4(),
        team_id=team.id,
        name=name,
        colleague_type=colleague_type,
        user_id=user_id,
    )
    db.add(colleague)
    await db.flush()
    await db.commit()
    return colleague


async def create_coffee_option(
    db: AsyncSession,
    colleague_id: uuid.UUID,
    drink_type_id: uuid.UUID,
    size_id: uuid.UUID,
    milk_option_id: uuid.UUID | None = None,
    sugar: int = 0,
    notes: str | None = None,
    is_default: bool = False,
):
    from app.models.coffee_option import CoffeeOption

    option = CoffeeOption(
        id=uuid.uuid4(),
        colleague_id=colleague_id,
        drink_type_id=drink_type_id,
        size_id=size_id,
        milk_option_id=milk_option_id,
        sugar=sugar,
        notes=notes,
        is_default=is_default,
    )
    db.add(option)
    await db.flush()
    await db.commit()
    return option


async def get_menu_ids(db: AsyncSession, team_id: uuid.UUID) -> dict:
    """Return the first drink_type_id, size_id, milk_option_id for a team."""
    from sqlalchemy import select as _select

    from app.models.menu import DrinkType, MilkOption, Size

    dt = (
        await db.execute(_select(DrinkType).where(DrinkType.team_id == team_id).limit(1))
    ).scalar_one()
    sz = (await db.execute(_select(Size).where(Size.team_id == team_id).limit(1))).scalar_one()
    mk = (
        await db.execute(_select(MilkOption).where(MilkOption.team_id == team_id).limit(1))
    ).scalar_one()
    return {
        "drink_type_id": dt.id,
        "size_id": sz.id,
        "milk_option_id": mk.id,
    }
