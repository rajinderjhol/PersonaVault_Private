import httpx
import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from app.services.trace_service import TraceService, TraceStep

class BaseAgent:
    """Foundation for all PersonaVault Swarm Agents with Auditable Trace support."""
    def __init__(self, name: str, client: Optional[httpx.AsyncClient] = None, trace_service: Optional[TraceService] = None):
        self.name = name
        self._client = client
        self.trace_service = trace_service
        self.logger = logging.getLogger(f"persona.swarm.{name}")
        self.temporal_context: Optional[Dict[str, Any]] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy access to a shared AsyncClient."""
        if not self._client:
            self.logger.debug(f"Agent {self.name}: Initializing local AsyncClient.")
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def create_trace_async(self, 
                     input_data: Any, 
                     signals: List[Dict] = None, 
                     policy: Optional[str] = None, 
                     decision: Optional[str] = None,
                     explanation: Optional[str] = None,
                     confidence: float = 0.5,
                     metadata: Optional[Dict] = None,
                     session_id: Optional[int] = None,
                     step: TraceStep = TraceStep.SUMMARY) -> Dict[str, Any]:
                     """Generate and optionally persist a structured Auditable Decision Trace."""
                     trace_dict = {
                         "decision_id": f"D-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{hash(str(input_data)) % 10000:04d}",
                         "timestamp": datetime.now().isoformat(),
                         "agent": self.name,
                         "trace": {
                             "perception": {
                                 "source": "raw_input",
                                 "confidence": confidence
                             },
                             "signals": signals or [],
                             "policy": {
                                 "matched": policy or "default",
                                 "conditions": []
                             },
                             "decision": {
                                 "type": decision or "observe",
                                 "severity": "low",
                                 "autonomy_level": "observe",
                                 "metadata": metadata or {}
                             },
                             "actions": []
                         },
                         "explanation": explanation or "Agent processed input"
                     }

                     if self.temporal_context:
                         trace_dict["trace"]["perception"]["temporal_context"] = self.temporal_context

                     # Persist to database if service and session are available
                     if self.trace_service and session_id:
                         try:
                             await self.trace_service.capture_step(
                                 session_id=session_id,
                                 step=step,
                                 data=trace_dict,
                                 agent_id=self.name,
                                 confidence_score=confidence,
                                 query=str(input_data),
                                 pack_name=metadata.get("domain") if metadata else None
                             )
                         except Exception as e:
                             self.logger.error(f"Failed to persist trace to DB: {e}")

                     return trace_dict

    def create_trace(self, *args, **kwargs) -> Dict[str, Any]:
        """Legacy synchronous trace creation (does not persist to DB)."""
        return {
            "decision_id": f"D-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{hash(str(args[0] if args else '')) % 10000:04d}",
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "trace": {
                "perception": {"source": "raw_input", "confidence": kwargs.get('confidence', 0.5)},
                "signals": kwargs.get('signals', []),
                "policy": {"matched": kwargs.get('policy', 'default'), "conditions": []},
                "decision": {
                    "type": kwargs.get('decision', 'observe'),
                    "severity": "low",
                    "autonomy_level": "observe",
                    "metadata": kwargs.get('metadata', {})
                },
                "actions": []
            },
            "explanation": kwargs.get('explanation', "Agent processed input")
        }