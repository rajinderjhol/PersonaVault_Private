from typing import Optional, Dict, Any
from app.api.v2.models.environment import Environment
from app.api.v2.models.outcome import Outcome, OutcomeSourceType
from app.api.v2.services.crystallization_service import CrystallizationService
from app.services.memory_service import MemoryService
import logging

logger = logging.getLogger(__name__)

class OutcomeLearningBridge:
    def __init__(self, crystallization_service: CrystallizationService, memory_service: MemoryService):
        self.crystallization_service = crystallization_service
        self.memory_service = memory_service

    async def process_outcome(self, environment: Environment, outcome: Outcome) -> Optional[str]:
        """
        Process an outcome event, detect patterns, and automatically trigger crystallization if appropriate.
        """
        # 1. SECURITY GUARD: Only allow real actions to trigger learning
        if outcome.source_type == OutcomeSourceType.SIMULATION:
            logger.info(f"🛡️ Blocking crystallization from simulation in env {environment.id}")
            return None  # Do not crystallize simulated outcomes
        
        if outcome.source_type == OutcomeSourceType.PREDICTION_EVAL:
            logger.info(f"🛡️ Blocking crystallization from prediction evaluation in env {environment.id}")
            return None  # Do not crystallize prediction evaluations
        
        # 2. Analyze outcome for pattern detection
        pattern = await self._detect_pattern(outcome)
        
        if pattern:
            # 3. Auto-crystallize
            memory_id = await self.crystallization_service.crystallize_pattern(
                environment=environment,
                pattern_data=pattern,
                source_decision_id=outcome.decision_id
            )
            logger.info(f"✅ Crystallized pattern from real action in env {environment.id}")
            return memory_id
        return None

    async def _detect_pattern(self, outcome: Outcome) -> Optional[Dict[str, Any]]:
        """
        Logic to detect if outcome contains a reusable pattern.
        """
        # Basic detection: successful outcome with high confidence
        if outcome.success and outcome.metrics and outcome.metrics.get("confidence", 0) > 0.7:
            return {
                "content": outcome.result.get("summary", "Pattern detected from outcome"),
                "confidence": outcome.metrics.get("confidence", 0.8),
                "tags": ["automated_learning", "outcome_success"]
            }
        return None
