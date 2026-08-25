"""
Tests for PlanningAgent - updated for Auditable Traces.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
import sys
from app.swarm.core.planner import PlanningAgent
from app.services.semantic_memory import SemanticMemory
from app.schemas.memory_schemas import RetrievalPlan, SemanticPattern

@pytest.fixture
def mock_semantic_memory():
    """Mock semantic memory for testing."""
    mock = AsyncMock(spec=SemanticMemory)
    # Return actual SemanticPattern objects, not dicts
    mock.get_patterns.return_value = [
        SemanticPattern(
            pattern_type="query_refinement",
            trigger="test",
            correction="fixed",
            occurrence_count=3,
            is_active=True,
            weight=0.8
        )
    ]
    return mock

@pytest.fixture
def planning_agent(mock_semantic_memory):
    """Create a PlanningAgent instance with mocked dependencies."""
    return PlanningAgent(semantic_memory=mock_semantic_memory)

class TestPlanningAgent:
    """Test suite for PlanningAgent."""
    
    def test_init(self, mock_semantic_memory):
        """Test PlanningAgent initialization."""
        agent = PlanningAgent(semantic_memory=mock_semantic_memory)
        assert agent is not None
        assert agent.semantic_memory == mock_semantic_memory
    
    def test_init_requires_semantic_memory(self):
        """Test that PlanningAgent requires semantic_memory parameter."""
        with pytest.raises(TypeError):
            PlanningAgent()
    
    @pytest.mark.asyncio
    async def test_plan_returns_retrieval_plan_and_trace(self, planning_agent):
        """Test that plan returns a dict with plan and trace."""
        result = await planning_agent.plan(
            query="test query",
            context={"user_id": 1}
        )
        assert isinstance(result, dict)
        assert "plan" in result
        assert "trace" in result
        
        plan = result["plan"]
        assert isinstance(plan, RetrievalPlan)
        assert hasattr(plan, 'needs_retrieval')
        assert hasattr(plan, 'semantic_queries')
        assert hasattr(plan, 'reasoning')
        
        trace = result["trace"]
        assert trace["agent"] == "planner"
        assert trace["trace"]["decision"]["type"] == "create_retrieval_plan"
    
    @pytest.mark.asyncio
    async def test_plan_with_empty_query(self, planning_agent):
        """Test plan with empty query."""
        result = await planning_agent.plan(
            query="",
            context={"user_id": 1}
        )
        assert "plan" in result
        assert isinstance(result["plan"], RetrievalPlan)
    
    @pytest.mark.asyncio
    async def test_plan_uses_semantic_memory(self, planning_agent, mock_semantic_memory):
        """Test that plan uses semantic memory for patterns."""
        result = await planning_agent.plan(
            query="test query",
            context={"user_id": 1}
        )
        assert "plan" in result
        # Verify semantic memory was called
        mock_semantic_memory.get_patterns.assert_called()
    
    @pytest.mark.asyncio
    async def test_plan_with_complex_query(self, planning_agent):
        """Test plan with a complex, multi-part query."""
        result = await planning_agent.plan(
            query="What is the status of the project and who is working on it?",
            context={"user_id": 1, "project_id": 123}
        )
        assert "plan" in result
        plan = result["plan"]
        # Should have higher complexity for multi-part query
        assert plan.complexity_score >= 0.3

if __name__ == "__main__":
    pytest.main(["-v", __file__])
