import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

class BaseAgent:
    """Foundation for all PersonaVault Swarm Agents with Auditable Trace support."""
    def __init__(self, name: str, client: Optional[httpx.AsyncClient] = None):
        self.name = name
        self._client = client
        self.logger = logging.getLogger(f"persona.swarm.{name}")

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy access to a shared AsyncClient."""
        if not self._client:
            self.logger.debug(f"Agent {self.name}: Initializing local AsyncClient.")
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    def create_trace(self, 
                     input_data: Any, 
                     signals: List[Dict] = None, 
                     policy: Optional[str] = None, 
                     decision: Optional[str] = None,
                     explanation: Optional[str] = None,
                     confidence: float = 0.5,
                     metadata: Optional[Dict] = None) -> Dict[str, Any]:
                     """Generate a structured Auditable Decision Trace for this agent's action."""
                     return {
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