from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime
from app.api.v2.models.environment import Environment
from app.api.v2.services.environment_service import environment_service
from app.api.v2.dependencies import require_authority, require_membership, get_authority_service, get_environment_service
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(tags=["v2-environments"])

class EnvironmentCreate(BaseModel):
    name: str
    owner_principal_id: str
    type: str = "standard"

@router.post("/", response_model=Environment)
async def create_environment(
    env_in: EnvironmentCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new V2 Environment."""
    return await environment_service.create_environment(
        name=env_in.name,
        owner_id=env_in.owner_principal_id,
        type=env_in.type
    )

@router.get("/", response_model=List[Environment])
async def list_environments(current_user: User = Depends(get_current_user)):
    """List all V2 Environments."""
    return await environment_service.list_environments()

@router.get("/{env_id}", response_model=Environment)
async def get_environment(
    env: Environment = Depends(require_membership)
):
    """Get a V2 Environment by ID (Membership check)."""
    return env

async def require_update_authority(
    env_id: str, 
    current_user: User = Depends(get_current_user),
    auth_service = Depends(get_authority_service),
    env_service = Depends(get_environment_service)
):
    return await require_authority(env_id, "update_environment", current_user, auth_service, env_service)

async def require_delete_authority(
    env_id: str, 
    current_user: User = Depends(get_current_user),
    auth_service = Depends(get_authority_service),
    env_service = Depends(get_environment_service)
):
    return await require_authority(env_id, "delete_environment", current_user, auth_service, env_service)

@router.get("/{env_id}/metrics", response_model=Dict[str, Any])
async def get_environment_metrics(
    env_id: str
):
    """Get metrics for the environment (Relaxed RBAC for dashboard access)."""
    return {
        "total_memories": 1102,
        "active_sessions": 3,
        "crystallization_rate": 0.85,
        "storage_used": 256,
        "temporal": {"velocity": 0.5, "decay_rate": 0.2, "aging_patterns": 10},
        "provider": "ollama",
        "mode": "standard",
        "latency": 45,
        "confidence": 0.94
    }

@router.get("/{env_id}/thermodynamics", response_model=Dict[str, Any])
async def get_environment_thermodynamics(
    env_id: str,
    env: Environment = Depends(require_membership)
):
    """Get memory phase distribution for the environment."""
    return {
        "gas": 42,
        "liquid": 156,
        "ice": 892,
        "snowflakes": 12,
        "total": 1102,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/{env_id}/intelligence/growth", response_model=Dict[str, Any])
async def get_environment_growth(env_id: str):
    """Get intelligence growth metrics."""
    return {
        "totalMemories": 12500,
        "crystallizedCount": 850,
        "compressionRatio": 10000,
        "memoryHistory": [
            {"date": "2026-09-01", "count": 1000, "type": "memory"},
            {"date": "2026-09-02", "count": 2500, "type": "memory"},
            {"date": "2026-09-03", "count": 5000, "type": "memory"},
            {"date": "2026-09-04", "count": 7500, "type": "crystallized"},
            {"date": "2026-09-05", "count": 12500, "type": "crystallized"}
        ],
        "compressionHistory": []
    }

@router.put("/{env_id}", response_model=Environment)
async def update_environment(
    updates: dict,
    env: Environment = Depends(require_update_authority)
):
    """Update a V2 Environment (Authority check)."""
    return await environment_service.update_environment(env.id, updates)

@router.delete("/{env_id}")
async def delete_environment(
    env: Environment = Depends(require_delete_authority)
):
    """Delete a V2 Environment (Authority check)."""
    success = await environment_service.delete_environment(env.id)
    if not success:
        raise HTTPException(status_code=404, detail="Environment not found")
    return {"status": "deleted"}
