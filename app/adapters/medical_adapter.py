import logging
logger = logging.getLogger(__name__)

class MedicalTelemetryAdapter:
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.last_reading = {"heart_rate": 72, "spo2": 98, "is_anomaly": False}
