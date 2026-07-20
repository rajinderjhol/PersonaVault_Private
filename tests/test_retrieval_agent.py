"""
Tests for RetrievalAgent - fixed async mock issues.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.retrieval_agent import RetrievalAgent
from app.schemas.memory_schemas import RetrievalPlan, MemoryResult

@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing with async methods."""
    mock = AsyncMock()
    # Make search_similar an async method
    mock.search_similar = AsyncMock(return_value=[
        {"id": 1, "content": "Test result 1", "score": 0.95},
        {"id": 2, "content": "Test result 2", "score": 0.85}
    ])
    return mock

@pytest.fixture
def mock_graph_service():
    """Mock graph service for testing."""
    return AsyncMock()

@pytest.fixture
def mock_keyword_search():
    """Mock keyword search for testing."""
    mock = MagicMock()
    mock.search.return_value = [
        {"id": 5, "content": "Keyword result 1"},
        {"id": 6, "content": "Keyword result 2"}
    ]
    return mock

@pytest.fixture
def retrieval_plan():
    """Sample retrieval plan for testing."""
    return RetrievalPlan(
        needs_retrieval=True,
        semantic_queries=["test query 1", "test query 2"],
        keyword_queries=["keyword query"],
        graph_traversals=["MATCH (n) RETURN n"],
        reasoning="Test reasoning",
        complexity_score=0.5
    )

class TestRetrievalAgent:
    """Test suite for RetrievalAgent."""
    
    def test_init(self):
        """Test RetrievalAgent initialization."""
        agent = RetrievalAgent()
        assert agent is not None
        assert hasattr(agent, 'vector_store')
        assert hasattr(agent, 'graph_service')
        assert hasattr(agent, 'keyword_search')
    
    def test_init_with_custom_services(self, mock_vector_store, mock_graph_service):
        """Test RetrievalAgent initialization with custom services."""
        agent = RetrievalAgent(
            vector_store=mock_vector_store,
            graph_service=mock_graph_service
        )
        assert agent.vector_store == mock_vector_store
        assert agent.graph_service == mock_graph_service
    
    @pytest.mark.asyncio
    async def test_hybrid_search_with_all_queries(self, retrieval_plan):
        """Test hybrid search with semantic, keyword, and graph queries."""
        agent = RetrievalAgent()
        
        # Mock the individual search methods
        with patch.object(agent, '_semantic_search', new_callable=AsyncMock) as mock_semantic:
            mock_semantic.return_value = [
                MemoryResult(content="Semantic result", source="faiss", score=0.9)
            ]
            with patch.object(agent, '_keyword_search', new_callable=AsyncMock) as mock_keyword:
                mock_keyword.return_value = [
                    MemoryResult(content="Keyword result", source="keyword", score=0.8)
                ]
                with patch.object(agent, '_graph_search', new_callable=AsyncMock) as mock_graph:
                    mock_graph.return_value = [
                        MemoryResult(content="Graph result", source="graph", score=0.85)
                    ]
                    
                    results = await agent.hybrid_search(retrieval_plan, user_id=1)
                    
                    assert len(results) == 3
                    assert any(r.source == "faiss" for r in results)
                    assert any(r.source == "keyword" for r in results)
                    assert any(r.source == "graph" for r in results)
    
    @pytest.mark.asyncio
    async def test_hybrid_search_with_only_semantic(self, retrieval_plan):
        """Test hybrid search with only semantic queries."""
        agent = RetrievalAgent()
        plan = RetrievalPlan(
            needs_retrieval=True,
            semantic_queries=["test query"],
            keyword_queries=[],
            graph_traversals=[],
            reasoning="Test",
            complexity_score=0.5
        )
        
        with patch.object(agent, '_semantic_search', new_callable=AsyncMock) as mock_semantic:
            mock_semantic.return_value = [
                MemoryResult(content="Semantic result", source="faiss", score=0.9)
            ]
            results = await agent.hybrid_search(plan, user_id=1)
            assert len(results) == 1
            assert results[0].source == "faiss"
            mock_semantic.assert_called_once_with(["test query"], 1)
    
    @pytest.mark.asyncio
    async def test_hybrid_search_with_no_results(self, retrieval_plan):
        """Test hybrid search with no results."""
        agent = RetrievalAgent()
        
        with patch.object(agent, '_semantic_search', new_callable=AsyncMock) as mock_semantic:
            mock_semantic.return_value = []
            with patch.object(agent, '_keyword_search', new_callable=AsyncMock) as mock_keyword:
                mock_keyword.return_value = []
                with patch.object(agent, '_graph_search', new_callable=AsyncMock) as mock_graph:
                    mock_graph.return_value = []
                    results = await agent.hybrid_search(retrieval_plan, user_id=1)
                    assert results == []
    
    @pytest.mark.asyncio
    async def test_hybrid_search_deduplication(self, retrieval_plan):
        """Test that hybrid search deduplicates results."""
        agent = RetrievalAgent()
        
        with patch.object(agent, '_semantic_search', new_callable=AsyncMock) as mock_semantic:
            mock_semantic.return_value = [
                MemoryResult(content="Duplicate result", source="faiss", score=0.9)
            ]
            with patch.object(agent, '_keyword_search', new_callable=AsyncMock) as mock_keyword:
                mock_keyword.return_value = [
                    MemoryResult(content="Duplicate result", source="keyword", score=0.8)
                ]
                with patch.object(agent, '_graph_search', new_callable=AsyncMock) as mock_graph:
                    mock_graph.return_value = []
                    results = await agent.hybrid_search(retrieval_plan, user_id=1)
                    # Should deduplicate
                    assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_semantic_search(self):
        """Test semantic search method with async mock."""
        agent = RetrievalAgent()
        
        # Create an async mock for search_similar
        mock_search = AsyncMock(return_value=[
            {"id": 1, "content": "Result 1", "score": 0.95},
            {"id": 2, "content": "Result 2", "score": 0.85}
        ])
        
        # Patch the vector_store's search_similar method
        with patch.object(agent.vector_store, 'search_similar', mock_search):
            results = await agent._semantic_search(["test query"], user_id=1)
            
            assert len(results) == 2
            assert results[0].source == "faiss"
            assert results[0].score == 0.95
            assert results[0].metadata.get("memory_id") == 1
            mock_search.assert_called_once_with("test query", 1, limit=10)
    
    @pytest.mark.asyncio
    async def test_semantic_search_with_multiple_queries(self):
        """Test semantic search with multiple queries."""
        agent = RetrievalAgent()
        
        # Create an async mock
        mock_search = AsyncMock(return_value=[{"id": 1, "content": "Result", "score": 0.9}])
        
        with patch.object(agent.vector_store, 'search_similar', mock_search):
            results = await agent._semantic_search(["q1", "q2"], user_id=1)
            
            assert len(results) == 2
            assert mock_search.call_count == 2
    
    @pytest.mark.asyncio
    async def test_semantic_search_handles_empty_results(self):
        """Test semantic search handles empty results."""
        agent = RetrievalAgent()
        
        # Create an async mock that returns empty list
        mock_search = AsyncMock(return_value=[])
        
        with patch.object(agent.vector_store, 'search_similar', mock_search):
            results = await agent._semantic_search(["test query"], user_id=1)
            assert results == []

if __name__ == "__main__":
    pytest.main(["-v", __file__])
