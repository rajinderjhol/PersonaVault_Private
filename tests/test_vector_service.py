"""
Tests for VectorService - matching actual implementation.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import numpy as np
from app.services.vector_service import VectorService

class TestVectorService:
    """Test suite for VectorService."""
    
    def test_init(self):
        """Test VectorService initialization."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            service = VectorService()
            assert service is not None
            assert service.dimension == 768
            assert service.index is not None
    
    @pytest.mark.asyncio
    async def test_get_embedding(self):
        """Test embedding generation."""
        with patch('os.path.exists', return_value=False):
            service = VectorService()
            
            # Mock requests.post to return a valid response
            with patch('app.services.vector_service.requests.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3] + [0.0] * 765}
                mock_post.return_value = mock_response
                
                embedding = await service._get_embedding("test text")
                assert isinstance(embedding, np.ndarray)
                assert embedding.shape == (service.dimension,)
    
    @pytest.mark.asyncio
    async def test_get_embedding_fallback(self):
        """Test embedding generation fallback when Ollama fails."""
        with patch('os.path.exists', return_value=False):
            service = VectorService()
            
            with patch('app.services.vector_service.requests.post') as mock_post:
                mock_post.side_effect = Exception("Connection error")
                
                embedding = await service._get_embedding("test text")
                assert isinstance(embedding, np.ndarray)
                assert embedding.shape == (service.dimension,)
                assert np.all(embedding == 0)
    
    @pytest.mark.asyncio
    async def test_index_memory(self):
        """Test indexing a memory."""
        with patch('os.path.exists', return_value=False):
            service = VectorService()
            
            with patch.object(service, '_get_embedding', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = np.ones(service.dimension) * 0.5
                
                await service.index_memory(1, "Test content", user_id=1)
                
                # Verify metadata was added
                assert len(service.metadata) > 0
                last_idx = service.index.ntotal - 1
                assert service.metadata[last_idx]["id"] == 1
                assert service.metadata[last_idx]["user_id"] == 1
    
    @pytest.mark.asyncio
    async def test_search_similar_empty_index(self):
        """Test search when index is empty."""
        with patch('os.path.exists', return_value=False):
            service = VectorService()
            
            results = await service.search_similar("test query", user_id=1)
            assert results == []
    
    @pytest.mark.asyncio
    async def test_search_similar_with_data(self):
        """Test search with indexed data."""
        with patch('os.path.exists', return_value=False):
            service = VectorService()
            
            with patch.object(service, '_get_embedding', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = np.ones(service.dimension) * 0.5
                
                await service.index_memory(1, "Test content", user_id=1)
                
                results = await service.search_similar("test query", user_id=1)
                assert isinstance(results, list)
    
    def test_save_index(self):
        """Test saving index to disk."""
        with patch('os.path.exists', return_value=False):
            service = VectorService()
            
            with patch('faiss.write_index') as mock_write:
                with patch('pickle.dump') as mock_pickle:
                    service._save_index()
                    mock_write.assert_called_once()
                    mock_pickle.assert_called_once()
    
    def test_load_existing_index(self):
        """Test loading existing index from disk."""
        with patch('os.path.exists', return_value=True):
            with patch('faiss.read_index') as mock_read:
                with patch('pickle.load') as mock_load:
                    mock_read.return_value = MagicMock()
                    mock_load.return_value = {0: {"id": 1, "content": "test", "user_id": 1}}
                    
                    service = VectorService()
                    assert service.index is not None
                    assert len(service.metadata) == 1
    
    def test_load_existing_index_fails(self):
        """Test handling when loading existing index fails."""
        with patch('os.path.exists', return_value=True):
            with patch('faiss.read_index') as mock_read:
                mock_read.side_effect = Exception("Load error")
                with patch('app.services.vector_service.logger.error'):
                    service = VectorService()
                    # Should create a new index
                    assert service.index is not None
                    assert service.metadata == {}

if __name__ == "__main__":
    pytest.main(["-v", __file__])
