import pytest
from unittest.mock import MagicMock
from app.swarm.core.planner import PlannerAgent
from app.schemas.memory_schemas import RetrievalPlan

@pytest.mark.asyncio
async def test_create_plan_collects_instructions_without_modifying_query():
    # Setup
    mock_semantic_memory = MagicMock()
    # Mock patterns that trigger on "contract"
    mock_pattern = MagicMock()
    mock_pattern.trigger = "contract"
    mock_pattern.correction = "contract_response_template"
    mock_pattern.weight = 0.8
    mock_pattern.is_active = True
    
    # Correct async mocking
    async def get_patterns():
        return [mock_pattern]
    
    mock_semantic_memory.get_patterns = get_patterns

    planner = PlannerAgent(semantic_memory=mock_semantic_memory)
    
    query = "tell me about the contracts?"
    
    # Execute
    plan = await planner.create_plan(query)
    
    # Assert
    # Query should be original and unmodified
    assert plan.semantic_queries[0] == query
    
    # Instructions should contain the pattern correction
    assert "contract_response_template" in plan.instructions
    
    # Ensure instructions didn't leak into semantic query
    assert "[SYSTEM INSTRUCTION:" not in plan.semantic_queries[0]
