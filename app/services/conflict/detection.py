"""
Conflict Detection and Resolution Service for Multi-Agent Systems.
Implements CRDT-style conflict resolution for state updates.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.learning.behaviour_event import BehaviourEvent
from app.models.learning.policy import Policy
from app.models.learning.vector_clock import VectorClock

logger = logging.getLogger(__name__)

class ConflictDetectionService:
    """Detect and resolve conflicts in agent state updates."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    async def detect_conflicts(self, event: BehaviourEvent, time_window_minutes: int = 5) -> List[BehaviourEvent]:
        """Detect conflicting events for a given event."""
        conflicts = []
        cutoff_time = event.timestamp - timedelta(minutes=time_window_minutes)
        
        async with self.session_factory() as db:
            # Find events with same artefact within time window
            stmt = select(BehaviourEvent).where(
                BehaviourEvent.artefact == event.artefact,
                BehaviourEvent.id != event.id,
                BehaviourEvent.timestamp >= cutoff_time
            )
            result = await db.execute(stmt)
            related_events = result.scalars().all()
            
            # Check for conflicting decisions
            for related in related_events:
                if related.decision != event.decision:
                    conflicts.append(related)
        
        return conflicts
    
    async def resolve_conflict(
        self, 
        events: List[BehaviourEvent], 
        resolution_strategy: str = "crdt_merge"
    ) -> Dict[str, Any]:
        """Resolve conflicts using CRDT-style merge."""
        if len(events) < 2:
            return {"resolved": False, "reason": "Not enough events"}
        
        if resolution_strategy == "crdt_merge":
            return await self._crdt_merge(events)
        elif resolution_strategy == "last_write_wins":
            return await self._last_write_wins(events)
        elif resolution_strategy == "human_review":
            return await self._human_review(events)
        else:
            return {"resolved": False, "reason": f"Unknown strategy: {resolution_strategy}"}
    
    async def _crdt_merge(self, events: List[BehaviourEvent]) -> Dict[str, Any]:
        """Merge conflicting events using CRDT semantics."""
        # Timestamp-based ordering
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        latest = sorted_events[-1]
        
        # Count decision types
        decisions = {}
        for e in events:
            decisions[e.decision] = decisions.get(e.decision, 0) + 1
        
        # If there's a majority decision, use it
        majority_decision = max(decisions, key=decisions.get) if decisions else latest.decision
        
        # Find the event with the highest confidence
        best_event = max(events, key=lambda e: e.confidence)
        max_confidence = max([e.confidence for e in events])
        
        return {
            "resolved": True,
            "strategy": "crdt_merge",
            "merged_decision": majority_decision,
            "confidence": max_confidence,
            "original_events": [e.id for e in events],
            "majority_vote": decisions,
            "highest_confidence_event": best_event.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": f"Majority: {majority_decision} ({decisions}), Best confidence: {best_event.id} ({best_event.confidence:.2f})"
        }
    
    async def _last_write_wins(self, events: List[BehaviourEvent]) -> Dict[str, Any]:
        """Resolve by taking the latest event."""
        latest = max(events, key=lambda e: e.timestamp)
        return {
            "resolved": True,
            "strategy": "last_write_wins",
            "decision": latest.decision,
            "confidence": latest.confidence,
            "event_id": latest.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": f"Latest event: {latest.id} at {latest.timestamp}"
        }
    
    async def _human_review(self, events: List[BehaviourEvent]) -> Dict[str, Any]:
        """Flag for human review."""
        return {
            "resolved": False,
            "strategy": "human_review",
            "events": [e.id for e in events],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": "Conflict requires human resolution",
            "needs_hitl": True,
            "decision_options": list(set([e.decision for e in events]))
        }
