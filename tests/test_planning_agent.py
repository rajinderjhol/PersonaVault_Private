"""
Tests for PlanningAgent - fixed semantic patterns issue.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
import sys
sys.path.insert(0, '/home/rajinderj8888/personavault/backend')

from app.services.planning_agent import PlanningAgent
from app.services.semantic_memory import SemanticMemory
from app.schemas.memory_schemas import RetrievalPlan, SemanticPattern

@pytest.fixture
def mock_semantic_memory():
    """Mock semantic memory for testing."""
    mock = MagicMock(spec=SemanticMemory)
    # Return actual SemanticPattern objects, not dicts
    mock.get_patterns.return_value = [
        SemanticPattern(
            pattern_type="query_refinement",
            trigger="test",
            correction="fixed",
            occurrence_count=3
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
    async def test_plan_returns_retrieval_plan(self, planning_agent):
        """Test that plan returns a RetrievalPlan."""
        plan = await planning_agent.plan(
            query="test query",
            context={"user_id": 1}
        )
        assert isinstance(plan, RetrievalPlan)
        assert hasattr(plan, 'needs_retrieval')
        assert hasattr(plan, 'semantic_queries')
        assert hasattr(plan, 'keyword_queries')
        assert hasattr(plan, 'graph_traversals')
        assert hasattr(plan, 'reasoning')
        assert hasattr(plan, 'complexity_score')
    
    @pytest.mark.asyncio
    async def test_plan_with_empty_query(self, planning_agent):
        """Test plan with empty query."""
        plan = await planning_agent.plan(
            query="",
            context={"user_id": 1}
        )
        assert isinstance(plan, RetrievalPlan)
    
    @pytest.mark.asyncio
    async def test_plan_uses_semantic_memory(self, planning_agent, mock_semantic_memory):
        """Test that plan uses semantic memory for patterns."""
        plan = await planning_agent.plan(
            query="test query",
            context={"user_id": 1}
        )
        assert isinstance(plan, RetrievalPlan)
        # Verify semantic memory was called
        mock_semantic_memory.get_patterns.assert_called()
    
    @pytest.mark.asyncio
    async def test_plan_with_complex_query(self, planning_agent):
        """Test plan with a complex, multi-part query."""
        plan = await planning_agent.plan(
            query="What is the status of the project and who is working on it?",
            context={"user_id": 1, "project_id": 123}
        )
        assert isinstance(plan, RetrievalPlan)
        # Should have higher complexity for multi-part query
        assert plan.complexity_score >= 0.3

if __name__ == "__main__":
    pytest.main(["-v", __file__])
