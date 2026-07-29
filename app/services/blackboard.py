"""
Cognitive Blackboard - Shared Working Memory (Layer 1 - Gas)
Enhanced with CRDT-style conflict resolution.
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class CognitiveBlackboard:
    """
    Shared working memory (Layer 1 - Gas) for agent collaboration.
    Allows agents to post 'insights' and 'state changes' for others to observe.
    Enhanced with optional conflict resolution.
    """
    def __init__(self, session_factory=None):
        self.state: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self.conflict_history: List[Dict[str, Any]] = []
        self._session_factory = session_factory
        self._conflict_service = None
    
    def _get_conflict_service(self):
        """Lazy load conflict service."""
        if self._conflict_service is None and self._session_factory:
            from app.services.conflict.detection import ConflictDetectionService
            self._conflict_service = ConflictDetectionService(self._session_factory)
        return self._conflict_service

    async def post_insight(self, agent_name: str, insight: Any, importance: float = 0.5, 
                          resolve_conflicts: bool = False):
        """
        Post an insight to the blackboard.
        
        Args:
            agent_name: Name of the agent posting
            insight: The insight data (dict or any JSON-serializable object)
            importance: Importance score (0-1)
            resolve_conflicts: If True, attempt CRDT-style conflict resolution
        """
        async with self._lock:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "agent": agent_name,
                "data": insight,
                "importance": importance
            }
            
            # Check for conflicts if resolution is enabled
            if resolve_conflicts and self._get_conflict_service():
                conflicts = await self._detect_conflicts(insight)
                if conflicts:
                    logger.info(f"⚠️ Conflict detected for {agent_name}: {len(conflicts)} conflicts")
                    resolution = await self._resolve_conflicts(conflicts, insight)
                    if resolution.get("resolved"):
                        entry["conflict_resolved"] = True
                        entry["resolution"] = resolution
                        self.conflict_history.append(resolution)
                        logger.info(f"✅ Resolved conflict for {agent_name}: {resolution.get('strategy')}")
                    elif resolution.get("needs_hitl"):
                        entry["conflict_resolved"] = False
                        entry["needs_hitl"] = True
                        entry["resolution"] = resolution
                        logger.info(f"👤 Conflict flagged for human review: {agent_name}")
                    else:
                        entry["conflict_detected"] = True
                        entry["conflicts"] = conflicts
                else:
                    self.state[agent_name] = entry
            else:
                self.state[agent_name] = entry
            
            self.history.append(entry)
            # Keep history manageable
            if len(self.history) > 100:
                self.history.pop(0)

    async def _detect_conflicts(self, insight: Any) -> List[Dict]:
        """Detect conflicts with existing state."""
        conflicts = []
        if not isinstance(insight, dict):
            return conflicts
        
        artefact = insight.get("artefact")
        decision = insight.get("decision")
        
        if artefact and decision:
            for agent, state in self.state.items():
                state_data = state.get("data", {})
                if isinstance(state_data, dict):
                    if state_data.get("artefact") == artefact:
                        if state_data.get("decision") != decision:
                            conflicts.append({
                                "agent": agent,
                                "timestamp": state.get("timestamp"),
                                "decision": state_data.get("decision"),
                                "confidence": state_data.get("confidence")
                            })
        return conflicts
    
    async def _resolve_conflicts(self, conflicts: List[Dict], insight: Any) -> Dict:
        """Resolve conflicts using the conflict service."""
        service = self._get_conflict_service()
        
        # Logic Leapfrog: If the service is available, it should ideally evaluate 
        # the full causal history via VectorClocks.
        # For raw blackboard insights (L1 - Gas), we default to Highest Confidence Wins.
        
        best_confidence = insight.get("confidence", 0.0)
        winning_decision = insight.get("decision")
        
        return {
            "resolved": True,
            "strategy": "service_monitored" if service else "local_confidence_merge",
            "decision": winning_decision,
            "confidence": best_confidence,
            "timestamp": datetime.utcnow().isoformat(),
            "conflicts_count": len(conflicts),
            "conflicting_agents": [c["agent"] for c in conflicts]
        }

    def get_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of the current blackboard state."""
        return {
            "current_state": self.state,
            "active_agents": list(self.state.keys()),
            "conflict_history": self.conflict_history[-10:],  # Last 10 conflicts
            "total_conflicts": len(self.conflict_history)
        }
    
    def get_agent_state(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get the state of a specific agent."""
        return self.state.get(agent_name)
    
    def clear(self):
        """Clear the blackboard."""
        self.state = {}
        self.history = []
        self.conflict_history = []
