"""
Identity API Endpoints - User profiles, devices, permissions, trust
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.identity.identity_service import IdentityService
from app.models.identity import DeviceType, DeviceTrustLevel, PermissionLevel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])


class ProfileCreate(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None


class DeviceRegister(BaseModel):
    name: str
    device_type: DeviceType = DeviceType.WEB
    metadata: Optional[dict] = None


class PermissionGrant(BaseModel):
    action: str
    level: PermissionLevel
    expires_in_days: Optional[int] = None


class TrustEntityAdd(BaseModel):
    entity_type: str
    entity_id: str
    trust_level: float = 0.5
    reason: Optional[str] = None


# Profiles
@router.post("/profile")
async def create_profile(request: ProfileCreate):
    """Create a new user profile."""
    service = IdentityService()
    profile = await service.create_profile(
        username=request.username,
        email=request.email,
        full_name=request.full_name
    )
    return profile


@router.get("/profile/{user_id}")
async def get_profile(user_id: int):
    """Get a user profile."""
    service = IdentityService()
    profile = await service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@router.put("/profile/{user_id}")
async def update_profile(user_id: int, **kwargs):
    """Update a user profile."""
    service = IdentityService()
    profile = await service.update_profile(user_id, **kwargs)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


# Devices
@router.post("/device/{user_id}")
async def register_device(user_id: int, request: DeviceRegister):
    """Register a new device."""
    service = IdentityService()
    device = await service.register_device(
        user_id=user_id,
        name=request.name,
        device_type=request.device_type,
        metadata=request.metadata
    )
    return device


@router.get("/devices/{user_id}")
async def get_devices(user_id: int):
    """Get all devices for a user."""
    service = IdentityService()
    return await service.get_devices(user_id)


@router.put("/device/{user_id}/{device_id}/trust")
async def trust_device(
    user_id: int,
    device_id: str,
    trust_level: DeviceTrustLevel
):
    """Set trust level for a device."""
    service = IdentityService()
    device = await service.trust_device(device_id, user_id, trust_level)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


# Permissions
@router.post("/permission/{user_id}")
async def grant_permission(user_id: int, request: PermissionGrant):
    """Grant a permission to a user."""
    service = IdentityService()
    permission = await service.grant_permission(
        user_id=user_id,
        action=request.action,
        level=request.level,
        expires_in_days=request.expires_in_days
    )
    return permission


@router.get("/permissions/{user_id}")
async def get_permissions(user_id: int):
    """Get all permissions for a user."""
    service = IdentityService()
    return await service.get_permissions(user_id)


@router.delete("/permission/{user_id}/{action}")
async def revoke_permission(user_id: int, action: str):
    """Revoke a permission."""
    service = IdentityService()
    result = await service.revoke_permission(user_id, action)
    return {"success": result}


@router.get("/permission/{user_id}/check")
async def check_permission(
    user_id: int,
    action: str = Query(...),
    level: PermissionLevel = Query(...)
):
    """Check if a user has a permission."""
    service = IdentityService()
    has_permission = await service.check_permission(user_id, action, level)
    return {
        "user_id": user_id,
        "action": action,
        "required_level": level,
        "has_permission": has_permission
    }


# Trust
@router.post("/trust/{user_id}")
async def add_trusted_entity(user_id: int, request: TrustEntityAdd):
    """Add a trusted entity."""
    service = IdentityService()
    entity = await service.add_trusted_entity(
        user_id=user_id,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        trust_level=request.trust_level,
        reason=request.reason
    )
    return entity


@router.get("/trust/{user_id}")
async def get_trusted_entities(user_id: int):
    """Get all trusted entities."""
    service = IdentityService()
    return await service.get_trusted_entities(user_id)


# Sync
@router.post("/sync/{user_id}")
async def sync_devices(
    user_id: int,
    from_device: str = Query(...),
    to_device: str = Query(...)
):
    """Sync context between devices."""
    service = IdentityService()
    return await service.sync_context(user_id, from_device, to_device)


@router.get("/sync/{user_id}/{device_id}")
async def get_sync_state(user_id: int, device_id: str):
    """Get sync state for a device."""
    service = IdentityService()
    state = await service.get_sync_state(user_id, device_id)
    if not state:
        raise HTTPException(status_code=404, detail="Sync state not found")
    return state


# Statistics
@router.get("/statistics")
async def get_statistics():
    """Get identity layer statistics."""
    service = IdentityService()
    return await service.get_statistics()
