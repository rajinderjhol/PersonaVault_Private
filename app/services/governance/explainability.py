"""
Explainability Engine for decision transparency.
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.learning.behaviour_event import BehaviourEvent
from app.models.learning.policy import Policy

logger = logging.getLogger(__name__)

class ExplainabilityEngine:
    """Explain every decision."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    async def explain_decision(self, decision_id: str) -> Dict[str, Any]:
        """Explain a decision."""
        async with self.session_factory() as db:
            # Get the decision
            stmt = select(BehaviourEvent).where(BehaviourEvent.audit_id == decision_id)
            result = await db.execute(stmt)
            event = result.scalars().first()
            
            if not event:
                return {"error": "Decision not found"}
            
            # Get associated policies
            policies = []
            if event.policy_id:
                stmt = select(Policy).where(Policy.id == event.policy_id)
                result = await db.execute(stmt)
                policy = result.scalars().first()
                if policy:
                    policies.append({
                        "name": policy.name,
                        "confidence": policy.confidence,
                        "version": policy.version
                    })
            
            return {
                "decision_id": event.audit_id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "decision": event.decision,
                "reason": event.reason,
                "outcome": event.outcome,
                "confidence": event.confidence,
                "policies_applied": policies,
                "extra_data": event.extra_data,
                "explanation": self._generate_explanation(event, policies)
            }
    
    def _generate_explanation(self, event: BehaviourEvent, policies: list) -> str:
        """Generate human-readable explanation."""
        parts = [
            f"This decision was made by {event.actor or 'system'}",
            f"Decision type: {event.event_type}",
            f"Outcome: {event.outcome}"
        ]
        
        if event.reason:
            parts.append(f"Reason: {event.reason}")
        
        if event.confidence > 0:
            parts.append(f"Confidence: {event.confidence:.2f}")
        
        if policies:
            parts.append(f"Policies applied: {', '.join(p['name'] for p in policies)}")
        
        return ". ".join(parts) + "."
