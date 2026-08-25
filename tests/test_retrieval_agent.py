"""
Tests for RetrievalAgent - updated for Auditable Traces.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.swarm.core.retriever import RetrievalAgent
from app.schemas.memory_schemas import RetrievalPlan, MemoryResult

@pytest.fixture
def mock_vector_repo():
    mock = AsyncMock()
    mock.search.return_value = [{"content": "Memory 1", "score": 0.9}]
    return mock

@pytest.fixture
def mock_graph_repo():
    mock = AsyncMock()
    mock.search.return_value = []
    return mock

@pytest.fixture
def agent(mock_vector_repo, mock_graph_repo):
    return RetrievalAgent(
        vector_repo=mock_vector_repo,
        graph_repo=mock_graph_repo
    )

def test_init(mock_vector_repo, mock_graph_repo):
    """Test RetrievalAgent initialization."""
    agent = RetrievalAgent(
        vector_repo=mock_vector_repo,
        graph_repo=mock_graph_repo
    )
    assert agent is not None
    assert agent.vector_repo == mock_vector_repo
    assert agent.graph_repo == mock_graph_repo

@pytest.mark.asyncio
async def test_hybrid_search(agent):
    """Test hybrid_search with RetrievalPlan."""
    plan = RetrievalPlan(
        needs_retrieval=True,
        semantic_queries=["test query"],
        keyword_queries=["test"],
        graph_traversals=[],
        reasoning="Test query reasoning",
        complexity_score=0.5
    )
    result = await agent.hybrid_search(plan=plan, user_id=1)
    assert isinstance(result, list)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_search_returns_trace(agent):
    """Test search method returns results and trace."""
    result_data = await agent.search(query="test", user_id=1)
    assert "results" in result_data
    assert "trace" in result_data
    assert result_data["trace"]["agent"] == "retriever"
    assert result_data["trace"]["trace"]["decision"]["type"] == "retrieve_memories"
