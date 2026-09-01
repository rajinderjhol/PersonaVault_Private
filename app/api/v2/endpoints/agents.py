from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.api.v2.models.environment import Environment
from app.api.v2.dependencies import require_membership
from app.swarm.orchestrator import get_orchestrator
from app.services.memory_service import MemoryService
from app.api.v2.services.authority_service import AuthorityService
from app.api.v2.services.crystallization_service import crystallization_service
from app.api.v2.services.prediction_service import PredictionService
from app.api.v2.services.simulation_service import SimulationService
from app.repositories.sqlalchemy.memory import SQLMemoryRepository
from app.repositories.faiss.vector import FAISSSemanticRepository

router = APIRouter(prefix="/v2/environments/{env_id}/agents", tags=["v2-agents"])

# Service Factory
def get_full_orchestrator():
    mem_repo = SQLMemoryRepository(db=None) 
    vec_repo = FAISSSemanticRepository()
    memory_service = MemoryService(memory_repo=mem_repo, vector_repo=vec_repo)
    authority_service = AuthorityService(membership_service=None) # Mock membership
    crystallization_service = crystallization_service
    prediction_service = PredictionService(memory_service, crystallization_service)
    simulation_service = SimulationService(prediction_service)
    
    return get_orchestrator(
        db_session=None,
        blackboard=None,
        memory_service=memory_service,
        authority_service=authority_service,
        crystallization_service=crystallization_service,
        prediction_service=prediction_service,
        simulation_service=simulation_service
    )

@router.post("/chat")
async def chat_with_agent(
    env_id: str,
    query: str,
    env: Environment = Depends(lambda env_id: require_membership(env_id)),
    orchestrator = Depends(get_full_orchestrator)
):
    """Chat with an agent within the context of a specific environment."""
    context = {"environment_id": env_id, "user_id": 1}
    return await orchestrator.process_query(query, user_id=1, provider="ollama")
