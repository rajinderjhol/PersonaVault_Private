import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import Base, get_db
from app.config import Config

# Use an in-memory SQLite database for high-speed "Leapfrog" testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    """Provides an authenticated TestClient with a mocked database session."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def mock_ollama(monkeypatch):
    """Mocks Ollama responses to prevent slow LLM calls during logic testing."""
    async def mock_post(*args, **kwargs):
        return type("Response", (), {"status_code": 200, "json": lambda: {"response": '{"faithfulness": 1.0, "relevance": 1.0}'}})
    # Monkeypatch the shared ai_client if needed