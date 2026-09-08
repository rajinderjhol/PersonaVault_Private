from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.trust_policy import TrustPolicy
from app.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/trust-policies", tags=["Trust Policies"])

# Pydantic models
class TrustPolicyResponse(BaseModel):
    id: str
    layer: str
    min_trust_threshold: float
    max_trust_threshold: Optional[float]
    is_enforced: bool
    action_on_violation: str
    notification_enabled: bool
    created_at: datetime
    updated_at: datetime

class TrustPolicyUpdateRequest(BaseModel):
    min_trust_threshold: Optional[float] = Field(None, ge=0, le=1)
    max_trust_threshold: Optional[float] = Field(None, ge=0, le=1)
    is_enforced: Optional[bool] = None
    action_on_violation: Optional[str] = Field(None, pattern="^(block|warn|quarantine)$")
    notification_enabled: Optional[bool] = None

class TrustPolicyCreateRequest(BaseModel):
    layer: str = Field(..., pattern="^(gas|liquid|ice|crystallized)$")
    min_trust_threshold: float = Field(0.40, ge=0, le=1)
    max_trust_threshold: Optional[float] = Field(None, ge=0, le=1)
    action_on_violation: str = Field("block", pattern="^(block|warn|quarantine)$")
    notification_enabled: bool = True

# Helper function
def model_to_response(model: TrustPolicy) -> TrustPolicyResponse:
    return TrustPolicyResponse(
        id=model.id,
        layer=model.layer,
        min_trust_threshold=model.min_trust_threshold,
        max_trust_threshold=model.max_trust_threshold,
        is_enforced=model.is_enforced,
        action_on_violation=model.action_on_violation,
        notification_enabled=model.notification_enabled,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )

# API Endpoints

@router.get("/defaults", response_model=Dict[str, Dict])
async def get_default_policies():
    """Get recommended trust policy thresholds for each layer."""
    return {
        "gas": {"min": 0.20, "max": 0.50, "default": 0.35, "action": "warn"},
        "liquid": {"min": 0.40, "max": 0.70, "default": 0.55, "action": "quarantine"},
        "ice": {"min": 0.70, "max": 0.95, "default": 0.85, "action": "block"},
        "crystallized": {"min": 0.90, "max": 1.0, "default": 0.98, "action": "block"}
    }

@router.get("/", response_model=List[TrustPolicyResponse])
async def list_policies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all trust policies for the current user."""
    stmt = select(TrustPolicy).where(
        TrustPolicy.user_id == current_user.id
    )
    result = await db.execute(stmt)
    policies = result.scalars().all()
    return [model_to_response(p) for p in policies]

@router.get("/{layer}", response_model=TrustPolicyResponse)
async def get_policy(
    layer: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific trust policy by layer."""
    stmt = select(TrustPolicy).where(
        TrustPolicy.layer == layer,
        TrustPolicy.user_id == current_user.id
    )
    result = await db.execute(stmt)
    policy = result.scalars().first()
    
    if not policy:
        raise HTTPException(status_code=404, detail=f"No policy found for layer: {layer}")
    return model_to_response(policy)

@router.post("/", response_model=TrustPolicyResponse, status_code=201)
async def create_policy(
    request: TrustPolicyCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new trust policy for a layer."""
    # Check if policy already exists
    stmt = select(TrustPolicy).where(
        TrustPolicy.layer == request.layer,
        TrustPolicy.user_id == current_user.id
    )
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail=f"Policy for layer {request.layer} already exists")
    
    policy = TrustPolicy(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        layer=request.layer,
        min_trust_threshold=request.min_trust_threshold,
        max_trust_threshold=request.max_trust_threshold,
        action_on_violation=request.action_on_violation,
        notification_enabled=request.notification_enabled,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return model_to_response(policy)

@router.patch("/{layer}", response_model=TrustPolicyResponse)
async def update_policy(
    layer: str,
    request: TrustPolicyUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing trust policy."""
    stmt = select(TrustPolicy).where(
        TrustPolicy.layer == layer,
        TrustPolicy.user_id == current_user.id
    )
    result = await db.execute(stmt)
    policy = result.scalars().first()
    
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy for layer {layer} not found")
    
    if request.min_trust_threshold is not None:
        policy.min_trust_threshold = request.min_trust_threshold
    if request.max_trust_threshold is not None:
        policy.max_trust_threshold = request.max_trust_threshold
    if request.is_enforced is not None:
        policy.is_enforced = request.is_enforced
    if request.action_on_violation is not None:
        policy.action_on_violation = request.action_on_violation
    if request.notification_enabled is not None:
        policy.notification_enabled = request.notification_enabled
        
    policy.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(policy)
    return model_to_response(policy)

@router.delete("/{layer}", status_code=204)
async def delete_policy(
    layer: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a trust policy."""
    stmt = select(TrustPolicy).where(
        TrustPolicy.layer == layer,
        TrustPolicy.user_id == current_user.id
    )
    result = await db.execute(stmt)
    policy = result.scalars().first()
    
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy for layer {layer} not found")
    
    await db.delete(policy)
    await db.commit()
    return None
