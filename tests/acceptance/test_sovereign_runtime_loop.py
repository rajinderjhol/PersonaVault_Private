import pytest
from unittest.mock import AsyncMock
from app.api.v2.models.environment import Environment
from app.api.v2.models.outcome import OutcomeSourceType, Outcome
from app.api.v2.services.crystallization_service import CrystallizationService
from app.api.v2.services.runtime.outcome_learning_bridge import OutcomeLearningBridge
from datetime import datetime

@pytest.mark.asyncio
async def test_sovereign_runtime_loop():
    """
    Decisive Runtime Test:
    1. Real Loop: Real Action -> Real Outcome -> Triggered Learning -> Crystallized Knowledge.
    2. Simulation Loop: Simulated Action -> Simulated Outcome -> Blocked Learning.
    """
    # Setup
    now = datetime.utcnow()
    env = Environment(id="env_sovereign", name="Sovereign Env", owner_principal_id="p1", status="active", type="standard", created_at=now, updated_at=now)
    
    # Mock services
    crystallization_service = AsyncMock(spec=CrystallizationService)
    # The bridge doesn't actually need memory_service to function if we mock the pattern detection
    bridge = OutcomeLearningBridge(crystallization_service, memory_service=AsyncMock())
    
    # Define success outcome
    real_outcome_data = {
        "success": True, 
        "result": {"summary": "Real-world success pattern"}
    }
    real_outcome = Outcome(
        id="o1",
        environment_id=env.id,
        decision_id="d1",
        source_type=OutcomeSourceType.REAL_ACTION,
        observed_at=now,
        result=real_outcome_data["result"],
        success=True,
        metrics={"confidence": 0.9},
        created_at=now,
        updated_at=now
    )

    # 1. Real Loop Execution
    result_id = await bridge.process_outcome(env, real_outcome)
    
    # Verify crystallization was triggered
    crystallization_service.crystallize_pattern.assert_called_once()
    print("\n✅ Real-world learning path verified.")

    # 2. Simulation Loop Execution
    simulated_outcome_data = {
        "success": True, 
        "result": {"summary": "Simulated success"}
    }
    simulated_outcome = Outcome(
        id="o2",
        environment_id=env.id,
        decision_id="d2",
        source_type=OutcomeSourceType.SIMULATION,
        observed_at=now,
        result=simulated_outcome_data["result"],
        success=True,
        metrics={"confidence": 0.9},
        created_at=now,
        updated_at=now
    )
    
    crystallization_service.reset_mock()
    
    # Verify simulation learning is blocked
    result_sim = await bridge.process_outcome(env, simulated_outcome)
    assert result_sim is None
    crystallization_service.crystallize_pattern.assert_not_called()
    
    print("✅ Simulation loop boundary verified (Learning blocked).")
    print("🚀 Sovereign Runtime Loop Operational.")
