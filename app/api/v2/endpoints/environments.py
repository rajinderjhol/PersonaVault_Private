from fastapi import APIRouter, HTTPException
from typing import List
from app.api.v2.models.environment import Environment
from app.api.v2.services.environment_service import environment_service
from pydantic import BaseModel

router = APIRouter(prefix="/v2/environments", tags=["v2-environments"])

class EnvironmentCreate(BaseModel):
    name: str
    owner_principal_id: str
    type: str = "standard"

@router.post("/", response_model=Environment)
async def create_environment(env_in: EnvironmentCreate):
    """Create a new V2 Environment."""
    return await environment_service.create_environment(
        name=env_in.name,
        owner_id=env_in.owner_principal_id,
        type=env_in.type
    )

@router.get("/", response_model=List[Environment])
async def list_environments():
    """List all V2 Environments."""
    return await environment_service.list_environments()

@router.get("/{env_id}", response_model=Environment)
async def get_environment(env_id: str):
    """Get a V2 Environment by ID."""
    env = await environment_service.get_environment(env_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return env
