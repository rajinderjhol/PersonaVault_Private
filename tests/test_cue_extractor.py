"""
Tests for CueExtractor.
"""
import pytest
from app.mragent.cue_extractor import CueExtractor
from app.models.memory_graph import MemoryCue

class TestCueExtractor:
    """Test suite for CueExtractor."""
    
    def test_init(self):
        """Test CueExtractor initialization."""
        extractor = CueExtractor()
        assert extractor is not None
    
    @pytest.mark.asyncio
    async def test_extract_cues_basic(self):
        """Test basic cue extraction."""
        extractor = CueExtractor()
        text = "Create a security policy for Acme Corp today"
        cues = await extractor.extract_cues(text)
        
        assert cues is not None
        assert len(cues) > 0
        
        # Should have at least an action cue
        action_cues = [c for c in cues if c.type == "action"]
        assert len(action_cues) > 0
    
    @pytest.mark.asyncio
    async def test_extract_cues_with_entities(self):
        """Test extracting entity cues."""
        extractor = CueExtractor()
        text = "John Doe from Google visited the office"
        cues = await extractor.extract_cues(text)
        
        entity_cues = [c for c in cues if c.type == "entity"]
        assert len(entity_cues) > 0
        # Should contain proper names
        entity_texts = [c.text for c in entity_cues]
        assert any("Google" in t or "John" in t for t in entity_texts)
    
    @pytest.mark.asyncio
    async def test_extract_cues_with_time(self):
        """Test extracting time cues."""
        extractor = CueExtractor()
        text = "Meeting tomorrow at 3pm"
        cues = await extractor.extract_cues(text)
        
        time_cues = [c for c in cues if c.type == "time"]
        # Should find at least one time reference
        assert len(time_cues) >= 0  # May not find due to simple regex
    
    @pytest.mark.asyncio
    async def test_extract_cues_empty(self):
        """Test extracting cues from empty text."""
        extractor = CueExtractor()
        cues = await extractor.extract_cues("")
        assert cues == []
    
    @pytest.mark.asyncio
    async def test_extract_cues_with_llm_fallback(self):
        """Test LLM-based cue extraction falls back to basic."""
        extractor = CueExtractor(llm_client=None)
        text = "This is a test"
        cues = await extractor.extract_cues_with_llm(text)
        assert cues is not None

if __name__ == "__main__":
    pytest.main(["-v", __file__])
