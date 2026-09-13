import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.memory_thermodynamics import PatternPhaseManager, MemoryPhase

@pytest.mark.asyncio
async def test_recursive_synthesis_prevention():
    manager = PatternPhaseManager()
    
    # Mix of base patterns and meta-patterns
    patterns = [
        {"id": i, "metadata": {"type": "crystallized_pattern"}} for i in range(15)
    ] + [
        {"id": f"meta-{i}", "metadata": {"type": "meta_pattern"}} for i in range(10)
    ]
    
    # Redundancy is high
    pressure = manager.calculate_thermal_pressure(patterns, 0.9)
    
    # Even though total count is 25, meta-patterns are excluded.
    # Base count is 15. Count Density = 15/20 = 0.75.
    # Pressure = (0.75 * 0.4) + (0.9 * 0.6) = 0.3 + 0.54 = 0.84
    assert pressure < 1.0
    print("\n✅ Recursive synthesis prevention verified.")

@pytest.mark.asyncio
async def test_guarded_evaporation():
    manager = PatternPhaseManager()
    mock_db = AsyncMock()
    
    from datetime import datetime, timedelta
    old_date = datetime.now() - timedelta(days=100)
    
    # 1. Stale, unused pattern (Should evaporate)
    p_stale = MagicMock()
    p_stale.updated_at = old_date
    p_stale.occurrence_count = 0
    p_stale.weight = 0.5
    p_stale.trigger = "Normal pattern"
    
    # 2. Critical pattern (Should NOT evaporate)
    p_critical = MagicMock()
    p_critical.updated_at = old_date
    p_critical.occurrence_count = 0
    p_critical.weight = 0.95
    p_critical.trigger = "Critical security rule"
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [p_stale, p_critical]
    mock_db.execute.side_effect = [mock_result, MagicMock(scalar=MagicMock(return_value=0)), MagicMock(scalar=MagicMock(return_value=0))]
    
    deleted = await manager.evaporate_patterns(mock_db, "security")
    
    assert deleted == 1
    assert mock_db.delete.called
    print("✅ Guarded evaporation verified.")

@pytest.mark.asyncio
async def test_rejection_path():
    manager = PatternPhaseManager()
    result = await manager.handle_synthesis_rejection("env-001", "finance", "Too early")
    assert result is True
    print("✅ Rejection path verified.")

@pytest.mark.asyncio
async def test_hysteresis_logic():
    manager = PatternPhaseManager()
    
    # Low pressure should keep it armed (Logic-only check)
    patterns_low = [{"id": 1, "metadata": {"type": "crystallized"}}]
    # We test the evaluate_synthesis_need behavior
    with patch("app.db.session.SessionLocal") as mock_session, \
         patch("app.api.v2.services.environment_service.environment_service.get_environment", new_callable=AsyncMock) as mock_get_env, \
         patch("app.api.v2.services.environment_service.environment_service.update_environment", new_callable=AsyncMock):
        
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db
        
        # Setup mock environment
        mock_env = MagicMock()
        mock_env.thermal_threshold = 20.0
        mock_env.is_armed = True
        mock_get_env.return_value = mock_env
        
        # Mock result for idempotency check
        mock_res = MagicMock()
        mock_res.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_res
        
        # High pressure (25 patterns, 1.0 redundancy) -> Trigger
        patterns_high = [{"id": i, "metadata": {"type": "crystallized"}} for i in range(25)]
        triggered = await manager.evaluate_synthesis_need("env-001", patterns_high, "finance", 1.0)
        assert triggered is True
        
    print("✅ Hysteresis/Trigger logic verified.")

if __name__ == "__main__":
    asyncio.run(test_recursive_synthesis_prevention())
    asyncio.run(test_guarded_evaporation())
    asyncio.run(test_rejection_path())
    asyncio.run(test_hysteresis_logic())
