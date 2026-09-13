import asyncio
import pytest
from app.services.discovery.discovery_service import DiscoveryService
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_scan_environment():
    discovery = DiscoveryService()
    findings = await discovery.scan_environment("data_test/discovery_mock/procurement")
    
    assert "procurement" in findings["path"]
    assert findings["total_files"] >= 3
    assert ".py" in findings["file_types"]
    assert ".json" in findings["file_types"]
    assert ".md" in findings["file_types"]
    assert "governance.md" in findings["content_samples"]
    print("\n✅ Scan environment verified.")

@pytest.mark.asyncio
async def test_suggest_pack_mocked():
    # Mock generator to avoid external dependency for unit test
    mock_generator = MagicMock()
    mock_generator.generate = AsyncMock(return_value={
        "answer": """
        {
            "pack": {
                "name": "procurement-intelligence",
                "domain": "procurement",
                "version": "1.0.0",
                "description": "Governs automated procurement and vendor validation"
            },
            "policies": [
                {
                    "name": "Auto Approval",
                    "description": "Approve invoices under 5000",
                    "conditions": ["amount < 5000"],
                    "actions": ["approve"]
                }
            ]
        }
        """
    })
    
    discovery = DiscoveryService(generator=mock_generator)
    scan_results = {
        "path": "/mock/procurement",
        "total_files": 3,
        "structure": ["governance.md", "schema.json", "validators.py"],
        "file_types": {".md": 1, ".json": 1, ".py": 1},
        "content_samples": {"governance.md": "Standard approval..."}
    }
    
    suggestion = await discovery.suggest_pack(scan_results)
    
    assert suggestion["pack"]["name"] == "procurement-intelligence"
    assert suggestion["pack"]["domain"] == "procurement"
    assert len(suggestion["policies"]) == 1
    print("✅ Suggest pack (mocked) verified.")

if __name__ == "__main__":
    asyncio.run(test_scan_environment())
    asyncio.run(test_suggest_pack_mocked())
