import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone

from app.models.learning.behaviour_event import BehaviourEvent
from app.models.learning.policy import Policy
from app.swarm.core.inference import policy_inference_agent

logger = logging.getLogger(__name__)

class PolicyInferenceService:
    """
    V3 Policy Inference Service: Automates the transition from human corrections 
    to formal governance policies.
    """
    
    def __init__(self, db: AsyncSession, agent=None):
        self.db = db
        self.agent = agent or policy_inference_agent

    async def infer_and_propose(self, domain: str, user_id: int) -> Dict[str, Any]:
        """
        1. Fetch recent unlearned corrections.
        2. Propose new policies.
        3. Save proposed policies for review.
        """
        logger.info(f"🧠 Inferring implicit governance for domain: {domain}")

        # 1. Fetch corrections
        stmt = select(BehaviourEvent).where(
            BehaviourEvent.event_type == domain,
            BehaviourEvent.correction != None,
            BehaviourEvent.learned == False
        ).limit(50)
        
        result = await self.db.execute(stmt)
        events = result.scalars().all()
        
        if not events:
            return {"status": "skipped", "reason": "No new corrections found"}

        corrections_data = [
            {
                "id": e.id,
                "event": e.event_type,
                "decision": e.decision,
                "correction": e.correction,
                "reason": e.reason
            } for e in events
        ]

        # 2. Fetch existing policies
        policy_stmt = select(Policy).where(Policy.domain == domain, Policy.is_active == True)
        policy_result = await self.db.execute(policy_stmt)
        existing_policies = [
            {
                "name": p.name,
                "description": p.description,
                "conditions": p.conditions
            } for p in policy_result.scalars().all()
        ]

        # 3. Infer new policies
        proposals = await self.agent.infer_policies(corrections_data, existing_policies)
        
        # 4. Save proposals
        created_policies = []
        for prop in proposals:
            try:
                new_policy = Policy(
                    name=f"Inferred: {prop['name']}",
                    domain=domain,
                    description=prop['description'],
                    triggers=prop.get('conditions', []),
                    conditions=prop.get('conditions', []),
                    actions=["notify_admin", "log_audit"], # Default V3 actions
                    confidence=prop.get('confidence', 0.8),
                    is_active=False, # Must be reviewed/promoted
                    created_by=user_id,
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None)
                )
                self.db.add(new_policy)
                created_policies.append(prop['name'])
            except Exception as e:
                logger.error(f"Failed to create inferred policy: {e}")

        # 5. Mark events as learned
        event_ids = [e.id for e in events]
        await self.db.execute(
            update(BehaviourEvent)
            .where(BehaviourEvent.id.in_(event_ids))
            .values(learned=True)
        )
        
        await self.db.commit()

        return {
            "status": "success",
            "events_processed": len(event_ids),
            "policies_proposed": created_policies
        }

async def get_policy_inference_service(db: AsyncSession = None):
    # This would typically be a FastAPI dependency
    return PolicyInferenceService(db)
