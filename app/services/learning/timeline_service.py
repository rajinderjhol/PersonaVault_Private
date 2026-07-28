"""
Timeline Service for building decision timelines.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.learning.behaviour_event import BehaviourEvent
from app.models.learning.decision_timeline import DecisionTimeline
from app.models.learning.policy import Policy

logger = logging.getLogger(__name__)

class TimelineService:
    """Build and manage decision timelines."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    async def build_timeline(self, event: BehaviourEvent) -> List[Dict]:
        """Build a complete timeline for a decision event."""
        timeline = []
        
        # Step 1: Event detection
        timeline.append({
            "step": 1,
            "type": "detection",
            "label": "Event Detected",
            "description": f"{event.event_type} detected: {event.artefact}",
            "confidence": event.confidence,
            "actor": event.actor,
            "timestamp": event.timestamp.isoformat()
        })
        
        # Step 2: Policy matching
        policies = await self._get_policies_for_event(event)
        if policies:
            timeline.append({
                "step": 2,
                "type": "policy_match",
                "label": "Policy Matched",
                "description": f"Matched {len(policies)} policies",
                "policies": policies,
                "timestamp": event.timestamp.isoformat()
            })
        
        # Step 3: AI Recommendation
        if event.confidence > 0.7:
            timeline.append({
                "step": 3,
                "type": "ai_recommendation",
                "label": "AI Recommendation",
                "description": f"AI recommended {event.decision} with {event.confidence*100:.0f}% confidence",
                "confidence": event.confidence,
                "decision": event.decision,
                "timestamp": event.timestamp.isoformat()
            })
        else:
            timeline.append({
                "step": 3,
                "type": "ai_recommendation",
                "label": "AI Recommendation",
                "description": f"AI uncertain ({event.confidence*100:.0f}%), recommended review",
                "confidence": event.confidence,
                "decision": "review",
                "timestamp": event.timestamp.isoformat()
            })
        
        # Step 4: Decision
        timeline.append({
            "step": 4,
            "type": "decision",
            "label": "Decision Made",
            "description": f"Decision: {event.decision}",
            "reason": event.reason,
            "actor": event.actor,
            "outcome": event.outcome,
            "timestamp": event.timestamp.isoformat()
        })
        
        # Step 5: Audit
        timeline.append({
            "step": 5,
            "type": "audit",
            "label": "Audit Logged",
            "description": f"Audit ID: {event.audit_id}",
            "audit_id": event.audit_id,
            "timestamp": event.timestamp.isoformat()
        })
        
        # Step 6: Learning (if applicable)
        if event.learned:
            timeline.append({
                "step": 6,
                "type": "learning",
                "label": "Learning Applied",
                "description": "Pattern extracted for future decisions",
                "timestamp": event.timestamp.isoformat()
            })
        
        # Save timeline to database
        await self._save_timeline(event.id, timeline)
        
        return timeline
    
    async def _get_policies_for_event(self, event: BehaviourEvent) -> List[str]:
        """Get policies that applied to this event."""
        async with self.session_factory() as db:
            # Simple matching - in production, use actual policy matching
            policies = []
            stmt = select(Policy).where(Policy.is_active == True)
            result = await db.execute(stmt)
            all_policies = result.scalars().all()
            
            for policy in all_policies:
                if policy.triggers:
                    event_text = str(event.extra_data) + " " + str(event.reason)
                    for trigger in policy.triggers:
                        if trigger.lower() in event_text.lower():
                            policies.append(policy.name)
                            break
            
            return policies[:3]  # Limit to top 3
    
    async def _save_timeline(self, event_id: int, timeline: List[Dict]):
        """Save timeline steps to database."""
        async with self.session_factory() as db:
            for step in timeline:
                # Check if step already exists
                stmt = select(DecisionTimeline).where(
                    DecisionTimeline.event_id == event_id,
                    DecisionTimeline.step_number == step["step"]
                )
                result = await db.execute(stmt)
                existing = result.scalars().first()
                
                if existing:
                    # Update existing
                    existing.step_type = step["type"]
                    existing.step_label = step["label"]
                    existing.step_description = step["description"]
                    existing.confidence = step.get("confidence")
                    existing.actor = step.get("actor")
                    existing.reason = step.get("reason")
                    existing.extra_data = {k: v for k, v in step.items() if k not in ["step", "type", "label", "description", "confidence", "actor", "reason", "timestamp"]}
                else:
                    # Create new
                    db_timeline = DecisionTimeline(
                        event_id=event_id,
                        step_number=step["step"],
                        step_type=step["type"],
                        step_label=step["label"],
                        step_description=step["description"],
                        confidence=step.get("confidence"),
                        actor=step.get("actor"),
                        reason=step.get("reason"),
                        extra_data={k: v for k, v in step.items() if k not in ["step", "type", "label", "description", "confidence", "actor", "reason", "timestamp"]}
                    )
                    db.add(db_timeline)
            
            await db.commit()
    
    async def get_timeline(self, event_id: int) -> List[Dict]:
        """Get saved timeline for an event."""
        async with self.session_factory() as db:
            stmt = select(DecisionTimeline).where(
                DecisionTimeline.event_id == event_id
            ).order_by(DecisionTimeline.step_number)
            result = await db.execute(stmt)
            steps = result.scalars().all()
            
            return [{
                "step": step.step_number,
                "type": step.step_type,
                "label": step.step_label,
                "description": step.step_description,
                "confidence": step.confidence,
                "actor": step.actor,
                "reason": step.reason,
                "extra_data": step.extra_data,
                "timestamp": step.timestamp.isoformat()
            } for step in steps]
