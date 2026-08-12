"""
PersonaVault Test Configuration
================================
Provides fixtures for unit and integration testing against an in-memory SQLite DB.
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.db.session import Base, get_db
from app.models import User, UserSession, Organization
from app.core.dependencies import get_current_user

# Use an in-memory SQLite database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    async_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session
        await session.rollback()

@pytest.fixture
def client(db_session):
    """Create a test client with a fully authenticated admin user."""
    loop = asyncio.get_event_loop()
    user, token = loop.run_until_complete(create_test_admin(db_session))
    
    # Override the get_db dependency
    async def override_get_db():
        yield db_session
        
    # Override get_current_user
    async def override_get_current_user():
        return user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    # Create client
    with TestClient(app) as tc:
        # Set the session cookie so RBAC works
        tc.cookies.set("session_id", token)
        yield tc
    
    app.dependency_overrides.clear()

async def create_test_admin(db_session):
    """Create a test admin user with an active session."""
    user = User(
        username=f"admin_{uuid.uuid4().hex[:6]}",
        email=f"admin_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="pw",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create an active session
    token = str(uuid.uuid4())
    session = UserSession(
        user_id=user.id,
        session_token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        is_active=True
    )
    db_session.add(session)
    await db_session.commit()
    
    return user, token

@pytest.fixture
def admin_client(client):
    return client
