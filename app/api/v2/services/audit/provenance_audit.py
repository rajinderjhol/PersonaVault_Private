from typing import Dict, Any, List
from app.api.v2.models.reasoning_chain import ReasoningChain
from app.api.v2.services.reasoning_engine import ReasoningEngine # Placeholder, need to ensure access to storage

class ProvenanceAudit:
    def __init__(self, reasoning_repository):
        self.reasoning_repository = reasoning_repository
    
    async def audit_reasoning_chain(self, chain_id: str) -> Dict[str, Any]:
        """Audit a reasoning chain for provenance integrity."""
        # Retrieve the chain from the repository
        chain = await self.reasoning_repository.get_reasoning_chain(chain_id)
        if not chain:
            return {"chain_id": chain_id, "status": "failed", "issues": ["Chain not found"]}
            
        issues = []
        
        # Check trace completeness
        for step in chain.steps:
            # Assuming step has trace_id and evidence fields
            if not getattr(step, 'trace_id', None):
                issues.append(f"Step {step.step_id} missing trace_id")
            if not step.evidence:
                issues.append(f"Step {step.step_id} missing evidence")
        
        # Check confidence propagation
        last_confidence = 1.0
        for step in chain.steps:
            if step.confidence > last_confidence + 0.1:
                issues.append(f"Confidence increase without evidence: {step.step_id}")
            last_confidence = step.confidence
        
        return {
            "chain_id": chain_id,
            "status": "passed" if not issues else "failed",
            "issues": issues,
            "step_count": len(chain.steps),
            "confidence_trail": [s.confidence for s in chain.steps]
        }
