from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MedicalTelemetryAdapter:
    """
    Converts raw medical device data into Layer 1 memory and monitors for anomalies.
    """
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        # Default baseline reading
        self.last_reading = {"heart_rate": 72, "spo2": 99, "is_anomaly": False, "timestamp": datetime.utcnow().isoformat()}

    async def process_telemetry(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses incoming telemetry and triggers HITL if safety thresholds are crossed.
        """
        hr = raw_data.get("heart_rate", 75)
        spo2 = raw_data.get("spo2", 98)
        
        anomaly = False
        reason = ""

        if spo2 < 92:
            anomaly = True
            reason = f"Low blood oxygen detected: {spo2}%"
        elif hr > 140 or hr < 40:
            anomaly = True
            reason = f"Abnormal heart rate: {hr} bpm"

        processed = {
            "timestamp": datetime.utcnow().isoformat(),
            "heart_rate": hr,
            "spo2": spo2,
            "is_anomaly": anomaly,
            "reason": reason
        }
        
        self.last_reading = processed

        if anomaly and self.orchestrator:
            logger.warning(f"Medical Anomaly Detected: {reason}. Escalating to HITL Agent.")
            # Trigger Proactive HITL if the agent is available in the swarm
            if "hitl" in self.orchestrator.agents:
                await self.orchestrator.agents["hitl"].request_clarification(
                    agent_type="HealthAgent",
                    query=f"Medical alert: {reason}",
                    options={"telemetry": processed, "priority": "critical"}
                )

        return processed