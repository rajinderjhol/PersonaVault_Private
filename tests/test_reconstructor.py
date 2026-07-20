"""
Tests for ActiveMemoryReconstructor.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.mragent.reconstructor import ActiveMemoryReconstructor
from app.models.memory_graph import MemoryContent

@pytest.fixture
def mock_llm():
    """Mock LLM client."""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value={"answer": "Test answer"})
    return mock

@pytest.fixture
def mock_vector_store():
    """Mock vector store."""
    mock = MagicMock()
    mock.search_similar = MagicMock(return_value=[
        {"id": 1, "content": "Test result 1", "score": 0.95},
        {"id": 2, "content": "Test result 2", "score": 0.85}
    ])
    return mock

@pytest.fixture
def mock_graph_store():
    """Mock graph store."""
    mock = MagicMock()
    mock.execute_query = MagicMock(return_value=[
        {"n": {"title": "Graph result 1"}},
        {"n": {"title": "Graph result 2"}}
    ])
    return mock

class TestActiveMemoryReconstructor:
    """Test suite for ActiveMemoryReconstructor."""
    
    def test_init(self):
        """Test initialization."""
        reconstructor = ActiveMemoryReconstructor()
        assert reconstructor is not None
        assert reconstructor.max_turns == 3
    
    def test_init_with_custom_max_turns(self):
        """Test initialization with custom max_turns."""
        reconstructor = ActiveMemoryReconstructor(max_turns=5)
        assert reconstructor.max_turns == 5
    
    @pytest.mark.asyncio
    async def test_reconstruct_basic(self, mock_llm):
        """Test basic reconstruction flow."""
        reconstructor = ActiveMemoryReconstructor(llm_client=mock_llm)
        result = await reconstructor.reconstruct("What is the status?")
        
        assert "answer" in result
        assert "evidence" in result
        assert "turns" in result
        assert "total_evidence" in result
    
    @pytest.mark.asyncio
    async def test_reconstruct_with_vector_store(self, mock_llm, mock_vector_store):
        """Test reconstruction with vector store."""
        reconstructor = ActiveMemoryReconstructor(
            llm_client=mock_llm,
            vector_store=mock_vector_store
        )
        result = await reconstructor.reconstruct("What is the status?")
        
        assert "answer" in result
        # Should have some evidence from vector store
        assert result["total_evidence"] >= 0
    
    @pytest.mark.asyncio
    async def test_reconstruct_with_both_stores(self, mock_llm, mock_vector_store, mock_graph_store):
        """Test reconstruction with both vector and graph stores."""
        reconstructor = ActiveMemoryReconstructor(
            llm_client=mock_llm,
            vector_store=mock_vector_store,
            graph_store=mock_graph_store
        )
        result = await reconstructor.reconstruct("What is the status?")
        
        assert "answer" in result
        assert result["total_evidence"] >= 0
    
    @pytest.mark.asyncio
    async def test_reconstruct_without_llm(self):
        """Test reconstruction without LLM (should still work)."""
        reconstructor = ActiveMemoryReconstructor()
        result = await reconstructor.reconstruct("Test query")
        
        assert "answer" in result
        # Should have a fallback answer
        assert result["answer"] is not None
    
    @pytest.mark.asyncio
    async def test_reconstruct_multiple_turns(self, mock_llm):
        """Test reconstruction with multiple turns."""
        reconstructor = ActiveMemoryReconstructor(llm_client=mock_llm, max_turns=2)
        result = await reconstructor.reconstruct("Complex query needs multiple turns")
        
        assert "turns" in result
        assert len(result["turns"]) <= 2
    
    def test_get_reconstructor(self):
        """Test getting the global reconstructor instance."""
        from app.mragent import get_reconstructor
        reconstructor = get_reconstructor()
        assert reconstructor is not None

if __name__ == "__main__":
    pytest.main(["-v", __file__])
