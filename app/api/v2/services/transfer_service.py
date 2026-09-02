from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime
from app.api.v2.models.environment import Environment
from app.api.v2.models.transfer import TransferCandidate, SensitivityClassification, AbstractionLevel
from app.api.v2.services.crystallization_service import CrystallizationService

SENSITIVITY_RANK = {
    SensitivityClassification.PUBLIC: 0,
    SensitivityClassification.INTERNAL: 1,
    SensitivityClassification.CONFIDENTIAL: 2,
    SensitivityClassification.RESTRICTED: 3,
    SensitivityClassification.SENSITIVE: 4
}

class TransferService:
    def __init__(self, crystallization_service: CrystallizationService):
        self.crystallization_service = crystallization_service

    async def distill_for_transfer(
        self,
        environment: Environment,
        pattern_id: str,
        target_sensitivity: SensitivityClassification,
        target_abstraction: AbstractionLevel,
        trace_id: Optional[str] = None
    ) -> TransferCandidate:
        """
        Distill a pattern for transfer, applying appropriate abstractions.
        """
        # In a real system, this would involve LLM-based distillation
        # to meet the requested sensitivity and abstraction levels.
        
        # Guard: Check if source environment allows this sensitivity level
        if SENSITIVITY_RANK[target_sensitivity] > SENSITIVITY_RANK[environment.max_sensitivity]:
            raise ValueError(f"Requested sensitivity {target_sensitivity} exceeds source environment max {environment.max_sensitivity}")

        # Create the candidate envelope
        candidate = TransferCandidate(
            id=str(uuid.uuid4()),
            source_environment_id=environment.id,
            pattern_id=pattern_id,
            sensitivity=target_sensitivity,
            abstraction_level=target_abstraction,
            trace_id=trace_id,
            created_at=datetime.utcnow(),
            status="proposed"
        )
        
        return candidate

    async def validate_eligibility(
        self,
        candidate: TransferCandidate,
        target_environment: Environment
    ) -> bool:
        """
        Check if a candidate is eligible for transfer to the target environment.
        """
        # Guard: Sensitivity check
        if SENSITIVITY_RANK[candidate.sensitivity] > SENSITIVITY_RANK[target_environment.max_sensitivity]:
            return False
        
        # Guard: Abstraction level check
        if candidate.abstraction_level not in target_environment.allowed_abstraction_levels:
            return False
            
        return True

    async def authorize_transfer(
        self,
        candidate: TransferCandidate,
        target_environment: Environment
    ) -> TransferCandidate:
        """
        Authorize a candidate for transfer, updating its status.
        """
        if not await self.validate_eligibility(candidate, target_environment):
            candidate.status = "rejected"
            return candidate
            
        candidate.target_environment_id = target_environment.id
        candidate.status = "authorized"
        return candidate
