"""
Tests for RetrievalAgent - fixed to match actual schema.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.swarm.core.retriever import RetrievalAgent
from app.schemas.memory_schemas import RetrievalPlan, MemoryResult

@pytest.fixture
def mock_vector_repo():
    mock = AsyncMock()
    return mock

@pytest.fixture
def mock_graph_repo():
    mock = AsyncMock()
    return mock

@pytest.fixture
def agent(mock_vector_repo, mock_graph_repo):
    return RetrievalAgent(
        vector_repo=mock_vector_repo,
        graph_repo=mock_graph_repo
    )

# ============================================================
# TESTS - Using correct RetrievalPlan schema
# ============================================================

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
    # Use the correct schema fields
    plan = RetrievalPlan(
        needs_retrieval=True,
        semantic_queries=["test query"],
        keyword_queries=["test"],
        graph_traversals=[],
        reasoning="Test query reasoning",
        complexity_score=0.5
    )
    result = await agent.hybrid_search(plan=plan, user_id=1)
    assert result is not None

@pytest.mark.asyncio
async def test_semantic_search(agent):
    """Test semantic search."""
    result = await agent._semantic_search(queries=["test"], user_id=1)
    assert result is not None
