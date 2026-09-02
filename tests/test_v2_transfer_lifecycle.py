import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from app.api.v2.models.environment import Environment
from app.api.v2.models.transfer import SensitivityClassification, AbstractionLevel
from app.api.v2.services.transfer_service import TransferService
from app.api.v2.services.crystallization_service import CrystallizationService
from app.api.v2.services.transfer_coordinator import TransferCoordinator
from app.services.memory_service import MemoryService

@pytest.mark.asyncio
async def test_governed_transfer_lifecycle():
    """
    Test the Governed Knowledge Transfer Lifecycle (Priority 1):
    1. Successfully transfer pattern from Internal to Confidential environment.
    2. Fail transfer when sensitivity exceeds target environment max.
    3. Fail transfer when abstraction level is not allowed.
    """
    
    # Setup
    now = datetime.utcnow()
    env_internal = Environment(
        id="env_internal", 
        name="Internal Env", 
        owner_principal_id="p1", 
        status="active", 
        type="standard",
        max_sensitivity=SensitivityClassification.INTERNAL,
        created_at=now,
        updated_at=now
    )
    
    env_confidential = Environment(
        id="env_confidential", 
        name="Confidential Env", 
        owner_principal_id="p1", 
        status="active", 
        type="standard",
        max_sensitivity=SensitivityClassification.CONFIDENTIAL,
        created_at=now,
        updated_at=now
    )
    
    env_public = Environment(
        id="env_public", 
        name="Public Env", 
        owner_principal_id="p1", 
        status="active", 
        type="standard",
        max_sensitivity=SensitivityClassification.PUBLIC,
        created_at=now,
        updated_at=now
    )

    memory_service = AsyncMock(spec=MemoryService)
    crystallization_service = CrystallizationService(memory_service=memory_service)
    transfer_service = TransferService(crystallization_service=crystallization_service)
    coordinator = TransferCoordinator(transfer_service, crystallization_service)

    # 1. Success Case: Internal -> Confidential
    pattern_id = "123"
    memory_service.get_memory.return_value = {
        "id": 123,
        "content": "Secret internal sauce",
        "metadata": {"type": "crystallized_pattern", "tags": ["strategy"], "title": "Strategy A"}
    }
    # Mock save_memory to return a dummy result
    mock_res = MagicMock()
    mock_res.id = 456
    memory_service.save_memory.return_value = mock_res

    result = await coordinator.execute_transfer_lifecycle(
        source_env=env_internal,
        target_env=env_confidential,
        pattern_id=pattern_id,
        sensitivity=SensitivityClassification.INTERNAL,
        abstraction=AbstractionLevel.GENERALIZED
    )

    assert result.status == "transferred"
    assert memory_service.save_memory.called
    print("\n✅ Success Case: Internal -> Confidential verified.")

    # 2. Failure Case: Internal -> Public (Sensitivity Violation)
    memory_service.save_memory.reset_mock()
    
    result_fail = await coordinator.execute_transfer_lifecycle(
        source_env=env_internal,
        target_env=env_public,
        pattern_id=pattern_id,
        sensitivity=SensitivityClassification.INTERNAL,
        abstraction=AbstractionLevel.GENERALIZED
    )

    assert result_fail.status == "rejected"
    assert not memory_service.save_memory.called
    print("✅ Failure Case: Sensitivity guard verified.")

    # 3. Failure Case: Abstraction Level Violation
    env_public_strict = Environment(
        id="env_public_strict", 
        name="Public Strict Env", 
        owner_principal_id="p1", 
        status="active", 
        type="standard",
        max_sensitivity=SensitivityClassification.PUBLIC,
        allowed_abstraction_levels=[AbstractionLevel.PRINCIPLE], # Only principles allowed
        created_at=now,
        updated_at=now
    )
    
    result_fail_abs = await coordinator.execute_transfer_lifecycle(
        source_env=env_internal,
        target_env=env_public_strict,
        pattern_id=pattern_id,
        sensitivity=SensitivityClassification.PUBLIC, # Lower sensitivity to pass first guard
        abstraction=AbstractionLevel.GENERALIZED # But generalized is not allowed
    )

    assert result_fail_abs.status == "rejected"
    assert not memory_service.save_memory.called
    print("✅ Failure Case: Abstraction guard verified.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_governed_transfer_lifecycle())
