import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from app.api.v2.models.environment import Environment
from app.api.v2.models.principal import Principal
from app.api.v2.services.crystallization_service import CrystallizationService
from app.services.memory_service import MemoryService
from app.api.v2.services.membership_service import MembershipService
from app.swarm.context import AgentEnvironmentContext
from app.swarm.specialized.security_agent import SecurityAgent

@pytest.mark.asyncio
async def test_crystallization_verification():
    """
    Crystallization Verification Test:
    1. Interact with an agent in Environment A to trigger a learning event.
    2. Verify Storage: Check that the resulting pattern is stored in Environment A with the correct environment_id.
    3. Cross-Check Isolation: Ensure that an agent in Environment B cannot recall the patterns learned in Environment A.
    4. Confirm Recall: Ensure that a subsequent query in Environment A successfully retrieves the learned pattern.
    """

    # Setup: Create two environments, two principals, and mock services
    now = datetime.utcnow()
    env_a = Environment(id="env_a", name="Environment A", owner_principal_id="principal_a", status="active", type="standard", created_at=now, updated_at=now)
    env_b = Environment(id="env_b", name="Environment B", owner_principal_id="principal_b", status="active", type="standard", created_at=now, updated_at=now)
    
    # Mock the memory service to verify storage and retrieval
    memory_service = AsyncMock(spec=MemoryService)
    # Mock retrieve_memory for search_memories
    memory_service.search_memories = AsyncMock()
    # Mock save_memory
    memory_service.save_memory = AsyncMock()
    
    crystallization_service = CrystallizationService(memory_service=memory_service)
    
    # Mock the membership service
    membership_service = AsyncMock(spec=MembershipService)

    # Step 1: Interact with agent in Environment A to trigger learning
    context_a = AgentEnvironmentContext(
        environment=env_a,
        memory_service=memory_service,
        authority_service=AsyncMock(),
        crystallization_service=crystallization_service,
        prediction_service=AsyncMock(),
        simulation_service=AsyncMock()
    )
    
    agent_a = SecurityAgent(name="SecurityAgentA")
    agent_a.set_context(context_a)
    
    # Trigger learning event
    threat_data = {"type": "security_breach", "severity": "high", "details": "Unauthorized access detected"}
    # Mock the dependency checks in SecurityAgent
    agent_a.context.check_authority = AsyncMock(return_value=True)
    agent_a.context.predict = AsyncMock(return_value={"outcome": "predicted"})
    
    # Setup store_memory to return a dummy ID
    mock_memory_id = MagicMock()
    mock_memory_id.id = 999
    memory_service.save_memory.return_value = mock_memory_id
    
    learning_result = await agent_a.analyze_threat(threat_data)
    
    # Step 2: Verify Storage
    assert learning_result["status"] == "responded"
    
    # Verify the memory service was called with the correct environment_id
    memory_service.save_memory.assert_called_once()
    call_args = memory_service.save_memory.call_args
    assert call_args.kwargs.get("environment_id") == env_a.id
    assert call_args.kwargs.get("memory_type") == "crystallized_pattern"

    # Step 3: Cross-Check Isolation - Ensure Environment B cannot recall Environment A's patterns
    context_b = AgentEnvironmentContext(
        environment=env_b,
        memory_service=memory_service,
        authority_service=AsyncMock(),
        crystallization_service=crystallization_service,
        prediction_service=AsyncMock(),
        simulation_service=AsyncMock()
    )
    
    # Setup memory retrieval for B to return nothing
    memory_service.search_memories.return_value = []
    
    patterns_b = await context_b.recall_patterns(query="security threat")
    
    # Verify that the memory service was called with Environment B's ID
    memory_service.search_memories.assert_called_with(
        user_id=1,
        query="security threat",
        limit=5,
        environment_id=env_b.id
    )
    assert len(patterns_b) == 0

    # Step 4: Confirm Recall - Ensure Environment A can retrieve the learned pattern
    # Mock memory retrieval for A to return the pattern
    memory_service.search_memories.return_value = [{
        "id": 999,
        "content": "Pattern content",
        "metadata": {"type": "crystallized_pattern", "environment_id": env_a.id}
    }]
    
    patterns_a = await context_a.recall_patterns(query="security threat")
    
    assert len(patterns_a) > 0
    assert patterns_a[0]["metadata"]["environment_id"] == env_a.id
    
from app.api.v2.services.runtime.outcome_learning_bridge import OutcomeLearningBridge

@pytest.mark.asyncio
async def test_outcome_learning_bridge():
    """
    Verification Test for Outcome -> Learning Bridge:
    1. Simulate an 'Outcome' event.
    2. Ensure OutcomeLearningBridge detects the success.
    3. Verify it automatically triggers crystallization.
    """
    # Setup
    now = datetime.utcnow()
    env = Environment(id="env_test", name="Test Env", owner_principal_id="p1", status="active", type="standard", created_at=now, updated_at=now)
    
    memory_service = AsyncMock(spec=MemoryService)
    crystallization_service = AsyncMock(spec=CrystallizationService)
    
    bridge = OutcomeLearningBridge(crystallization_service, memory_service)
    
    outcome = {"success": True, "result": "Action completed successfully"}
    
    # Run
    await bridge.process_outcome(env, outcome)
    
    # Verify crystallization was triggered
    crystallization_service.crystallize_pattern.assert_called_once()
    call_args = crystallization_service.crystallize_pattern.call_args
    assert call_args.kwargs["environment"].id == env.id
    assert "success" in call_args.kwargs["pattern_data"]["content"]

    print("\n✅ Outcome -> Learning Bridge Test Passed")
