"""
Proactive Intelligence Service - Anticipate user needs and provide suggestions
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from datetime import datetime, timedelta
import logging

from app.models.decision_trace import DecisionTrace
from app.models.user import User
from app.services.intelligence_gateway import gateway

logger = logging.getLogger(__name__)


class ProactiveIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_insights(self, user: User) -> List[Dict[str, Any]]:
        """Generate proactive insights based on user activity."""
        insights = []
        
        # 1. Check for patterns
        patterns = await self._detect_patterns(user)
        if patterns:
            insights.append({
                "type": "pattern",
                "title": "🔍 Emerging Pattern Detected",
                "description": f"I've noticed {patterns['count']} similar decisions forming a pattern.",
                "action": "Review pattern",
                "priority": "high"
            })
        
        # 2. Check for crystallization opportunities
        crystallization = await self._check_crystallization(user)
        if crystallization:
            insights.append({
                "type": "crystallization",
                "title": "🧊 Crystallization Ready",
                "description": f"You have {crystallization['count']} decisions ready to crystallize.",
                "action": "Crystallize now",
                "priority": "high"
            })
        
        # 3. Check for confidence drops
        confidence_drop = await self._check_confidence_drop(user)
        if confidence_drop:
            insights.append({
                "type": "alert",
                "title": "⚠️ Confidence Drop Detected",
                "description": f"Confidence in {confidence_drop['domain']} has dropped by {confidence_drop['drop']}%.",
                "action": "Investigate",
                "priority": "high"
            })
        
        # 4. Check for inactivity
        if await self._check_inactivity(user):
            insights.append({
                "type": "reminder",
                "title": "💡 Ready to Continue?",
                "description": "You haven't made any decisions in 3 days. New insights are waiting.",
                "action": "Start now",
                "priority": "medium"
            })
        
        return insights

    async def _detect_patterns(self, user: User) -> Optional[Dict]:
        """Detect emerging patterns in user decisions."""
        # Get recent decisions
        recent = datetime.utcnow() - timedelta(days=7)
        result = await self.db.execute(
            select(DecisionTrace)
            .where(DecisionTrace.user_id == user.id)
            .where(DecisionTrace.timestamp >= recent)
        )
        traces = result.scalars().all()
        
        # Group by domain/pack
        domains = {}
        for trace in traces:
            domain = trace.pack_name or "unknown"
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(trace)
        
        # Find domains with multiple decisions
        patterns = []
        for domain, domain_traces in domains.items():
            if len(domain_traces) >= 5:
                patterns.append({
                    "domain": domain,
                    "count": len(domain_traces),
                    "average_confidence": sum(t.confidence_score or 0 for t in domain_traces) / len(domain_traces)
                })
        
        if patterns:
            return {
                "count": len(patterns),
                "patterns": patterns
            }
        return None

    async def _check_crystallization(self, user: User) -> Optional[Dict]:
        """Check for decisions ready to crystallize."""
        # Find high confidence decisions that aren't crystallized
        result = await self.db.execute(
            select(DecisionTrace)
            .where(DecisionTrace.user_id == user.id)
            .where(DecisionTrace.confidence_score >= 0.8)
            .where(DecisionTrace.is_crystallized == False)
        )
        traces = result.scalars().all()
        
        if len(traces) >= 3:
            return {
                "count": len(traces),
                "traces": [{"id": str(t.id), "step": t.step} for t in traces[:3]]
            }
        return None

    async def _check_confidence_drop(self, user: User) -> Optional[Dict]:
        """Check for significant confidence drops."""
        # Get recent vs older confidence
        recent = datetime.utcnow() - timedelta(days=7)
        older = datetime.utcnow() - timedelta(days=30)
        
        recent_result = await self.db.execute(
            select(func.avg(DecisionTrace.confidence_score))
            .where(DecisionTrace.user_id == user.id)
            .where(DecisionTrace.timestamp >= recent)
        )
        recent_avg = recent_result.scalar() or 0.5
        
        older_result = await self.db.execute(
            select(func.avg(DecisionTrace.confidence_score))
            .where(DecisionTrace.user_id == user.id)
            .where(DecisionTrace.timestamp.between(older, recent))
        )
        older_avg = older_result.scalar() or 0.5
        
        drop = (older_avg - recent_avg) * 100
        if drop > 15:
            return {
                "domain": "Overall",
                "drop": round(drop, 1)
            }
        return None

    async def _check_inactivity(self, user: User) -> bool:
        """Check if user has been inactive."""
        recent = datetime.utcnow() - timedelta(days=3)
        result = await self.db.execute(
            select(DecisionTrace)
            .where(DecisionTrace.user_id == user.id)
            .where(DecisionTrace.timestamp >= recent)
            .limit(1)
        )
        return result.scalar_one_or_none() is None
