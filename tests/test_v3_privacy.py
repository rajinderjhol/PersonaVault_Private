import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.cross_env_service import CrossEnvironmentService
from app.swarm.core.privacy import PrivacyAbstractionAgent

@pytest.mark.asyncio
async def test_cross_env_transfer_mocked():
    # 1. Mock Agent
    mock_generator = MagicMock()
    mock_generator.generate = AsyncMock(return_value={
        "answer": """
        {
            "abstract_title": "Anonymized Access Policy",
            "abstract_content": "Requests to restricted paths must be verified by the centralized identity provider.",
            "universal_anchors": ["auth", "verification"],
            "privacy_confidence": 0.99,
            "original_id_hash": "abc-123-hash"
        }
        """
    })
    agent = PrivacyAbstractionAgent(generator=mock_generator)
    
    # 2. Mock Services
    mock_crystallization_svc = MagicMock()
    mock_crystallization_svc.get_patterns = AsyncMock(return_value=[
        {"id": "p1", "content": "Internal: John Doe approved invoice #42 for \$500", "metadata": {"domain": "finance"}}
    ])
    mock_crystallization_svc.crystallize_pattern = AsyncMock(return_value="shared-456")
    
    # Mock environment_service.get_environment
    from app.api.v2.services.environment_service import environment_service
    environment_service.get_environment = AsyncMock(return_value=MagicMock(id="env-target"))
    
    # 3. Test Service
    service = CrossEnvironmentService(agent=agent, crystallization_svc=mock_crystallization_svc)
    result = await service.transfer_intelligence("env-source", "env-target")
    
    assert result["status"] == "success"
    assert result["patterns_transferred"] == 1
    assert "shared-456" in result["transferred_ids"]
    
    # Verify crystallization was called with SHARED prefix
    args, kwargs = mock_crystallization_svc.crystallize_pattern.call_args
    assert "SHARED:" in args[1]["title"]
    assert "cross-env-transfer" in args[1]["tags"]
    
    print("\n✅ Cross-environment privacy transfer verified.")

@pytest.mark.asyncio
async def test_privacy_negative_assertion():
    # Real agent, mocked generator
    mock_generator = MagicMock()
    mock_generator.generate = AsyncMock(return_value={
        "answer": """
        {
            "abstract_title": "Anonymized Finance Policy",
            "abstract_content": "Approve invoices only if they follow the standard corporate expenditure policy.",
            "universal_anchors": ["finance", "approval"],
            "privacy_confidence": 0.99,
            "original_id_hash": "hash-val"
        }
        """
    })
    agent = PrivacyAbstractionAgent(generator=mock_generator)
    
    # Input with PII
    raw_pattern = {"content": "Internal: John Doe approved invoice #42 for $500"}
    abstracted = await agent.abstract_pattern(raw_pattern)
    
    # Negative assertions
    content = abstracted["abstract_content"]
    assert "John Doe" not in content
    assert "$500" not in content
    assert "42" not in content
    assert "invoice" in content # Generic term should remain
    
    print("\n✅ Privacy negative assertions verified.")

if __name__ == "__main__":
    asyncio.run(test_cross_env_transfer_mocked())
    asyncio.run(test_privacy_negative_assertion())
