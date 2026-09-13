import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.synthesis_service import SynthesisService
from app.swarm.core.synthesis import SynthesisAgent

@pytest.mark.asyncio
async def test_meta_pattern_synthesis_mocked():
    # 1. Mock Agent
    mock_generator = MagicMock()
    mock_generator.generate = AsyncMock(return_value={
        "answer": """
        [
            {
                "title": "Universal Access Control",
                "content": "All requests to sensitive endpoints must include a valid JWT and an active organization_id.",
                "derived_from": ["p1", "p2"],
                "abstraction_level": "high",
                "reasoning": "Synthesizes individual auth patterns into a single master rule."
            }
        ]
        """
    })
    agent = SynthesisAgent(generator=mock_generator)
    
    # 2. Mock Crystallization Service
    mock_crystallization_svc = MagicMock()
    mock_crystallization_svc.get_patterns = AsyncMock(return_value=[
        {"id": "p1", "content": "Security: Check JWT for /api/v1", "metadata": {"domain": "security"}},
        {"id": "p2", "content": "Security: Check org_id for /admin", "metadata": {"domain": "security"}}
    ])
    mock_crystallization_svc.crystallize_pattern = AsyncMock(return_value="meta-123")
    
    # 3. Test Service
    service = SynthesisService(crystallization_svc=mock_crystallization_svc, agent=agent)
    result = await service.compound_intelligence("env-test-001")
    
    assert result["status"] == "success"
    assert result["input_patterns"] == 2
    assert result["meta_patterns_created"] == 1
    assert "meta-123" in result["meta_pattern_ids"]
    
    # Verify crystallization was called with META prefix
    args, kwargs = mock_crystallization_svc.crystallize_pattern.call_args
    assert "META:" in args[1]["title"]
    assert "meta-pattern" in args[1]["tags"]
    
    print("\n✅ Meta-pattern synthesis verified.")

if __name__ == "__main__":
    asyncio.run(test_meta_pattern_synthesis_mocked())
