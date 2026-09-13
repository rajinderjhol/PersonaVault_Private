"""
PersonaVault Test Configuration
================================
Provides fixtures for unit and integration testing against an in-memory SQLite DB.
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
import tempfile
import yaml
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.db.session import Base, get_db
from app.models import User, UserSession, Organization
from app.models.decision_trace import DecisionTrace, ProvenanceRecord
from app.api.v2.services.environment_service import environment_service
from app.core.dependencies import get_current_user

# Use an in-memory SQLite database
TEST_DATABASE_URL = "sqlite+aiosqlite:////tmp/test.db"

@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Initializes the database using Alembic migrations."""
    from alembic.config import Config
    from alembic import command
    from sqlalchemy import create_engine
    
    # Create a synchronous engine with StaticPool to keep DB alive in-memory
    from sqlalchemy.pool import StaticPool
    sync_engine = create_engine(TEST_DATABASE_URL.replace('sqlite+aiosqlite:///', 'sqlite:///'), poolclass=StaticPool)
    
    # Configure Alembic
    alembic_cfg = Config("migrations/alembic.ini")
    
    # Pass the connection to Alembic
    with sync_engine.connect() as connection:
        alembic_cfg.attributes['connection'] = connection
        command.upgrade(alembic_cfg, "head")
        
    # Yield the async engine for the tests
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
    yield engine
    await engine.dispose()
    sync_engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    async_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session
        # Cleanup: Truncate/Clear all tables after test
        await session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            try:
                await session.execute(table.delete())
            except Exception:
                # Table might not exist, ignore
                pass
        await session.commit()
        # Reset environment service
        environment_service.reset()

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
def client(db_session):
    """Create a test client with admin authentication."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    user, token = loop.run_until_complete(create_test_admin(db_session))
    loop.close()
    
    async def override_get_db():
        yield db_session
    
    async def override_get_current_user():
        return user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as tc:
        tc.cookies.set("session_id", token)
        yield tc
    
    app.dependency_overrides.clear()

@pytest.fixture
def admin_client(client):
    """Alias for client - already has admin auth."""
    return client

@pytest.fixture
def auth_client(db_session):
    """Create a test client with regular user authentication."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    user, token = loop.run_until_complete(create_test_user(db_session, role="user"))
    loop.close()
    
    async def override_get_db():
        yield db_session
    
    async def override_get_current_user():
        return user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as tc:
        tc.cookies.set("session_id", token)
        yield tc
    
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
