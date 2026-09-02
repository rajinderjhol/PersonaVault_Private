import logging
from typing import Optional, List
from app.api.v2.models.environment import Environment
from app.api.v2.models.transfer import TransferCandidate, SensitivityClassification, AbstractionLevel
from app.api.v2.models.provenance import ProvenanceRef
from app.api.v2.services.transfer_service import TransferService
from app.api.v2.services.crystallization_service import CrystallizationService
from app.api.v2.services.commerce_service import CommerceService, PaymentStatus

logger = logging.getLogger(__name__)

class TransferCoordinator:
    def __init__(
        self, 
        transfer_service: TransferService, 
        crystallization_service: CrystallizationService,
        commerce_service: Optional[CommerceService] = None
    ):
        self.transfer_service = transfer_service
        self.crystallization_service = crystallization_service
        self.commerce_service = commerce_service or CommerceService()

    async def execute_transfer_lifecycle(
        self,
        source_env: Environment,
        target_env: Environment,
        pattern_id: str,
        sensitivity: SensitivityClassification,
        abstraction: AbstractionLevel,
        trace_id: Optional[str] = None
    ) -> TransferCandidate:
        """
        Orchestrate the full transfer lifecycle: Initiate -> Govern -> Validate -> Promote.
        """
        logger.info(f"🚀 Initiating transfer lifecycle for pattern {pattern_id} from {source_env.id} to {target_env.id} [Trace: {trace_id}]")
        
        # 1. Initiate (Distillation)
        candidate = await self.transfer_service.distill_for_transfer(
            source_env, pattern_id, sensitivity, abstraction, trace_id=trace_id
        )
        
        # 2. Govern (Sensitivity & Abstraction guards)
        candidate = await self.transfer_service.authorize_transfer(candidate, target_env)
        if candidate.status == "rejected":
            logger.warning(f"🛡️ Transfer REJECTED by governance: {candidate.id} (env {target_env.id})")
            return candidate

        # 3. Validate (Provenance Integrity)
        # Ensure the provenance chain is present and starts with the source
        if not candidate.provenance_chain:
            candidate.provenance_chain.append(
                ProvenanceRef(source_type="environment", source_id=source_env.id)
            )
        
        # 4. Commerce Hook (Priority 5: x402 integration)
        # Trigger x402 payment flow for the target environment's owner
        logger.info(f"💳 Requesting x402 payment for transfer {candidate.id}")
        tx = await self.commerce_service.initiate_payment(
            principal_id=target_env.owner_principal_id,
            asset_id=candidate.pattern_id
        )
        
        # In this demo, we verify settlement immediately
        settled = await self.commerce_service.verify_settlement(tx.id)
        if not settled:
            logger.error(f"❌ Transfer FAILED: x402 payment settlement failed for {tx.id}")
            candidate.status = "rejected"
            return candidate
            
        candidate.status = "authorized"
        logger.info(f"✅ x402 Payment SETTLED for transfer {candidate.id}")

        # 5. Promote (Finalize Transfer)
        try:
            # Retrieve the distilled content (using the pattern_id from candidate)
            # Enforce source environment isolation
            pattern = await self.crystallization_service.get_pattern(
                candidate.pattern_id, 
                environment_id=source_env.id
            )
            if not pattern:
                logger.error(f"❌ Transfer FAILED: Pattern {candidate.pattern_id} not found in source {source_env.id}")
                candidate.status = "rejected"
                return candidate
                
            # Store in target environment
            new_pattern_id = await self.crystallization_service.crystallize_pattern(
                environment=target_env,
                pattern_data={
                    "content": pattern["content"],
                    "tags": pattern["metadata"].get("tags", []) + ["transferred"],
                    "title": f"Transferred: {pattern['metadata'].get('title', 'Pattern')}"
                }
            )
            
            candidate.status = "transferred"
            logger.info(f"✅ Transfer COMPLETED: {candidate.id} -> new pattern {new_pattern_id} in {target_env.id}")
            return candidate
        except Exception as e:
            logger.error(f"❌ Transfer FAILED due to system error: {e}")
            candidate.status = "rejected"
            return candidate
