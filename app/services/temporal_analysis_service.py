"""
Temporal Analysis Service - Engine for time-aware intelligence calculations
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.decision_trace import DecisionTrace

logger = logging.getLogger(__name__)

class TemporalAnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_decision_velocity(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Calculate decision velocity over a period."""
        start_date = datetime.utcnow() - timedelta(days=days)
        stmt = select(DecisionTrace).where(
            DecisionTrace.user_id == user_id,
            DecisionTrace.timestamp >= start_date
        ).order_by(DecisionTrace.timestamp)
        
        result = await self.db.execute(stmt)
        traces = result.scalars().all()
        
        if not traces:
            return {"velocity": 0, "unit": "decisions/day"}
            
        total_days = (datetime.utcnow() - traces[0].timestamp).days or 1
        velocity = len(traces) / total_days
        
        return {
            "velocity": round(velocity, 2),
            "total_decisions": len(traces),
            "time_span_days": total_days,
            "unit": "decisions/day"
        }

    def calculate_pattern_decay(self, confidence: float, last_reinforced: datetime, decay_rate: float = 0.1) -> float:
        """Calculate current confidence based on temporal decay."""
        days_passed = (datetime.utcnow() - last_reinforced).days
        # Exponential decay: C = C0 * e^(-rt)
        decayed_confidence = confidence * (1 - decay_rate) ** days_passed
        return max(0.0, decayed_confidence)

    async def get_temporal_relevance_score(self, trace: DecisionTrace) -> float:
        """Calculate temporal relevance of a decision trace."""
        # More recent decisions are more relevant
        days_old = (datetime.utcnow() - trace.timestamp).days
        # Simple relevance formula: 1 / (1 + days_old)
        return 1 / (1 + days_old)
