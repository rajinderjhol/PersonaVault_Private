from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.api.v2.models.hypothesis import Hypothesis
from app.api.v2.models.experiment import Experiment
from app.api.v2.dependencies import require_membership
from app.api.v2.services.hypothesis_service import HypothesisService
from app.api.v2.services.experiment_service import ExperimentService

router = APIRouter(prefix="/experiments", tags=["experiments"])

# Placeholder services - TODO: Wire up to actual DI
hypothesis_service = HypothesisService()
experiment_service = ExperimentService()

@router.post("/hypothesis", response_model=Hypothesis)
async def create_hypothesis(
    env_id: str,
    data: Dict[str, Any],
    environment = Depends(require_membership)
):
    """Create a new hypothesis for an environment."""
    return await hypothesis_service.create_hypothesis(data)

@router.post("/run", response_model=Experiment)
async def run_experiment(
    env_id: str,
    hypothesis_id: str,
    environment = Depends(require_membership)
):
    """Run an experiment based on a hypothesis."""
    # TODO: Pass hypothesis_id to service
    return await experiment_service.run_experiment(hypothesis_id)
