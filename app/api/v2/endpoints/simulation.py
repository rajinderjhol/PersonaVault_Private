from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
from app.api.v2.models.environment import Environment
from app.api.v2.dependencies import require_authority, get_simulation_service
from app.api.v2.services.simulation_service import SimulationService

router = APIRouter(prefix="/{env_id}/simulations", tags=["v2-simulations"])

@router.post("/predict")
async def predict(
    env_id: str,
    scenario: Dict[str, Any],
    env: Environment = Depends(lambda env_id: require_authority(env_id, "predict")),
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """Predict the outcome of a scenario within the environment."""
    return await simulation_service.prediction_service.predict_outcome(env, scenario)

@router.post("/run")
async def run_simulation(
    env_id: str,
    scenario: Dict[str, Any],
    env: Environment = Depends(lambda env_id: require_authority(env_id, "simulate")),
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """Run a sandbox simulation with no side effects."""
    return await simulation_service.create_simulation(env, scenario)
