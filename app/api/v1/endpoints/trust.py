"""
Device Trust API endpoints.
"""
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter(prefix="/trust", tags=["trust"])

class TrustDevice(BaseModel):
    id: str
    name: str
    trust_score: float

class SyncStatus(BaseModel):
    status: str
    last_sync: datetime

@router.get("/devices", response_model=List[TrustDevice])
async def list_devices(admin_id: int = Depends(get_current_user)):
    """List trusted devices."""
    return [
        {"id": "dev-1", "name": "Work Laptop", "trust_score": 0.95},
        {"id": "dev-2", "name": "Personal Phone", "trust_score": 0.88},
    ]

@router.get("/sync", response_model=SyncStatus)
async def get_sync_status(admin_id: int = Depends(get_current_user)):
    """Get device sync status."""
    return {
        "status": "synchronized",
        "last_sync": datetime.utcnow()
    }
