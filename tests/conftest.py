"""
PersonaVault Test Configuration
================================
Provides fixtures for integration testing against a Postgres database.
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
import tempfile
import yaml
import os
from pathlib import Path
from contextlib import asynccontextmanager

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.session import Base, get_db
from app.models import User, UserSession, Organization
from app.api.v2.services.environment_service import environment_service
from app.core.dependencies import get_current_user

# Disable lifespan for tests to avoid startup hangs
@asynccontextmanager
async def noop_lifespan(app):
    yield

app.router.lifespan_context = noop_lifespan

# Use a separate test database
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://personavault:personavault@localhost:5432/test_db")

@pytest.fixture(scope="session")
def test_engine():
    """Initializes the database engine."""
    return create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

@pytest.fixture(autouse=True)
async def clean_db(test_engine):
    """Reset the database schema before every test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Reset environment service after test
    environment_service.reset()

@pytest.fixture
async def db_session(test_engine):
    async_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session


# ============================================================
# CREATE TEST ADMIN HELPER
# ============================================================

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

async def create_test_user(db_session, role="user"):
    """Create a test user with an active session."""
    user = User(
        username=f"{role}_{uuid.uuid4().hex[:6]}",
        email=f"{role}_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="pw",
        role=role,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
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

# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
async def client(db_session):
    """Create an async test client with admin authentication."""
    user, token = await create_test_admin(db_session)
    
    async def override_get_db():
        yield db_session
    
    async def override_get_current_user():
        return user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        c.cookies.set("session_id", token)
        yield c
    
    app.dependency_overrides.clear()

@pytest.fixture
def admin_client(client):
    """Alias for client - already has admin auth."""
    return client

@pytest.fixture
async def auth_client(db_session):
    """Create an async test client with regular user authentication."""
    user, token = await create_test_user(db_session, role="user")
    
    async def override_get_db():
        yield db_session
    
    async def override_get_current_user():
        return user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        c.cookies.set("session_id", token)
        yield c
    
    app.dependency_overrides.clear()

# ============================================================
# BEHAVIOR PACK FIXTURES
# ============================================================

@pytest.fixture
def valid_pack_data():
    """Return a valid pack YAML structure"""
    return {
        "pack": {
            "name": "Test Pack",
            "domain": "test",
            "version": "1.0.0",
            "description": "Test pack for unit tests"
        },
        "entities": {
            "test_entity": {
                "pattern": "test value \\$(?P<value>[\\d,]+)",
                "fields": {
                    "value": "number",
                    "status": "string"
                }
            }
        },
        "events": {
            "test_event": {
                "fields": {
                    "timestamp": "date",
                    "description": "string"
                }
            }
        },
        "policies": [{
            "name": "Test Policy",
            "description": "A test policy",
            "when": {
                "signals": ["test_entity"],
                "conditions": ["signals.get('test_entity', {}).get('value', 0) > 100"]
            },
            "decision": {
                "type": "test_decision",
                "severity": "medium",
                "reasoning": "Test condition met for value $signals.get('test_entity', {}).get('value')"
            },
            "actions": [{
                "action": "test_action",
                "priority": "medium"
            }],
            "autonomy": {
                "level": "recommend"
            },
            "confidence_threshold": 0.6
        }]
    }

@pytest.fixture
def valid_pack_file(valid_pack_data):
    """Create a temporary YAML file with valid pack data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(valid_pack_data, f)
        f.close()
        yield f.name
    # Cleanup
    Path(f.name).unlink(missing_ok=True)
