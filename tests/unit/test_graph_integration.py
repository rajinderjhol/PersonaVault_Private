import pytest
import asyncio
from unittest.mock import MagicMock, patch, call
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.evidence_extractor import EvidenceExtractor
from app.models.evidence import EvidenceBlock
from datetime import datetime

@pytest.mark.asyncio
async def test_evidence_extractor_graph_integration():
    """Test that EvidenceExtractor calls GraphService when storing evidence."""
    
    # 1. Mock the DB session
    mock_db = MagicMock(spec=AsyncSession)
    
    # Mock result to be awaitable
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    
    # 2. Patch the GraphService
    with patch('app.services.graph_service.graph_service') as mock_graph_service:
        # 3. Initialize Extractor with mocked DB
        extractor = EvidenceExtractor(db=mock_db)
        
        # 4. Prepare mock evidence block
        block_data = {
            "content": "This is a test document about Company X.",
            "source": "test_doc.txt",
            "source_type": "text",
            "metadata": {"paragraph": 1},
            "confidence": 0.9,
            "provenance_score": 0.9
        }
        
        # 5. Execute storage
        await extractor._store_evidence_block(block_data, job_id=1)
        
        # 6. Assert GraphService was called
        mock_graph_service.create_evidence_node.assert_called()
        print("✅ GraphService integration verified via mock")

if __name__ == "__main__":
    asyncio.run(test_evidence_extractor_graph_integration())
