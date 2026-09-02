import pytest
from unittest.mock import AsyncMock
from app.api.v2.services.experiment_coordinator import ExperimentCoordinator
from app.swarm.context import AgentEnvironmentContext
from app.api.v2.models.environment import Environment, EnvironmentStatus
from app.api.v2.models.knowledge_gap import KnowledgeGap
from app.api.v2.models.hypothesis import Hypothesis, HypothesisStatus
from app.api.v2.models.experiment import Experiment, ExperimentStatus
from app.api.v2.models.experiment_observation import ExperimentObservation
import uuid
from datetime import datetime

# Mocks
class MockHypothesisService:
    async def create_hypothesis(self, **kwargs):
        return Hypothesis(
            id="hyp-1", environment_id="env-1", statement="test", premise="test",
            expected_outcome={}, testability_criteria=[], priority=1,
            status=HypothesisStatus.PROPOSED, confidence=0.5,
            created_at=datetime.utcnow(), updated_at=datetime.utcnow()
        )
    async def get_hypothesis(self, hypothesis_id):
        return None

class MockExperimentService:
    async def create_experiment(self, **kwargs):
        return Experiment(
            id="exp-1", environment_id="env-1", hypothesis_id="hyp-1",
            description="test", intervention={}, control={}, metrics=[],
            status=ExperimentStatus.PLANNED, created_at=datetime.utcnow(), updated_at=datetime.utcnow()
        )

class MockExperimentBridge:
    async def process_experiment_results(self, **kwargs):
        return ExperimentObservation(
            id="obs-1", experiment_id="exp-1", observed_at=datetime.utcnow(),
            metric_name="test", value=1.0, expected_value=1.0, deviation=0.0, significance=1.0
        )
    async def learn_from_experiment(self, **kwargs):
        return {"learned": True}

class MockKnowledgeAgent:
    async def identify_gaps(self, **kwargs):
        return [KnowledgeGap(id="gap-1", question="test?", importance=0.8, evidence_needed=[], context={})]
    async def generate_hypothesis(self, **kwargs):
        return {"statement": "test", "premise": "test", "expected_outcome": {}, "testability_criteria": []}

class MockPredictionAgent:
    async def predict(self, **kwargs):
        return {}

class MockSimulationAgent:
    async def design_experiment(self, **kwargs):
        return {"description": "test", "intervention": {}, "control": {}, "metrics": []}
    async def simulate(self, **kwargs):
        return {}

@pytest.mark.asyncio
async def test_experimentation_cycle():
    """
    Test the full experimentation cycle:
    Knowledge Gap → Hypothesis → Experiment → Observation → Learning
    """
    # Setup
    env = Environment(
        id="env-1", 
        type="test-type", 
        name="test", 
        description="test", 
        owner_principal_id="user-1",
        status=EnvironmentStatus.ACTIVE,
        created_at=datetime.utcnow(), 
        updated_at=datetime.utcnow()
    )
    
    # Mock services
    context = AgentEnvironmentContext(
        environment=env,
        memory_service=AsyncMock(),
        authority_service=AsyncMock(),
        crystallization_service=AsyncMock(),
        prediction_service=AsyncMock(),
        simulation_service=AsyncMock()
    )
    
    # Create coordinator
    coordinator = ExperimentCoordinator(
        hypothesis_service=MockHypothesisService(),
        experiment_service=MockExperimentService(),
        experiment_bridge=MockExperimentBridge(),
        knowledge_agent=MockKnowledgeAgent(),
        prediction_agent=MockPredictionAgent(),
        simulation_agent=MockSimulationAgent()
    )
    
    # Run the cycle
    results = await coordinator.run_experimentation_cycle(context)
    
    # Assert
    assert len(results) > 0
    assert results[0]["gap"] == "gap-1"
    assert results[0]["hypothesis"] == "hyp-1"
    assert results[0]["experiment"] == "exp-1"
    assert results[0]["observation"] == "obs-1"
    assert results[0]["learning"] == {"learned": True}
    
    print("✅ Experimentation cycle test passed")
