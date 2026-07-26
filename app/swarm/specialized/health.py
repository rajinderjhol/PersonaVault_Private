from app.swarm.base import BaseAgent
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class HealthAgent(BaseAgent):
    """Specialized agent for medical telemetry monitoring."""
    def __init__(self, orchestrator: Any = None, client: Optional[Any] = None):
        super().__init__(name="health", client=client)
        self.orchestrator = orchestrator
        self.last_reading = {"heart_rate": 72, "spo2": 98, "is_anomaly": False}

    async def process_telemetry(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        hr = raw_data.get("heart_rate", 72)
        spo2 = raw_data.get("spo2", 98)
        
        if spo2 < 92:
            self.logger.warning(f"Health Alert: Low O2 ({spo2}%) detected.")
            
        return {"status": "normal" if spo2 >= 92 else "anomaly", "bpm": hr}
