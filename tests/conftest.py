"""
PersonaVault Test Configuration
================================
Provides fixtures for unit and integration testing against an in-memory SQLite DB.

Key design decisions:
- All DB tests use an isolated in-memory SQLite instance (no production data contamination)
- asyncio_mode = "auto" in pytest.ini so async fixtures are properly awaited
- `create_authenticated_session` helper uses the correct model fields: session_token + expires_at
- Both sync TestClient and async AsyncClient variants are available
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import Base, get_db
from app.models import User, UserSession

# ---------------------------------------------------------------------------
# Use an in-memory SQLite database — fast, isolated, no disk state
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ---------------------------------------------------------------------------
# Event loop — session-scoped so all async fixtures share one loop
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Database engine — created once per session
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


# ---------------------------------------------------------------------------
# DB session — rolled back after each test for isolation
# ---------------------------------------------------------------------------
@pytest.fixture
async def db_session(test_engine):
    """Yields an AsyncSession; all changes are rolled back after the test."""
    async_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Sync TestClient — wires override_get_db so routes use the test session
# ---------------------------------------------------------------------------
@pytest.fixture
async def client(db_session):
    """Sync TestClient with DB dependency overridden to the test session."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as tc:
        yield tc
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Async HTTPX client — for tests that need true async HTTP
# ---------------------------------------------------------------------------
@pytest.fixture
async def async_client(db_session):
    """Async HTTPX client with DB dependency overridden to the test session."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper: create a valid authenticated session in the DB
# Returns (user, session_token)
# ---------------------------------------------------------------------------
async def create_authenticated_session(
    db_session: AsyncSession,
    username: str = "test_user",
    email: str = "test@test.com",
    role: str = "user",
) -> tuple:
    """
    Create a User + active UserSession in the test DB.
    Uses correct model fields: session_token (not session_id) and expires_at.
    """
    user = User(
        username=username,
        email=email,
        hashed_password="hashed_placeholder",
        role=role,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    token = str(uuid.uuid4())
    expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24)
    session_record = UserSession(
        user_id=user.id,
        session_token=token,
        is_active=True,
        expires_at=expires,
    )
    db_session.add(session_record)
    await db_session.commit()
    await db_session.refresh(user)

    return user, token


# ---------------------------------------------------------------------------
# Convenience fixtures built on top of create_authenticated_session
# ---------------------------------------------------------------------------
@pytest.fixture
async def auth_user(db_session):
    """Creates a regular authenticated user and returns (user, token)."""
    return await create_authenticated_session(db_session)


@pytest.fixture
async def admin_user(db_session):
    """Creates an admin user and returns (user, token)."""
    return await create_authenticated_session(
        db_session,
        username="admin_test",
        email="admin_test@test.com",
        role="admin",
    )


@pytest.fixture
async def auth_client(client, auth_user):
    """Sync TestClient pre-authenticated as a regular user."""
    _, token = auth_user
    client.cookies.set("session_id", token)
    return client


@pytest.fixture
async def admin_client(client, admin_user):
    """Sync TestClient pre-authenticated as an admin user."""
    _, token = admin_user
    client.cookies.set("session_id", token)
    return client


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
@pytest.fixture
def app_state():
    return app.state


@pytest.fixture
def mock_ollama(monkeypatch):
    """Mocks Ollama responses to prevent slow LLM calls during logic testing."""
    async def _mock_post(*args, **kwargs):
        class _Resp:
            status_code = 200
            def json(self):
                return {"response": '{"faithfulness": 1.0, "relevance": 1.0}'}
        return _Resp()
    monkeypatch.setattr("httpx.AsyncClient.post", _mock_post)
