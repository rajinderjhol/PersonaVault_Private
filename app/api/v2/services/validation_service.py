from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid
import logging
from enum import Enum
from dataclasses import dataclass

from app.api.v2.services.performance_evaluation_service import PerformanceEvaluationService
from app.api.v2.services.proposal_service import Proposal, ProposalStatus
from app.swarm.specialized.simulation_agent import SimulationAgent
from app.swarm.specialized.prediction_agent import PredictionAgent

logger = logging.getLogger(__name__)

class ValidationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    HUMAN_REVIEW_REQUIRED = "human_review_required"

@dataclass
class ValidationResult:
    """Result of a validation run."""
    id: str
    proposal_id: str
    environment_id: str
    status: ValidationStatus
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    improvement: float
    threshold: float
    is_approved: bool
    details: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None
    reviewer_comments: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            "id": self.id,
            "proposal_id": self.proposal_id,
            "environment_id": self.environment_id,
            "status": self.status.value,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after,
            "improvement": self.improvement,
            "threshold": self.threshold,
            "is_approved": self.is_approved,
            "details": self.details,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "reviewer_comments": self.reviewer_comments
        }

class ValidationService:
    """
    Validates proposed changes before deployment.
    
    This service simulates the impact of changes and determines
    whether they should be approved for deployment.
    """
    
    def __init__(
        self,
        performance_service: PerformanceEvaluationService,
        simulation_agent: SimulationAgent,
        prediction_agent: PredictionAgent
    ):
        self.performance_service = performance_service
        self.simulation_agent = simulation_agent
        self.prediction_agent = prediction_agent
        self._validation_results: Dict[str, ValidationResult] = {}
        self._validation_history: List[ValidationResult] = []
    
    async def validate_proposal(
        self,
        proposal: Proposal,
        test_days: int = 7,
        threshold: float = 0.05  # 5% minimum improvement
    ) -> ValidationResult:
        """
        Validate a proposal by simulating its impact.
        """
        validation_id = str(uuid.uuid4())
        
        result = ValidationResult(
            id=validation_id,
            proposal_id=proposal.id,
            environment_id=proposal.environment_id,
            status=ValidationStatus.RUNNING,
            metrics_before={},
            metrics_after={},
            improvement=0.0,
            threshold=threshold,
            is_approved=False,
            details={},
            created_at=datetime.utcnow()
        )
        
        try:
            # Step 1: Get baseline metrics
            logger.info(f"Validating proposal {proposal.id}: Getting baseline metrics")
            baseline_data = await self.performance_service.get_performance_metrics(days=test_days)
            baseline_metrics = baseline_data.get("metrics", {})
            result.metrics_before = baseline_metrics
            
            # Step 2: Simulate the impact of the change
            logger.info(f"Validating proposal {proposal.id}: Simulating impact")
            simulated_metrics = await self._simulate_impact(
                environment_id=proposal.environment_id,
                parameter=proposal.parameter,
                proposed_value=proposal.proposed_value,
                baseline_metrics=baseline_metrics
            )
            result.metrics_after = simulated_metrics
            
            # Step 3: Calculate improvement
            baseline_quality = baseline_metrics.get("pattern_accuracy", 0.0)
            simulated_quality = simulated_metrics.get("pattern_accuracy", 0.0)
            improvement = simulated_quality - baseline_quality
            result.improvement = improvement
            
            # Step 4: Determine if the proposal passes
            result.is_approved = improvement >= threshold
            result.status = ValidationStatus.PASSED if result.is_approved else ValidationStatus.FAILED
            
            # Step 5: Generate detailed validation report
            result.details = await self._generate_validation_details(
                proposal=proposal,
                baseline_metrics=baseline_metrics,
                simulated_metrics=simulated_metrics,
                improvement=improvement
            )
            
            # Step 6: Generate human review requirement
            if result.is_approved and self._requires_human_review(proposal, improvement):
                result.status = ValidationStatus.HUMAN_REVIEW_REQUIRED
                result.details["human_review_required"] = True
            
        except Exception as e:
            logger.error(f"Validation failed for proposal {proposal.id}: {e}")
            result.status = ValidationStatus.ERROR
            result.details["error"] = str(e)
        
        result.completed_at = datetime.utcnow()
        self._validation_results[validation_id] = result
        self._validation_history.append(result)
        
        return result
    
    async def _simulate_impact(
        self,
        environment_id: str,
        parameter: str,
        proposed_value: Any,
        baseline_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Simulate the impact of a parameter change.
        """
        scenario = {
            "type": "parameter_change_simulation",
            "environment_id": environment_id,
            "parameter": parameter,
            "proposed_value": proposed_value,
            "baseline_metrics": baseline_metrics
        }
        
        # Run simulation
        simulation_result = await self.simulation_agent.simulate(
            context=None,
            scenario=scenario
        )
        
        simulated_metrics = simulation_result.get("metrics", {})
        
        if not simulated_metrics:
            prediction = await self.prediction_agent.predict_outcome(
                environment=environment_id,
                scenario=scenario
            )
            simulated_metrics = prediction.get("metrics", {})
        
        return simulated_metrics
    
    async def _generate_validation_details(
        self,
        proposal: Proposal,
        baseline_metrics: Dict[str, float],
        simulated_metrics: Dict[str, float],
        improvement: float
    ) -> Dict[str, Any]:
        """Generate detailed validation report."""
        details = {
            "parameter": proposal.parameter,
            "current_value": proposal.current_value,
            "proposed_value": proposal.proposed_value,
            "improvement": improvement,
            "metrics_compared": {}
        }
        
        # Compare all metrics
        all_metrics = set(baseline_metrics.keys()) | set(simulated_metrics.keys())
        for metric in all_metrics:
            before = baseline_metrics.get(metric, 0.0)
            after = simulated_metrics.get(metric, 0.0)
            diff = after - before
            details["metrics_compared"][metric] = {
                "before": before,
                "after": after,
                "change": diff,
                "change_percent": (diff / before * 100) if before != 0 else 0
            }
        
        return details
    
    def _requires_human_review(
        self,
        proposal: Proposal,
        improvement: float
    ) -> bool:
        """Determine if a proposal requires human review."""
        if proposal.risk_level == "high":
            return True
        if improvement > 0.5: return True
        if improvement < 0.01: return True
        if proposal.parameter in ["confidence_threshold", "crystallization_trigger"]:
            return True
        return False
    
    async def get_validation_result(self, validation_id: str) -> Optional[ValidationResult]:
        return self._validation_results.get(validation_id)
