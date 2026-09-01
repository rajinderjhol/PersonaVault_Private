from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from app.api.v2.models.environment import Environment
from app.api.v2.services.crystallization_service import CrystallizationService
from app.api.v2.dependencies import require_authority
from app.api.v2.services.environment_service import environment_service
from app.services.memory_service import MemoryService # Corrected import

router = APIRouter(prefix="/v2/environments/{env_id}/crystallize", tags=["v2-crystallization"])

# Placeholder factory for CrystallizationService
def get_crystallization_service():
    from app.repositories.sqlalchemy.memory import SQLMemoryRepository
    from app.repositories.faiss.vector import FAISSSemanticRepository
    # This is a bit hacky, but consistent with the existing patterns in the codebase
    mem_repo = SQLMemoryRepository(db=None) 
    vec_repo = FAISSSemanticRepository()
    memory_service = MemoryService(memory_repo=mem_repo, vector_repo=vec_repo)
    return CrystallizationService(memory_service=memory_service)

@router.post("/")
async def crystallize_pattern(
    env_id: str,
    pattern_data: Dict[str, Any],
    env: Environment = Depends(lambda env_id: require_authority(env_id, "create_pattern")),
    crystallization_service: CrystallizationService = Depends(get_crystallization_service)
):
    """Crystallize a new pattern from a learning experience."""
    return await crystallization_service.crystallize_pattern(env, pattern_data)

@router.get("/")
async def get_patterns(
    env_id: str,
    query: str,
    limit: int = 10,
    env: Environment = Depends(lambda env_id: require_authority(env_id, "view_patterns")),
    crystallization_service: CrystallizationService = Depends(get_crystallization_service)
):
    """Retrieve crystallized patterns from the environment."""
    return await crystallization_service.retrieve_crystallized_patterns(env, query, limit)
