import hashlib
import json
import logging
from typing import Optional, Dict, Any
from app.api.v2.models.environment import Environment
from app.api.v2.models.outcome import Outcome, OutcomeSourceType
from app.api.v2.services.crystallization_service import CrystallizationService
from app.services.memory_service import MemoryService
from datetime import datetime

logger = logging.getLogger(__name__)

class OutcomeLearningBridge:
    def __init__(self, crystallization_service: CrystallizationService, memory_service: MemoryService):
        self.crystallization_service = crystallization_service
        self.memory_service = memory_service

    async def process_outcome(
        self,
        environment: Environment,
        outcome: Outcome
    ) -> Optional[str]:
        """
        Process an outcome and trigger crystallization if appropriate.
        Now includes idempotency to prevent duplicate learning.
        """
        # 1. Generate idempotency key
        idempotency_key = self._generate_idempotency_key(outcome)
        
        # 2. Check if this outcome has already been processed
        if await self._is_outcome_processed(environment.id, idempotency_key):
            logger.info(f"🔄 Outcome {idempotency_key} already processed in env {environment.id}. Skipping.")
            return None

        # 3. SECURITY GUARD: Only allow real actions to trigger learning
        if outcome.source_type == OutcomeSourceType.SIMULATION:
            logger.info(f"🛡️ Blocking crystallization from simulation in env {environment.id}")
            return None  # Do not crystallize simulated outcomes
        
        if outcome.source_type == OutcomeSourceType.PREDICTION_EVAL:
            logger.info(f"🛡️ Blocking crystallization from prediction evaluation in env {environment.id}")
            return None  # Do not crystallize prediction evaluations
        
        # 4. Analyze outcome for pattern detection
        pattern = await self._detect_pattern(outcome)
        
        if pattern:
            # 5. Auto-crystallize
            try:
                memory_id = await self.crystallization_service.crystallize_pattern(
                    environment=environment,
                    pattern_data=pattern,
                    source_decision_id=outcome.decision_id
                )
                
                # 6. Mark outcome as processed
                await self._mark_outcome_processed(environment.id, idempotency_key, memory_id)
                
                logger.info(f"✅ Crystallized pattern from outcome {idempotency_key} in env {environment.id}")
                return memory_id
            except Exception as e:
                logger.error(f"❌ Crystallization failed for outcome {idempotency_key} in env {environment.id}: {e}")
                return None
        
        return None

    def _generate_idempotency_key(self, outcome: Outcome) -> str:
        """Generate a unique key for an outcome to prevent duplicate processing."""
        # Use decision_id/action_id and a hash of the result
        decision_id = outcome.decision_id or "unknown"
        action_id = outcome.action_id or "unknown"
        # Create a stable representation of the result
        result_str = json.dumps(outcome.result, sort_keys=True)
        result_hash = hashlib.sha256(result_str.encode()).hexdigest()[:8]
        return f"{decision_id}_{action_id}_{result_hash}"

    async def _is_outcome_processed(self, environment_id: str, idempotency_key: str) -> bool:
        """Check if this outcome has already been processed."""
        try:
            processed = await self.memory_service.search_memories(
                user_id=1,
                query=idempotency_key,
                limit=1,
                environment_id=environment_id
            )
            return len(processed) > 0
        except Exception:
            return False

    async def _mark_outcome_processed(self, environment_id: str, idempotency_key: str, memory_id: str):
        """Mark an outcome as processed."""
        await self.memory_service.save_memory(
            user_id=1,
            memory_type="processed_outcome",
            content=f"Processed outcome: {idempotency_key}",
            tags=["automated_learning", "processed_outcome"],
            title=f"Processed Outcome {idempotency_key}",
            environment_id=environment_id
        )

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
