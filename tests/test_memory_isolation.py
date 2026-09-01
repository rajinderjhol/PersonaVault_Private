import pytest
from unittest.mock import AsyncMock
from app.services.memory_service import MemoryService
from app.repositories.interfaces import IMemoryRepository, IVectorRepository, IGraphRepository

@pytest.fixture
def memory_service(mock_repos):
    return MemoryService(
        memory_repo=mock_repos["memory"],
        vector_repo=mock_repos["vector"],
        graph_repo=mock_repos["graph"]
    )

@pytest.fixture
def mock_repos():
    return {
        "memory": AsyncMock(spec=IMemoryRepository),
        "vector": AsyncMock(spec=IVectorRepository),
        "graph": AsyncMock(spec=IGraphRepository)
    }

@pytest.mark.asyncio
async def test_save_memory_with_environment_id(memory_service, mock_repos):
    """Test saving a memory with an environment_id propagates correctly."""
    user_id = 1
    content = "Hello Environment"
    environment_id = "env-123"
    
    # Setup mock return value
    mock_memory = AsyncMock()
    mock_memory.id = 1
    mock_repos["memory"].add.return_value = mock_memory
    
    await memory_service.save_memory(
        user_id=user_id,
        memory_type="text",
        content=content,
        tags="test",
        environment_id=environment_id
    )
    
    mock_repos["memory"].add.assert_called_once_with(
        user_id, content, content, "text", "test", environment_id=environment_id
    )
    mock_repos["vector"].add.assert_called_once_with(
        1, content, user_id, environment_id=environment_id
    )

@pytest.mark.asyncio
async def test_search_memories_with_environment_id(memory_service, mock_repos):
    """Test searching memories filters by environment_id."""
    user_id = 1
    query = "test"
    environment_id = "env-123"
    
    # Mock return values for search
    mock_repos["vector"].search.return_value = []
    mock_repos["memory"].search.return_value = []
    
    await memory_service.search_memories(
        user_id=user_id,
        query=query,
        environment_id=environment_id
    )
    
    mock_repos["vector"].search.assert_called_once_with(
        query, user_id, limit=5, environment_id=environment_id
    )
    mock_repos["memory"].search.assert_called_once_with(
        user_id, query, limit=5, environment_id=environment_id
    )
