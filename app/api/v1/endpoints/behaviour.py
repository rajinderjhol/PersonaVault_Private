"""
Behaviour Event API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.db.session import get_db
from app.core.dependencies import require_admin
from app.models.learning.behaviour_event import BehaviourEvent
from app.services.governance.audit_service_async import AsyncAuditService

router = APIRouter(prefix="/behaviour", tags=["behaviour"])

class BehaviourEventCreate(BaseModel):
    user_id: int
    event_type: str
    actor: str
    artefact: str
    decision: str
    reason: str
    outcome: str
    confidence: float
    extra_data: Optional[Dict[str, Any]] = {}

@router.post("/event")
async def create_behaviour_event(
    event_data: BehaviourEventCreate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new behaviour event."""
    try:
        event = BehaviourEvent(
            user_id=event_data.user_id,
            event_type=event_data.event_type,
            actor=event_data.actor,
            artefact=event_data.artefact,
            decision=event_data.decision,
            reason=event_data.reason,
            outcome=event_data.outcome,
            confidence=event_data.confidence,
            extra_data=event_data.extra_data,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        
        # Log audit
        audit = AsyncAuditService(db)
        audit_id = await audit.log_decision(event)
        
        return {
            "id": event.id,
            "audit_id": audit_id,
            "event_type": event.event_type,
            "decision": event.decision,
            "message": "Behaviour event created successfully"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events")
async def get_behaviour_events(
    user_id: int = Depends(require_admin),
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get all behaviour events."""
    stmt = select(BehaviourEvent).order_by(BehaviourEvent.timestamp.desc()).limit(limit)
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    return [{
        "id": e.id,
        "event_type": e.event_type,
        "decision": e.decision,
        "outcome": e.outcome,
        "confidence": e.confidence,
        "timestamp": e.timestamp.isoformat()
    } for e in events]

@router.get("/event/{event_id}")
async def get_behaviour_event(
    event_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific behaviour event."""
    stmt = select(BehaviourEvent).where(BehaviourEvent.id == event_id)
    result = await db.execute(stmt)
    event = result.scalars().first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {
        "id": event.id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "actor": event.actor,
        "artefact": event.artefact,
        "decision": event.decision,
        "reason": event.reason,
        "outcome": event.outcome,
        "confidence": event.confidence,
        "extra_data": event.extra_data,
        "timestamp": event.timestamp.isoformat()
    }
