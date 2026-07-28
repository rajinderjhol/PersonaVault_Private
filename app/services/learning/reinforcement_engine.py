"""
Reinforcement Engine for continuous decision improvement.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.learning.behaviour_event import BehaviourEvent
from app.models.learning.policy import Policy
from app.models import SemanticPattern

logger = logging.getLogger(__name__)

class ReinforcementEngine:
    """Core reinforcement learning for decision improvement."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    async def evaluate_decision(self, event: BehaviourEvent) -> Dict[str, Any]:
        """Evaluate the quality of a decision."""
        result = {
            "decision_id": event.id,
            "quality_score": 0.0,
            "feedback": [],
            "suggestions": [],
            "policies_applied": []
        }
        
        async with self.session_factory() as db:
            # Check against active policies
            stmt = select(Policy).where(Policy.is_active == True)
            result_db = await db.execute(stmt)
            policies = result_db.scalars().all()
            
            for policy in policies:
                # Check if policy triggers apply
                if self._matches_policy(event, policy):
                    result["policies_applied"].append(policy.name)
                    result["suggestions"].append({
                        "policy": policy.name,
                        "action": policy.actions[0] if policy.actions else "flag",
                        "confidence": policy.confidence
                    })
                    
                    # Update policy last_used
                    policy.last_used = datetime.now(timezone.utc)
            
            await db.commit()
            
            # Calculate quality score
            if result["policies_applied"]:
                result["quality_score"] = 0.8
            else:
                result["quality_score"] = 0.5
            
        return result
    
    def _matches_policy(self, event: BehaviourEvent, policy: Policy) -> bool:
        """Check if an event matches a policy's triggers."""
        if not policy.triggers:
            return False
        
        # Check triggers in event data
        event_text = str(event.extra_data) + " " + str(event.decision) + " " + str(event.reason)
        for trigger in policy.triggers:
            if trigger.lower() in event_text.lower():
                return True
        return False
    
    async def update_policy_confidence(self, policy_id: int, success: bool) -> None:
        """Update policy confidence based on outcome."""
        # Use a single session for the entire operation
        async with self.session_factory() as db:
            stmt = select(Policy).where(Policy.id == policy_id)
            result = await db.execute(stmt)
            policy = result.scalars().first()
            
            if not policy:
                logger.warning(f"Policy {policy_id} not found")
                return
            
            # Store policy name before any session operations
            policy_name = policy.name
            
            # Update the policy
            if success:
                policy.success_count += 1
                new_confidence = min(1.0, policy.confidence + 0.05)
            else:
                policy.failure_count += 1
                new_confidence = max(0.1, policy.confidence - 0.10)
            
            policy.confidence = new_confidence
            policy.updated_at = datetime.now(timezone.utc)
            
            await db.commit()
            
            # Log the update (using the stored policy name)
            logger.info(f"Policy {policy_name} confidence updated to {new_confidence:.2f}")
    
    async def extract_pattern(self, events: List[BehaviourEvent]) -> Optional[Dict]:
        """Extract pattern from a list of events."""
        if not events or len(events) < 3:
            return None
        
        # Count decision types
        decision_counts = {}
        for event in events:
            decision = event.decision
            decision_counts[decision] = decision_counts.get(decision, 0) + 1
        
        # Find most common pattern
        if decision_counts:
            most_common = max(decision_counts, key=decision_counts.get)
            if decision_counts[most_common] >= 3:
                return {
                    "pattern": most_common,
                    "count": decision_counts[most_common],
                    "confidence": min(1.0, decision_counts[most_common] / len(events)),
                    "event_ids": [e.id for e in events]
                }
        
        return None
