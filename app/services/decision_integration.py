"""
Decision Timeline Integration
Connects learned patterns to decisions in the timeline.
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.models import SemanticPattern, EpisodicEntry
from app.services.self_improving import SelfImprovingIntelligence

logger = logging.getLogger(__name__)

class DecisionIntegration:
    """
    Integrates learned patterns with the decision timeline.
    Patterns influence future decisions and decisions reinforce patterns.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.self_improving = SelfImprovingIntelligence(db)
    
    async def enrich_decision_with_patterns(self, decision: Dict) -> Dict:
        """
        Enrich a decision with insights from learned patterns.
        """
        patterns = await self.self_improving.get_active_patterns()
        
        relevant_patterns = []
        for pattern in patterns:
            trigger = pattern.get("trigger", "").lower()
            decision_text = str(decision).lower()
            if trigger and trigger in decision_text:
                relevant_patterns.append(pattern)
            elif pattern.get("type") == "domain" and decision.get("domain") == pattern.get("trigger"):
                relevant_patterns.append(pattern)
        
        if not relevant_patterns:
            return decision
        
        decision["pattern_insights"] = [
            {
                "type": p.get("type", "unknown"),
                "trigger": p.get("trigger", ""),
                "correction": p.get("correction", ""),
                "confidence": p.get("confidence", 0.5)
            }
            for p in relevant_patterns
        ]
        
        high_confidence = [p for p in relevant_patterns if p.get("confidence", 0) > 0.8]
        if high_confidence:
            best = high_confidence[0]
            decision["pattern_applied"] = True
            decision["pattern_guidance"] = best.get("correction", "")
            logger.info(f"✅ Applied pattern to decision: {best.get('type')} (confidence: {best.get('confidence', 0):.2f})")
        
        return decision
    
    async def record_decision_outcome(self, decision_id: int, outcome: str, confidence: float):
        """
        Record the outcome of a decision to reinforce patterns.
        """
        stmt = select(EpisodicEntry).where(EpisodicEntry.id == decision_id)
        result = await self.db.execute(stmt)
        decision = result.scalars().first()
        
        if not decision:
            logger.warning(f"Decision {decision_id} not found")
            return
        
        # Using existing fields in EpisodicEntry
        decision.evaluation = {"outcome": outcome, "confidence": confidence}
        await self.db.commit()
        
        if outcome == "success" and confidence > 0.8:
            await self._reinforce_success(decision)
        elif outcome == "failure" or confidence < 0.5:
            await self._review_failure(decision)
        
        logger.info(f"📊 Decision {decision_id} recorded: {outcome} (confidence: {confidence:.2f})")
    
    async def _reinforce_success(self, decision: EpisodicEntry):
        patterns = await self.self_improving.get_active_patterns()
        
        for pattern in patterns:
            trigger = pattern.get("trigger", "").lower()
            if trigger and trigger in (decision.query or "").lower():
                stmt = select(SemanticPattern).where(SemanticPattern.id == pattern["id"])
                result = await self.db.execute(stmt)
                db_pattern = result.scalars().first()
                if db_pattern:
                    db_pattern.weight += 0.05
                    db_pattern.success_count += 1
                    await self.db.commit()
                    logger.info(f"✅ Pattern {db_pattern.id} reinforced")
    
    async def _review_failure(self, decision: EpisodicEntry):
        patterns = await self.self_improving.get_active_patterns()
        
        for pattern in patterns:
            trigger = pattern.get("trigger", "").lower()
            if trigger and trigger in (decision.query or "").lower():
                stmt = select(SemanticPattern).where(SemanticPattern.id == pattern["id"])
                result = await self.db.execute(stmt)
                db_pattern = result.scalars().first()
                if db_pattern:
                    db_pattern.weight -= 0.10
                    if db_pattern.weight < 0.40:
                        db_pattern.is_active = False
                    await self.db.commit()
                    logger.info(f"📉 Pattern {db_pattern.id} adjusted")
    
    async def get_decision_trends(self, days: int = 30) -> Dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = select(EpisodicEntry).where(EpisodicEntry.timestamp >= cutoff)
        result = await self.db.execute(stmt)
        decisions = result.scalars().all()
        
        if not decisions:
            return {"message": "No decisions found in this period"}
        
        total = len(decisions)
        # Simplified success/failure logic based on evaluation field
        successes = sum(1 for d in decisions if d.evaluation and d.evaluation.get("outcome") == "success")
        failures = sum(1 for d in decisions if d.evaluation and d.evaluation.get("outcome") == "failure")
        
        success_rate = (successes / total) * 100 if total > 0 else 0
        
        return {
            "total_decisions": total,
            "success_rate": success_rate,
            "trend": "improving" if success_rate > 80 else "stable" if success_rate > 60 else "declining"
        }
