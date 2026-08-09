"""
Tests for ConsolidationService.
"""
import pytest
from unittest.mock import MagicMock
from app.services.consolidation_service import ConsolidationService

class TestConsolidationService:
    """Test suite for ConsolidationService."""
    
    def test_init(self):
        """Test initialization."""
        mock_factory = MagicMock()
        service = ConsolidationService(session_factory=mock_factory)
        assert service is not None
        assert service.session_factory == mock_factory

if __name__ == "__main__":
    pytest.main(["-v", __file__])

