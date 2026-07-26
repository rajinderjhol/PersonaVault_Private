from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from app.db.session import get_db
from app.models import IoTDevice, IoTData
from app.api.v1.endpoints.auth import get_current_user_id
from datetime import datetime, timezone

router = APIRouter()

class DeviceCreate(BaseModel):
    device_name: str
    device_type: str
    device_id: str

class DataIngest(BaseModel):
    device_id: str
    data_type: str
    value: dict
    linked_memory_id: Optional[int] = None

@router.post("/register")
async def register_device(device: DeviceCreate, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    stmt = select(IoTDevice).where(IoTDevice.device_id == device.device_id)
    result = await db.execute(stmt)
    existing = result.scalars().first()

    if existing:
        raise HTTPException(status_code=400, detail="Device already registered")
    
    new_device = IoTDevice(user_id=user_id, **device.model_dump(), last_seen=datetime.now(timezone.utc))
    db.add(new_device)
    await db.commit()
    return {"status": "success", "device_id": new_device.id}

@router.post("/ingest")
async def ingest_data(payload: DataIngest, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    stmt = select(IoTDevice).where(IoTDevice.device_id == payload.device_id)
    result = await db.execute(stmt)
    device = result.scalars().first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    data_entry = IoTData(
        device_id=device.device_id,
        user_id=user_id,
        data_type=payload.data_type,
        value=payload.value,
        linked_memory_id=payload.linked_memory_id
    )
    device.last_seen = datetime.now(timezone.utc)
    db.add(data_entry)
    await db.commit()
    return {"status": "data_ingested"}