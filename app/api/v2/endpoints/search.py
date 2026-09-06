from fastapi import APIRouter, Depends, Request
from typing import Dict, Any, List
from app.api.v2.models.environment import Environment
from app.api.v2.dependencies import require_authority
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/v2/environments/{env_id}/search", tags=["v2-search"])

def get_memory_service(request: Request):
    return request.app.state.memory_service

@router.post("")
async def search(
    env_id: str,
    query: Dict[str, Any],
    env: Environment = Depends(lambda env_id: require_authority(env_id, "read")),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Search memories within the environment."""
    search_query = query.get("query", "")
    limit = query.get("limit", 20)
    return await memory_service.search_memories(env, search_query, limit=limit)
