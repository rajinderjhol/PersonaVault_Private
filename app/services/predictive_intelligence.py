"""
Predictive Intelligence Service - Anticipate needs and simulate outcomes
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from app.models.decision_trace import DecisionTrace
from app.models.user import User
from app.services.intelligence_gateway import gateway

logger = logging.getLogger(__name__)


class PredictiveIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_predictions(self, user: User) -> Dict[str, Any]:
        """Generate comprehensive predictions for the user."""
        return {
            "pattern_predictions": await self._predict_patterns(user),
            "outcome_simulations": await self._simulate_outcomes(user),
            "automated_responses": await self._prepare_automated_responses(user),
            "intelligence_trends": await self._analyze_trends(user),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _predict_patterns(self, user: User) -> List[Dict]:
        """Predict emerging patterns before they fully form."""
        predictions = []
        
        # Analyze recent decisions
        recent = datetime.utcnow() - timedelta(days=7)
        result = await self.db.execute(
            select(DecisionTrace)
            .where(DecisionTrace.user_id == user.id)
            .where(DecisionTrace.timestamp >= recent)
        )
        traces = result.scalars().all()
        
        if not traces:
            return predictions
        
        # Group by domain
        domain_counts = defaultdict(int)
        for trace in traces:
            domain = trace.pack_name or "general"
            domain_counts[domain] += 1
        
        # Predict rising domains
        for domain, count in domain_counts.items():
            if count >= 3:
                predictions.append({
                    "type": "pattern",
                    "domain": domain,
                    "confidence": min(0.8 + (count * 0.02), 0.95),
                    "prediction": f"You're building momentum in {domain}. I predict you'll need to make a {domain} decision in the next {max(1, 5 - count)} days.",
                    "suggested_action": f"Review existing {domain} patterns to prepare.",
                    "urgency": "high" if count >= 5 else "medium"
                })
        
        return predictions

    async def _simulate_outcomes(self, user: User) -> List[Dict]:
        """Simulate potential outcomes for future decisions."""
        simulations = []
        
        # Get recent high-confidence patterns
        result = await self.db.execute(
            select(DecisionTrace)
            .where(DecisionTrace.user_id == user.id)
            .where(DecisionTrace.confidence_score >= 0.8)
            .where(DecisionTrace.is_crystallized == True)
            .order_by(desc(DecisionTrace.timestamp))
            .limit(10)
        )
        patterns = result.scalars().all()
        
        for pattern in patterns:
            # Simulate what would happen if this pattern was applied
            simulation = {
                "pattern_id": str(pattern.id),
                "domain": pattern.pack_name or "general",
                "confidence": pattern.confidence_score or 0.8,
                "simulation": {
                    "success_probability": min((pattern.confidence_score or 0.8) * 1.05, 0.98),
                    "risk_level": "low" if (pattern.confidence_score or 0.8) > 0.85 else "medium",
                    "expected_impact": {
                        "efficiency_gain": round((pattern.confidence_score or 0.8) * 0.3, 2),
                        "risk_reduction": round((pattern.confidence_score or 0.8) * 0.2, 2)
                    }
                }
            }
            simulations.append(simulation)
        
        return simulations[:5]

    async def _prepare_automated_responses(self, user: User) -> List[Dict]:
        """Prepare responses for predicted questions."""
        responses = []
        
        # Get common question patterns
        result = await self.db.execute(
            select(DecisionTrace.query, func.count())
            .where(DecisionTrace.user_id == user.id)
            .where(DecisionTrace.query.isnot(None))
            .group_by(DecisionTrace.query)
            .order_by(func.count().desc())
            .limit(5)
        )
        common_queries = result.all()
        
        for query, count in common_queries:
            if count >= 2:
                # Find the best response for this query
                response_result = await self.db.execute(
                    select(DecisionTrace.response)
                    .where(DecisionTrace.user_id == user.id)
                    .where(DecisionTrace.query == query)
                    .where(DecisionTrace.response.isnot(None))
                    .order_by(desc(DecisionTrace.confidence_score))
                    .limit(1)
                )
                best_response = response_result.scalar_one_or_none()
                
                if best_response:
                    responses.append({
                        "query": query,
                        "response": best_response,
                        "confidence": 0.85,
                        "times_asked": count,
                        "ready": True
                    })
        
        return responses

    async def _analyze_trends(self, user: User) -> Dict:
        """Analyze intelligence trends over time."""
        # Confidence trend
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_result = await self.db.execute(
            select(func.avg(DecisionTrace.confidence_score))
            .where(DecisionTrace.user_id == user.id)
            .where(DecisionTrace.timestamp >= week_ago)
        )
        recent_avg = recent_result.scalar() or 0.0
        
        older_result = await self.db.execute(
            select(func.avg(DecisionTrace.confidence_score))
            .where(DecisionTrace.user_id == user.id)
            .where(DecisionTrace.timestamp.between(month_ago, week_ago))
        )
        older_avg = older_result.scalar() or 0.0
        
        # Crystallization rate
        total = await self.db.execute(
            select(func.count()).select_from(DecisionTrace)
            .where(DecisionTrace.user_id == user.id)
        )
        total_count = total.scalar() or 0
        
        crystallized = await self.db.execute(
            select(func.count()).select_from(DecisionTrace)
            .where(DecisionTrace.user_id == user.id)
            .where(DecisionTrace.is_crystallized == True)
        )
        crystallized_count = crystallized.scalar() or 0
        
        return {
            "confidence_trend": "improving" if recent_avg > older_avg else "stable",
            "current_confidence": round(recent_avg * 100, 1),
            "crystallization_rate": round((crystallized_count / total_count) * 100 if total_count > 0 else 0, 1),
            "total_decisions": total_count,
            "crystallized_patterns": crystallized_count
        }
