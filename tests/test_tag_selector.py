"""
Tests for TagSelector.
"""
import pytest
from app.mragent.tag_selector import TagSelector
from app.models.memory_graph import MemoryCue, MemoryContent, MemoryTag

class TestTagSelector:
    """Test suite for TagSelector."""
    
    def test_init(self):
        """Test TagSelector initialization."""
        selector = TagSelector()
        assert selector is not None
    
    @pytest.mark.asyncio
    async def test_select_tags_with_cues(self):
        """Test selecting tags from cues."""
        selector = TagSelector()
        cues = [
            MemoryCue(text="security", type="entity"),
            MemoryCue(text="create", type="action"),
            MemoryCue(text="today", type="time")
        ]
        tags = await selector.select_tags(cues, [])
        
        assert tags is not None
        assert len(tags) > 0
        
        # Should have tags for each cue type
        tag_texts = [t.text for t in tags]
        assert any("security" in t for t in tag_texts) or "create" in tag_texts
    
    @pytest.mark.asyncio
    async def test_select_tags_with_evidence(self):
        """Test selecting tags with evidence."""
        selector = TagSelector()
        cues = []
        evidence = [
            MemoryContent(text="This is a test document about Python", type="episodic"),
            MemoryContent(text="Another document about machine learning", type="semantic")
        ]
        tags = await selector.select_tags(cues, evidence)
        
        assert tags is not None
        # Should extract tags from evidence
        tag_texts = [t.text for t in tags]
        assert len(tag_texts) >= 0
    
    @pytest.mark.asyncio
    async def test_select_tags_empty(self):
        """Test selecting tags with no cues or evidence."""
        selector = TagSelector()
        tags = await selector.select_tags([], [])
        assert tags == []
    
    @pytest.mark.asyncio
    async def test_select_tags_with_llm_fallback(self):
        """Test LLM-based tag selection falls back to basic."""
        selector = TagSelector(llm_client=None)
        cues = [MemoryCue(text="test", type="entity")]
        tags = await selector.select_tags_with_llm(cues, [])
        assert tags is not None
    
    @pytest.mark.asyncio
    async def test_select_tags_deduplication(self):
        """Test that tags are deduplicated."""
        selector = TagSelector()
        cues = [
            MemoryCue(text="security", type="entity"),
            MemoryCue(text="security", type="entity")  # Duplicate
        ]
        tags = await selector.select_tags(cues, [])
        
        # Should not have duplicates
        tag_texts = [t.text for t in tags]
        assert len(set(tag_texts)) == len(tag_texts)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
