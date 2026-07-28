"""
Decision Timeline and Replay API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.db.session import get_db
from app.core.dependencies import require_admin
from app.services.learning.timeline_service import TimelineService
from app.services.learning.replay_service import ReplayService
from app.models.learning.behaviour_event import BehaviourEvent
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/timeline", tags=["timeline"])

@router.get("/{event_id}")
async def get_timeline(
    event_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get decision timeline for an event."""
    # Check if event exists
    stmt = select(BehaviourEvent).where(BehaviourEvent.id == event_id)
    result = await db.execute(stmt)
    event = result.scalars().first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    service = TimelineService(lambda: db)
    timeline = await service.get_timeline(event_id)
    
    if not timeline:
        # Build timeline if not exists
        timeline = await service.build_timeline(event)
    
    return {
        "event_id": event_id,
        "event_type": event.event_type,
        "decision": event.decision,
        "timeline": timeline
    }

@router.post("/build/{event_id}")
async def build_timeline(
    event_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Build a new timeline for an event."""
    stmt = select(BehaviourEvent).where(BehaviourEvent.id == event_id)
    result = await db.execute(stmt)
    event = result.scalars().first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    service = TimelineService(lambda: db)
    timeline = await service.build_timeline(event)
    
    return {
        "event_id": event_id,
        "timeline": timeline
    }

@router.get("/replay/{event_id}")
async def replay_decision(
    event_id: int,
    target_time: Optional[str] = Query(None, description="ISO timestamp to replay at"),
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Replay a decision at a specific point in time."""
    stmt = select(BehaviourEvent).where(BehaviourEvent.id == event_id)
    result = await db.execute(stmt)
    event = result.scalars().first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    target_dt = None
    if target_time:
        try:
            target_dt = datetime.fromisoformat(target_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format")
    
    service = ReplayService(lambda: db)
    result = await service.replay_decision(event_id, target_dt)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@router.get("/compare/{event_id_1}/{event_id_2}")
async def compare_decisions(
    event_id_1: int,
    event_id_2: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Compare two decisions."""
    service = ReplayService(lambda: db)
    result = await service.compare_decisions(event_id_1, event_id_2)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@router.get("/trends/{event_type}")
async def get_trends(
    event_type: str,
    days: int = Query(30, description="Number of days to analyze"),
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get decision trends for an event type."""
    service = ReplayService(lambda: db)
    result = await service.get_trend_analysis(event_type, days)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result
