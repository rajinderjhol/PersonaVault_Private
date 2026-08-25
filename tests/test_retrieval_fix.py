import pytest
from unittest.mock import MagicMock, AsyncMock
from app.swarm.core.planner import PlannerAgent
from app.schemas.memory_schemas import RetrievalPlan, SemanticPattern

@pytest.mark.asyncio
async def test_create_plan_collects_instructions_without_modifying_query():
    # Setup
    mock_semantic_memory = AsyncMock()
    # Mock patterns that trigger on "contract"
    mock_pattern = SemanticPattern(
        pattern_type="query_refinement",
        trigger="contract",
        correction="contract_response_template",
        weight=0.8,
        is_active=True
    )
    
    mock_semantic_memory.get_patterns.return_value = [mock_pattern]

    planner = PlannerAgent(semantic_memory=mock_semantic_memory)
    
    query = "tell me about the contracts?"
    
    # Execute
    result = await planner.create_plan(query)
    plan = result["plan"]
    trace = result["trace"]
    
    # Assert
    # Query should be original and unmodified
    assert plan.semantic_queries[0] == query
    
    # Instructions should contain the pattern correction in the TRACE, not the plan
    # Signals in trace should have the pattern match
    pattern_matches = [s for s in trace["trace"]["signals"] if s["type"] == "pattern_match"]
    assert len(pattern_matches) > 0
    assert pattern_matches[0]["value"]["correction"] == "contract_response_template"
    
    # Ensure instructions didn't leak into semantic query
    assert "[SYSTEM INSTRUCTION:" not in plan.semantic_queries[0]
