import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from app.models import Memory
from app.services.memory_service import MemoryService
from app.repositories.interfaces import IMemoryRepository, IVectorRepository, IGraphRepository

@pytest.fixture
def mock_repos():
    return {
        "memory": AsyncMock(spec=IMemoryRepository),
        "vector": AsyncMock(spec=IVectorRepository),
        "graph": AsyncMock(spec=IGraphRepository)
    }

@pytest.mark.asyncio
async def test_delete_expired_memories(mock_repos):
    """Test that expired memories are deleted via repository."""
    memory_service = MemoryService(
        memory_repo=mock_repos["memory"],
        vector_repo=mock_repos["vector"],
        graph_repo=mock_repos["graph"]
    )
    
    await memory_service.delete_expired_memories()
    mock_repos["memory"].delete_expired.assert_called_once()

@pytest.mark.asyncio
async def test_delete_expired_memories_with_no_expired(mock_repos):
    """Test delete_expired_memories."""
    memory_service = MemoryService(
        memory_repo=mock_repos["memory"],
        vector_repo=mock_repos["vector"],
        graph_repo=mock_repos["graph"]
    )
    
    mock_repos["memory"].delete_expired.return_value = 0
    result = await memory_service.delete_expired_memories()
    
    assert result == 0
    mock_repos["memory"].delete_expired.assert_called_once()

def test_memory_service_init():
    """Test MemoryService initialization."""
    repo = MagicMock(spec=IMemoryRepository)
    service = MemoryService(memory_repo=repo)
    assert service is not None
    assert service.memory_repo == repo

