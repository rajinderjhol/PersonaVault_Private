import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.policy_inference_service import PolicyInferenceService
from app.swarm.core.inference import PolicyInferenceAgent

@pytest.mark.asyncio
async def test_policy_inference_mocked():
    # 1. Mock Agent
    mock_generator = MagicMock()
    mock_generator.generate = AsyncMock(return_value={
        "answer": """
        [
            {
                "name": "Strict Budget Cap",
                "description": "Reject all expenses over 10000 without multi-level approval.",
                "conditions": ["amount > 10000"],
                "reasoning": "Recurring corrections for high-value rejections.",
                "confidence": 0.95
            }
        ]
        """
    })
    agent = PolicyInferenceAgent(generator=mock_generator)
    
    # 2. Mock Database Session
    mock_db = MagicMock()
    
    # Mock corrections fetch
    mock_event = MagicMock()
    mock_event.id = 1
    mock_event.event_type = "finance"
    mock_event.decision = "approved"
    mock_event.correction = {"action": "reject"}
    mock_event.reason = "Over budget"
    mock_event.learned = False
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.side_effect = [
        [mock_event], # Events
        []            # Existing Policies
    ]
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    
    # 3. Test Service
    service = PolicyInferenceService(db=mock_db, agent=agent)
    result = await service.infer_and_propose("finance", user_id=1)
    
    assert result["status"] == "success"
    assert result["events_processed"] == 1
    assert "Strict Budget Cap" in result["policies_proposed"]
    
    # Verify DB calls
    assert mock_db.add.called
    assert mock_db.commit.called
    
    print("\n✅ Policy inference verified.")

if __name__ == "__main__":
    asyncio.run(test_policy_inference_mocked())
