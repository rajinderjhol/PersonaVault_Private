"""
Collaborative Intelligence Service
Enables team learning, shared insights, and collective intelligence.
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import BehaviourEvent, User, Organization
from app.services.self_improving import SelfImprovingIntelligence

logger = logging.getLogger(__name__)

class CollaborativeIntelligence:
    """
    Enables team-based learning and shared intelligence.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.self_improving = SelfImprovingIntelligence(db)
    
    # ==================== TEAM LEARNING ====================
    
    async def share_insight(self, user_id: int, insight: Dict) -> Dict:
        """
        Share an insight with the team.
        """
        # Store the insight in a shared semantic pattern or similar
        # For this prototype, we'll log it and reinforce team patterns
        logger.info(f"User {user_id} shared insight: {insight}")
        
        await self._apply_team_insight(insight)
        
        return {"status": "shared", "shared_at": datetime.utcnow().isoformat()}
    
    async def _apply_team_insight(self, insight: Dict):
        """Apply an insight to team patterns."""
        # Future: Upsert to a shared patterns table
        pass
    
    # ==================== CROSS-DOMAIN TRANSFER ====================
    
    async def transfer_patterns(self, source_domain: str, target_domain: str) -> Dict:
        """
        Transfer learned patterns from one domain to another.
        """
        # Get patterns from source domain
        source_patterns = await self.self_improving.get_active_patterns()
        
        # Filter by domain
        domain_patterns = [p for p in source_patterns if p.get("trigger", "").lower() == source_domain.lower() or p.get("type") == "domain"]
        
        # Transfer to target (simulation)
        transferred = []
        for pattern in domain_patterns[:5]:
            transferred.append({
                "original": pattern,
                "new_domain": target_domain,
                "adapted": True,
                "confidence": pattern.get("confidence", 0.5)
            })
        
        return {
            "source_domain": source_domain,
            "target_domain": target_domain,
            "transferred": len(transferred),
            "patterns": transferred
        }
    
    # ==================== TEAM STATISTICS ====================
    
    async def get_team_stats(self, team_id: int) -> Dict:
        """
        Get statistics for a team.
        """
        # Get team members
        team_members = await self._get_team_members(team_id)
        
        # Aggregate statistics
        stats = {
            "team_id": team_id,
            "members": len(team_members),
            "total_decisions": 0,
            "avg_confidence": 0,
            "top_domains": {},
            "shared_patterns": 0
        }
        
        if not team_members:
            return stats
            
        for member in team_members:
            # Get member stats
            member_stats = await self._get_member_stats(member.id)
            stats["total_decisions"] += member_stats.get("total_decisions", 0)
            stats["avg_confidence"] += member_stats.get("avg_confidence", 0)
        
        if team_members:
            stats["avg_confidence"] /= len(team_members)
        
        return stats
    
    async def _get_team_members(self, team_id: int) -> List[User]:
        """Get members of a team/organization."""
        stmt = select(User).where(User.organization_id == team_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def _get_member_stats(self, user_id: int) -> Dict:
        """Get statistics for a single member."""
        stmt = select(func.count(BehaviourEvent.id)).where(BehaviourEvent.user_id == user_id)
        total_decisions = (await self.db.execute(stmt)).scalar() or 0
        
        stmt = select(func.avg(BehaviourEvent.confidence)).where(BehaviourEvent.user_id == user_id)
        avg_confidence = (await self.db.execute(stmt)).scalar() or 0
        
        return {"total_decisions": total_decisions, "avg_confidence": avg_confidence or 0}
