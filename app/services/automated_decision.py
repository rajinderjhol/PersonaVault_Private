"""
Automated Decision Engine
Safely executes routine, high-confidence decisions automatically.
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import BehaviourEvent, SystemConfig
from app.services.self_improving import SelfImprovingIntelligence
from app.services.trace_service import TraceService
from app.models.decision_trace import TraceStep

logger = logging.getLogger(__name__)

class AutomatedDecisionEngine:
    """
    Automates routine decisions with high confidence.
    This is the culmination of the learning and prediction phases.
    """
    
    def __init__(self, db: AsyncSession, trace_service: Optional[TraceService] = None):
        self.db = db
        self.self_improving = SelfImprovingIntelligence(db)
        self.trace_service = trace_service
        self.min_confidence = 0.85  # Minimum confidence for automation
        self.max_daily_auto = 10  # Max auto-decisions per day
    
    async def can_automate(self, decision: Dict) -> Dict:
        """
        Determine if a decision can be automated.
        """
        confidence = decision.get("confidence", 0)
        domain = decision.get("domain", "unknown")
        
        # Check confidence
        if confidence < self.min_confidence:
            return {"can_automate": False, "reason": "confidence_too_low", "threshold": self.min_confidence}
        
        # Check if domain is routine
        if not await self._is_routine_domain(domain):
            return {"can_automate": False, "reason": "domain_not_routine"}
        
        # Check daily limit
        daily_count = await self._get_daily_auto_count()
        if daily_count >= self.max_daily_auto:
            return {"can_automate": False, "reason": "daily_limit_reached", "limit": self.max_daily_auto}
        
        # Check if similar decision was successful before
        similar_success = await self._has_similar_success(decision)
        if not similar_success:
            return {"can_automate": False, "reason": "no_similar_success"}
        
        return {
            "can_automate": True,
            "reason": "all_conditions_met",
            "confidence": confidence,
            "similar_successes": similar_success
        }
    
    async def execute_automated_decision(self, decision: Dict, session_id: Optional[int] = None) -> Dict:
        """
        Execute a decision automatically.
        """
        check = await self.can_automate(decision)
        if not check["can_automate"]:
            return {
                "executed": False,
                "decision": decision,
                "reason": check["reason"],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Log the automated decision
        event = BehaviourEvent(
            user_id=decision.get("user_id", 1),
            domain=decision.get("domain", "automated"),
            event_type=decision.get("event_type", "automated_decision"),
            decision=decision.get("decision", "approved"),
            reason=f"Automated decision: {decision.get('reason', '')}",
            outcome="success",
            confidence=decision.get("confidence", 0),
            extra_data={"automated": True, "original_decision": decision}
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        
        # --- TRACE CAPTURE: ACTION & OUTCOME ---
        trace_id = None
        if self.trace_service and session_id:
            # Capture ACTION step
            action_trace = await self.trace_service.capture_step(
                session_id=session_id,
                step=TraceStep.ACTION,
                data={
                    "decision_id": str(event.id),
                    "domain": decision.get("domain", "unknown"),
                    "action_taken": decision.get("decision", "approved"),
                    "reason": decision.get("reason", ""),
                    "confidence": decision.get("confidence", 0)
                },
                agent_id="AutomatedDecisionEngine",
                confidence_score=decision.get("confidence", 0.8)
            )
            
            # Capture OUTCOME step
            outcome_trace = await self.trace_service.capture_step(
                session_id=session_id,
                step=TraceStep.OUTCOME,
                data={
                    "decision_id": str(event.id),
                    "outcome": "success",
                    "timestamp": datetime.utcnow().isoformat(),
                    "execution_time_ms": 0
                },
                agent_id="AutomatedDecisionEngine",
                confidence_score=0.9
            )
            trace_id = str(action_trace.id) if action_trace else None
            
            # Add provenance
            if action_trace:
                await self.trace_service.add_provenance(
                    trace_id=action_trace.id,
                    source_type="automated_decision",
                    source_id=str(event.id),
                    source_text=f"Automated {decision.get('domain', '')} decision",
                    relevance_score=decision.get("confidence", 0.8)
                )
        # --- END TRACE CAPTURE ---
        
        logger.info(f"⚡ Automated decision executed: {event.id} - {decision.get('decision', 'unknown')}")
        
        return {
            "executed": True,
            "decision_id": event.id,
            "decision": decision,
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": trace_id
        }
    
    async def _is_routine_domain(self, domain: str) -> bool:
        """Check if a domain is routine and suitable for automation."""
        routine_domains = ["security", "compliance", "procurement", "contract"]
        return domain in routine_domains
    
    async def _get_daily_auto_count(self) -> int:
        """Get the number of automated decisions today."""
        today = datetime.utcnow().date()
        stmt = select(BehaviourEvent).where(
            and_(
                BehaviourEvent.extra_data.contains({"automated": True}),
                BehaviourEvent.timestamp >= today
            )
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())
    
    async def _has_similar_success(self, decision: Dict) -> int:
        """Check if similar decisions have been successful."""
        similar_count = 0
        patterns = await self.self_improving.get_active_patterns()
        
        for pattern in patterns:
            if pattern.get("type") == "success" and pattern.get("weight", 0) > 0.7:
                trigger = pattern.get("trigger", "").lower()
                decision_text = str(decision).lower()
                if trigger and trigger in decision_text:
                    similar_count += 1
        
        return similar_count
    
    async def get_automation_stats(self) -> Dict:
        """Get statistics on automated decisions."""
        stmt = select(BehaviourEvent).where(
            BehaviourEvent.extra_data.contains({"automated": True})
        )
        result = await self.db.execute(stmt)
        auto_decisions = result.scalars().all()
        
        if auto_decisions:
            successes = sum(1 for d in auto_decisions if d.outcome == "success")
            success_rate = (successes / len(auto_decisions)) * 100
        else:
            success_rate = 0
        
        return {
            "total_automated": len(auto_decisions),
            "success_rate": success_rate,
            "daily_limit": self.max_daily_auto,
            "daily_used": await self._get_daily_auto_count(),
            "min_confidence": self.min_confidence
        }
    
    async def get_pending_automations(self) -> List[Dict]:
        """Get decisions that are candidates for automation."""
        candidates = []
        patterns = await self.self_improving.get_active_patterns()
        high_confidence_patterns = [p for p in patterns if p.get("weight", 0) > 0.8]
        
        for pattern in high_confidence_patterns:
            candidates.append({
                "pattern_id": pattern.get("id"),
                "trigger": pattern.get("trigger"),
                "type": pattern.get("type"),
                "confidence": pattern.get("confidence", 0.5),
                "weight": pattern.get("weight", 0),
                "automation_ready": pattern.get("weight", 0) > 0.85
            })
        
        return candidates
