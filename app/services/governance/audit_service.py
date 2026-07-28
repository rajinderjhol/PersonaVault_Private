"""
Audit Service for sovereign governance.
"""
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import make_transient
from app.models.learning.behaviour_event import BehaviourEvent

logger = logging.getLogger(__name__)

class AuditService:
    """Enhanced audit trail for all decisions."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    async def log_decision(self, event: BehaviourEvent) -> str:
        """Log a decision with full context."""
        # Generate audit ID
        audit_id = f"audit-{uuid.uuid4().hex[:12]}"
        
        # Create a new event object to avoid session conflicts
        async with self.session_factory() as db:
            # Create a fresh copy of the event
            new_event = BehaviourEvent(
                user_id=event.user_id,
                event_type=event.event_type,
                actor=event.actor,
                artefact=event.artefact,
                decision=event.decision,
                reason=event.reason,
                outcome=event.outcome,
                confidence=event.confidence,
                extra_data=event.extra_data,
                audit_id=audit_id,
                timestamp=event.timestamp or datetime.now(timezone.utc)
            )
            
            # Copy learning fields if present
            if event.pattern_id:
                new_event.pattern_id = event.pattern_id
            if event.policy_id:
                new_event.policy_id = event.policy_id
            if event.correction:
                new_event.correction = event.correction
            if event.learned:
                new_event.learned = event.learned
            
            db.add(new_event)
            await db.commit()
            await db.refresh(new_event)
            
            logger.info(f"Audit logged: {audit_id}")
            return audit_id
    
    async def get_audit_trail(self, decision_id: str) -> Optional[Dict]:
        """Get full audit trail for a decision."""
        async with self.session_factory() as db:
            stmt = select(BehaviourEvent).where(BehaviourEvent.audit_id == decision_id)
            result = await db.execute(stmt)
            event = result.scalars().first()
            
            if not event:
                return None
            
            return {
                "id": event.id,
                "audit_id": event.audit_id,
                "timestamp": event.timestamp.isoformat(),
                "user_id": event.user_id,
                "event_type": event.event_type,
                "decision": event.decision,
                "reason": event.reason,
                "outcome": event.outcome,
                "confidence": event.confidence,
                "extra_data": event.extra_data
            }
    
    async def get_audit_trail_for_user(self, user_id: int, limit: int = 50) -> list:
        """Get audit trail for a user."""
        async with self.session_factory() as db:
            stmt = select(BehaviourEvent).where(
                BehaviourEvent.user_id == user_id
            ).order_by(BehaviourEvent.timestamp.desc()).limit(limit)
            result = await db.execute(stmt)
            events = result.scalars().all()
            
            return [{
                "audit_id": e.audit_id,
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "decision": e.decision,
                "outcome": e.outcome
            } for e in events]
