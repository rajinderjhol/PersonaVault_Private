"""
MCP Connectors API - Calendar and Device management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from app.mcp.connectors.calendar_connector import CalendarConnector
from app.mcp.connectors.device_connector import DeviceConnector
from app.mcp.device_registry import DeviceType, DeviceCapability, DeviceTrustLevel

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp-connectors"])

# --- Request/Response Models ---

class CalendarEventCreate(BaseModel):
    summary: str
    description: str = ""
    start_time: str
    end_time: str
    timezone: str = "UTC"
    attendees: List[str] = []
    calendar_id: str = "primary"

class CalendarEventUpdate(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: Optional[str] = None
    attendees: Optional[List[str]] = None

class DeviceRegisterRequest(BaseModel):
    device_type: str  # iot, robot, medical, camera, edge, enterprise, smart_home, wearable, network
    device_name: str
    capabilities: List[str]  # sensor, actuator, camera, network, medical, enterprise, storage, compute
    config: dict = {}
    trust_level: str = "medium"  # full, high, medium, low, untrusted
    metadata: dict = {}

class DeviceActionRequest(BaseModel):
    action: str
    params: dict = {}

class ScheduleDecisionRequest(BaseModel):
    decision_id: str
    scheduled_time: str
    timezone: str = "UTC"
    attendees: List[str] = []
    action_required: str = "Review"

# --- Calendar Endpoints ---

@router.get("/calendar/calendars")
async def get_calendars(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of available calendars."""
    connector = CalendarConnector({})
    return await connector.get_calendars()


@router.post("/calendar/events")
async def create_calendar_event(
    event: CalendarEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a calendar event."""
    connector = CalendarConnector({})
    return await connector.create_event(event.dict())


@router.get("/calendar/events")
async def get_calendar_events(
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get calendar events."""
    connector = CalendarConnector({})
    return await connector.get_events(time_min, time_max)


@router.patch("/calendar/events/{event_id}")
async def update_calendar_event(
    event_id: str,
    updates: CalendarEventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a calendar event."""
    connector = CalendarConnector({})
    return await connector.update_event(event_id, updates.dict(exclude_none=True))


@router.delete("/calendar/events/{event_id}")
async def delete_calendar_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a calendar event."""
    connector = CalendarConnector({})
    return await connector.delete_event(event_id)


@router.post("/calendar/schedule-decision")
async def schedule_decision(
    request: ScheduleDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Schedule a decision review."""
    connector = CalendarConnector({})
    return await connector.schedule_decision(request.dict())


@router.get("/calendar/available-slots")
async def find_available_slots(
    duration_minutes: int = Query(60, ge=15, le=480),
    days_ahead: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Find available time slots."""
    connector = CalendarConnector({})
    return await connector.find_available_slots(duration_minutes, days_ahead)


# --- Device Endpoints ---

@router.post("/devices/register")
async def register_device(
    request: DeviceRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Register a new device."""
    connector = DeviceConnector({}, db)
    return await connector.register_new_device(
        device_type=request.device_type,
        device_name=request.device_name,
        capabilities=request.capabilities,
        config=request.config,
        user_id=str(current_user.id),
        trust_level=request.trust_level
    )


@router.get("/devices")
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all devices for the current user."""
    connector = DeviceConnector({}, db)
    return await connector.list_devices(str(current_user.id))


@router.get("/devices/{device_id}")
async def get_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get device details."""
    connector = DeviceConnector({}, db)
    return await connector.get_device_status(device_id)


@router.post("/devices/{device_id}/action")
async def execute_device_action(
    device_id: str,
    request: DeviceActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute an action on a device."""
    connector = DeviceConnector({}, db)
    return await connector.control_device(device_id, request.action, request.params)


@router.patch("/devices/{device_id}/trust")
async def update_device_trust(
    device_id: str,
    trust_level: str = Query(..., regex="^(full|high|medium|low|untrusted)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update device trust level."""
    connector = DeviceConnector({}, db)
    return await connector.set_trust_level(device_id, trust_level)


@router.get("/devices/{device_id}/telemetry")
async def get_device_telemetry(
    device_id: str,
    time_range: str = Query("1h", regex="^(1h|6h|24h|7d)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get device telemetry data."""
    connector = DeviceConnector({}, db)
    return await connector.get_telemetry(device_id, time_range)


@router.delete("/devices/{device_id}")
async def revoke_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke a device."""
    connector = DeviceConnector({}, db)
    return await connector.revoke_device(device_id)


@router.get("/devices/types")
async def get_device_types(
    current_user: User = Depends(get_current_user)
):
    """Get supported device types."""
    return {
        "device_types": [
            {"type": "iot", "description": "IoT devices (sensors, actuators, etc.)"},
            {"type": "robot", "description": "Robotic devices"},
            {"type": "medical", "description": "Medical devices (patient monitors, etc.)"},
            {"type": "camera", "description": "Camera devices (CCTV, doorbells, etc.)"},
            {"type": "edge", "description": "Edge computing devices"},
            {"type": "enterprise", "description": "Enterprise systems (Salesforce, SAP, etc.)"},
            {"type": "smart_home", "description": "Smart home devices"},
            {"type": "wearable", "description": "Wearable devices"},
            {"type": "network", "description": "Network devices"}
        ],
        "capabilities": [
            {"capability": "sensor", "description": "Data collection"},
            {"capability": "actuator", "description": "Physical action"},
            {"capability": "camera", "description": "Visual input"},
            {"capability": "network", "description": "Network monitoring"},
            {"capability": "medical", "description": "Medical data"},
            {"capability": "enterprise", "description": "Enterprise integration"},
            {"capability": "storage", "description": "Storage devices"},
            {"capability": "compute", "description": "Edge compute"}
        ]
    }


# --- Device Admin Endpoints ---

@router.get("/admin/devices/all")
async def list_all_devices(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all devices (admin only)."""
    from app.models.device import Device
    from sqlalchemy import select
    
    result = await db.execute(
        select(Device).offset(skip).limit(limit)
    )
    devices = result.scalars().all()
    return {
        "devices": [d.to_dict() for d in devices],
        "total": len(devices)
    }


@router.get("/admin/devices/stats")
async def get_device_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get device statistics (admin only)."""
    from app.models.device import Device
    from sqlalchemy import select, func
    
    result = await db.execute(
        select(
            Device.device_type,
            func.count().label("count"),
            Device.status
        ).group_by(Device.device_type, Device.status)
    )
    stats = result.all()
    
    # Format stats
    type_stats = {}
    for row in stats:
        device_type = row[0].value if hasattr(row[0], 'value') else str(row[0])
        status = row[2].value if hasattr(row[2], 'value') else str(row[2])
        if device_type not in type_stats:
            type_stats[device_type] = {"total": 0, "statuses": {}}
        type_stats[device_type]["total"] += row[1]
        type_stats[device_type]["statuses"][status] = row[1]
    
    return {
        "total_devices": sum(s["total"] for s in type_stats.values()),
        "by_type": type_stats
    }
