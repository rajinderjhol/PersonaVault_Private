from datetime import datetime
import pytest
from unittest.mock import AsyncMock
from app.api.v2.models.environment import Environment, EnvironmentStatus
from app.api.v2.models.goal import Goal, GoalStatus
from app.api.v2.models.reasoning_chain import ReasoningChain
from app.api.v2.models.deliberation import Deliberation
from app.swarm.orchestrators.reasoning_orchestrator import ReasoningOrchestrator
from app.swarm.context import AgentEnvironmentContext

@pytest.mark.asyncio
async def test_reasoning_about_goal():
    """
    Test the complete General Reasoning process.
    """
    # Setup
    env = Environment(
        id="env_test",
        type="test",
        name="Test Environment",
        owner_principal_id="principal_test",
        status=EnvironmentStatus.ACTIVE,
        created_at=datetime.utcnow(), 
        updated_at=datetime.utcnow()
    )
    # Mock services for context
    context = AgentEnvironmentContext(
        environment=env,
        memory_service=AsyncMock(),
        authority_service=AsyncMock(),
        crystallization_service=AsyncMock(),
        prediction_service=AsyncMock(),
        simulation_service=AsyncMock()
    )
    
    # Create mocks
    goal_decomposition = AsyncMock()
    reasoning_engine = AsyncMock()
    deliberation_service = AsyncMock()
    knowledge_agent = AsyncMock()
    prediction_agent = AsyncMock()
    simulation_agent = AsyncMock()
    learning_agent = AsyncMock()
    
    # Mock goal decomposition
    mock_goal = Goal(
        id="goal_1",
        environment_id=env.id,
        statement="How can we improve customer satisfaction?",
        sub_goals=["sub_goal_1", "sub_goal_2"],
        status=GoalStatus.ACTIVE,
        created_at=datetime.utcnow(), 
        updated_at=datetime.utcnow()
    )
    goal_decomposition.decompose_goal.return_value = mock_goal
    
    # Mock reasoning engine
    mock_chain = ReasoningChain(
        id="chain_1",
        environment_id=env.id,
        goal_id="goal_1",
        query="How can we improve customer satisfaction?",
        steps=[],
        status="completed",
        created_at=datetime.utcnow(), 
        updated_at=datetime.utcnow()
    )
    reasoning_engine.reason.return_value = mock_chain
    
    # Mock deliberation service
    mock_deliberation = Deliberation(
        id="delib_1",
        environment_id=env.id,
        reasoning_chain_id="chain_1",
        alternatives=[{"id": "alt_1"}],
        chosen_alternative={"id": "alt_1", "description": "Best alternative"},
        rationale="This alternative has the highest score",
        confidence=0.85,
        status="completed",
        created_at=datetime.utcnow(), 
        updated_at=datetime.utcnow()
    )
    deliberation_service.deliberate.return_value = mock_deliberation
    
    # Mock simulation agent for alternatives
    simulation_agent.simulate.side_effect = [
        {"description": "Alternative 1", "strategy": {"action": "A"}, "expected_outcome": {"success": True}, "risk": 0.2, "confidence": 0.8},
        {"description": "Alternative 2", "strategy": {"action": "B"}, "expected_outcome": {"success": False}, "risk": 0.6, "confidence": 0.4},
        {"description": "Alternative 3", "strategy": {"action": "C"}, "expected_outcome": {"success": True}, "risk": 0.3, "confidence": 0.7}
    ]
    
    # Mock learning agent
    learning_agent.learn_from_reasoning.return_value = {"status": "learned", "patterns": ["pattern_1"]}
    
    # Mock prediction agent for conclusion
    prediction_agent.predict_outcome.return_value = {"conclusion": "Implement customer feedback system"}
    
    # Create orchestrator with mocks
    orchestrator = ReasoningOrchestrator(
        goal_decomposition_service=goal_decomposition,
        reasoning_engine=reasoning_engine,
        deliberation_service=deliberation_service,
        knowledge_agent=knowledge_agent,
        prediction_agent=prediction_agent,
        simulation_agent=simulation_agent,
        learning_agent=learning_agent
    )
    
    # Execute reasoning
    result = await orchestrator.reason_about_goal(
        context=context,
        goal_statement="How can we improve customer satisfaction?",
        context_data={"department": "support"}
    )
    
    # Assertions
    assert result["status"] == "completed"
    assert "goal" in result
    assert "reasoning_chain" in result
    assert "deliberation" in result
    assert "learning" in result
    assert "conclusion" in result
    
    # Verify goal was decomposed
    goal = result["goal"]
    assert goal.statement == "How can we improve customer satisfaction?"
    assert len(goal.sub_goals) == 2
    
    # Verify reasoning chain
    chain = result["reasoning_chain"]
    assert chain.id == "chain_1"
    assert chain.status == "completed"
    
    # Verify deliberation
    deliberation = result["deliberation"]
    assert deliberation.chosen_alternative["id"] == "alt_1"
    assert deliberation.confidence == 0.85
    
    # Verify learning
    learning = result["learning"]
    assert learning["status"] == "learned"
    
    # Verify conclusion
    assert result["conclusion"] == "Implement customer feedback system"
    
    print("✅ General Reasoning test passed")
