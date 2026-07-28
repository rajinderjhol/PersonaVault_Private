"""
Policy Evolution Engine for automatic policy improvement.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.learning.policy import Policy
from app.models import SemanticPattern  # Import from __init__

logger = logging.getLogger(__name__)

class PolicyEvolutionEngine:
    """Evolve policies based on outcomes."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    async def propose_policy(self, patterns: List[Dict]) -> Optional[Policy]:
        """Propose a new policy from patterns."""
        if not patterns or len(patterns) < 2:
            return None
        
        # Find common triggers
        common_triggers = []
        for pattern in patterns:
            if "trigger" in pattern:
                common_triggers.append(pattern["trigger"])
        
        if not common_triggers:
            return None
        
        # Create policy
        policy = Policy(
            name=f"Auto-Policy-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            version="1.0.0",
            domain="auto",
            description="Automatically proposed policy from patterns",
            triggers=list(set(common_triggers)),
            actions=[{"action": "flag", "severity": "medium"}],
            confidence=0.5,
            is_active=False  # Start as draft
        )
        
        return policy
    
    async def promote_policy(self, policy_id: int) -> bool:
        """Promote a policy to active if it meets criteria."""
        async with self.session_factory() as db:
            stmt = select(Policy).where(Policy.id == policy_id)
            result = await db.execute(stmt)
            policy = result.scalars().first()
            
            if not policy:
                return False
            
            if policy.confidence >= 0.7 and policy.success_count >= 3:
                policy.is_active = True
                policy.is_promoted = True
                await db.commit()
                logger.info(f"Policy {policy.name} promoted to active")
                return True
            
            return False
    
    async def retire_policy(self, policy_id: int) -> bool:
        """Retire a policy if it's no longer effective."""
        async with self.session_factory() as db:
            stmt = select(Policy).where(Policy.id == policy_id)
            result = await db.execute(stmt)
            policy = result.scalars().first()
            
            if not policy:
                return False
            
            # Check if policy should be retired
            if policy.confidence < 0.3:
                policy.is_active = False
                await db.commit()
                logger.info(f"Policy {policy.name} retired (confidence: {policy.confidence:.2f})")
                return True
            
            if policy.failure_count > policy.success_count * 2:
                policy.is_active = False
                await db.commit()
                logger.info(f"Policy {policy.name} retired (failures: {policy.failure_count})")
                return True
            
            return False
