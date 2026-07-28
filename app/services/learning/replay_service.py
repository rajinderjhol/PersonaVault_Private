"""
Decision Replay Service for analyzing decisions over time.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.learning.behaviour_event import BehaviourEvent
from app.models.learning.policy import Policy
from app.models.learning.decision_timeline import DecisionTimeline

logger = logging.getLogger(__name__)

class ReplayService:
    """Replay and analyze decisions."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    async def replay_decision(self, event_id: int, target_time: Optional[datetime] = None) -> Dict:
        """Replay a decision at a specific point in time."""
        async with self.session_factory() as db:
            # Get the event
            stmt = select(BehaviourEvent).where(BehaviourEvent.id == event_id)
            result = await db.execute(stmt)
            event = result.scalars().first()
            
            if not event:
                return {"error": "Event not found"}
            
            # Get policies at target time
            if target_time:
                stmt = select(Policy).where(
                    Policy.created_at <= target_time,
                    Policy.is_active == True
                ).order_by(Policy.created_at.desc())
            else:
                stmt = select(Policy).where(Policy.is_active == True)
            result = await db.execute(stmt)
            policies_at_time = result.scalars().all()
            
            # Simulate decision with policies at that time
            # This is a simplified version - in production, use the actual policy engine
            decision_analysis = {
                "original_decision": event.decision,
                "original_confidence": event.confidence,
                "original_reason": event.reason,
                "policies_at_time": [p.name for p in policies_at_time[:5]],
                "would_decision_change": False,
                "new_decision": None,
                "new_confidence": None,
                "reason_changed": None
            }
            
            # Check if policies have changed since the original decision
            if event.policy_id:
                stmt = select(Policy).where(Policy.id == event.policy_id)
                result = await db.execute(stmt)
                original_policy = result.scalars().first()
                
                if original_policy:
                    # Check if the policy has been updated
                    if original_policy.updated_at > event.timestamp:
                        decision_analysis["would_decision_change"] = True
                        decision_analysis["new_decision"] = event.decision
                        decision_analysis["new_confidence"] = min(1.0, original_policy.confidence + 0.05)
                        decision_analysis["reason_changed"] = "Policy updated since original decision"
            
            return {
                "event_id": event.id,
                "original_timestamp": event.timestamp.isoformat(),
                "target_time": target_time.isoformat() if target_time else "current",
                "original_decision": {
                    "decision": event.decision,
                    "confidence": event.confidence,
                    "reason": event.reason
                },
                "analysis": decision_analysis
            }
    
    async def compare_decisions(self, event_id_1: int, event_id_2: int) -> Dict:
        """Compare two decisions."""
        async with self.session_factory() as db:
            stmt = select(BehaviourEvent).where(BehaviourEvent.id.in_([event_id_1, event_id_2]))
            result = await db.execute(stmt)
            events = result.scalars().all()
            
            if len(events) < 2:
                return {"error": "One or both events not found"}
            
            event1 = events[0]
            event2 = events[1]
            
            return {
                "comparison": {
                    "event_1": {
                        "id": event1.id,
                        "event_type": event1.event_type,
                        "decision": event1.decision,
                        "confidence": event1.confidence,
                        "outcome": event1.outcome,
                        "timestamp": event1.timestamp.isoformat()
                    },
                    "event_2": {
                        "id": event2.id,
                        "event_type": event2.event_type,
                        "decision": event2.decision,
                        "confidence": event2.confidence,
                        "outcome": event2.outcome,
                        "timestamp": event2.timestamp.isoformat()
                    },
                    "differences": {
                        "decision_changed": event1.decision != event2.decision,
                        "confidence_changed": abs(event1.confidence - event2.confidence) > 0.1,
                        "outcome_changed": event1.outcome != event2.outcome,
                        "time_between": (event2.timestamp - event1.timestamp).total_seconds()
                    }
                }
            }
    
    async def get_trend_analysis(self, event_type: str, days: int = 30) -> Dict:
        """Analyze decision trends over time."""
        async with self.session_factory() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            
            stmt = select(BehaviourEvent).where(
                BehaviourEvent.event_type == event_type,
                BehaviourEvent.timestamp >= cutoff
            ).order_by(BehaviourEvent.timestamp)
            result = await db.execute(stmt)
            events = result.scalars().all()
            
            if not events:
                return {"error": "No events found for this type"}
            
            # Calculate trends
            decisions = {}
            confidences = []
            outcomes = {"success": 0, "failure": 0, "pending": 0}
            
            for event in events:
                decisions[event.decision] = decisions.get(event.decision, 0) + 1
                confidences.append(event.confidence)
                if event.outcome:
                    outcomes[event.outcome] = outcomes.get(event.outcome, 0) + 1
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                "event_type": event_type,
                "period_days": days,
                "total_events": len(events),
                "decision_distribution": decisions,
                "average_confidence": avg_confidence,
                "max_confidence": max(confidences) if confidences else 0,
                "min_confidence": min(confidences) if confidences else 0,
                "outcome_distribution": outcomes,
                "trend": "improving" if avg_confidence > 0.7 else "stable" if avg_confidence > 0.5 else "needs_attention"
            }
