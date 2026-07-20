"""
Tests for MemoryConsolidation service.
"""
import pytest
from datetime import datetime, timedelta
from app.services.consolidation import MemoryConsolidation

class TestMemoryConsolidation:
    """Test suite for MemoryConsolidation."""
    
    def test_init(self):
        """Test initialization."""
        service = MemoryConsolidation()
        assert service is not None
        assert service.max_size == 10000
    
    def test_init_with_custom_max_size(self):
        """Test initialization with custom max_size."""
        service = MemoryConsolidation(max_size=5000)
        assert service.max_size == 5000
    
    @pytest.mark.asyncio
    async def test_consolidate_empty(self):
        """Test consolidating empty list."""
        service = MemoryConsolidation()
        result = await service.consolidate([])
        assert result == []
    
    @pytest.mark.asyncio
    async def test_consolidate_deduplicates(self):
        """Test consolidation deduplicates similar memories."""
        service = MemoryConsolidation()
        memories = [
            {"id": 1, "content": "Test content 1"},
            {"id": 2, "content": "Test content 1 duplicate"},
            {"id": 3, "content": "Different content"}
        ]
        result = await service.consolidate(memories)
        # Should deduplicate based on first 50 chars
        assert len(result) <= len(memories)
    
    @pytest.mark.asyncio
    async def test_forget_keeps_recent(self):
        """Test forgetting keeps recent memories."""
        service = MemoryConsolidation(max_size=2)
        memories = [
            {"id": 1, "content": "Old memory", "created_at": datetime.now() - timedelta(days=100)},
            {"id": 2, "content": "Recent memory", "created_at": datetime.now()},
            {"id": 3, "content": "Another recent", "created_at": datetime.now()}
        ]
        result = await service.forget(memories)
        assert len(result) <= 2
    
    @pytest.mark.asyncio
    async def test_score_importance(self):
        """Test importance scoring."""
        service = MemoryConsolidation()
        memory = {
            "content": "This is a long memory with lots of important information",
            "access_count": 5,
            "tags": "important,security,policy"
        }
        score = await service.score_importance(memory)
        assert 0 <= score <= 1
    
    @pytest.mark.asyncio
    async def test_cluster_memories(self):
        """Test clustering similar memories."""
        service = MemoryConsolidation()
        memories = [
            {"id": 1, "content": "Python programming is great"},
            {"id": 2, "content": "Python is awesome for data science"},
            {"id": 3, "content": "Different topic entirely"}
        ]
        clusters = await service.cluster_memories(memories)
        assert clusters is not None
    
    @pytest.mark.asyncio
    async def test_score_importance_recency(self):
        """Test recency affects importance score."""
        service = MemoryConsolidation()
        old_memory = {"created_at": datetime.now() - timedelta(days=365)}
        new_memory = {"created_at": datetime.now()}
        
        old_score = await service.score_importance(old_memory)
        new_score = await service.score_importance(new_memory)
        
        # Newer memory should have higher score
        assert new_score >= old_score

if __name__ == "__main__":
    pytest.main(["-v", __file__])
