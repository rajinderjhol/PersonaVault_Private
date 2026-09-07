import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.api.v2.dependencies import require_authority, require_membership
from app.api.v2.models.environment import Environment
from app.services.crystallization.crystallization_service import crystallization_service
from app.core.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

class CrystallizeRequest(BaseModel):
    pattern: Dict[str, Any]
    source: Optional[str] = "chat_reasoning"

@router.post("/{env_id}/crystallize")
async def crystallize_pattern(
    env_id: str,
    request: CrystallizeRequest,
    current_user: User = Depends(get_current_user)
):
    """Crystallize a reasoning pattern into Ice memory."""
    result = await crystallization_service.crystallize(
        env_id=env_id,
        pattern=request.pattern,
        source=request.source
    )
    return result

@router.get("/{env_id}/crystallize")
async def get_patterns(
    env_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all crystallized patterns for an environment."""
    patterns = await crystallization_service.get_patterns(env_id)
    return {"patterns": patterns, "count": len(patterns)}

@router.get("/{env_id}/crystallize/{pattern_id}")
async def get_pattern(
    env_id: str,
    pattern_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific crystallized pattern by ID."""
    pattern = await crystallization_service.get_pattern(pattern_id)
    if pattern:
        return pattern
    return {"error": "Pattern not found", "pattern_id": pattern_id}
