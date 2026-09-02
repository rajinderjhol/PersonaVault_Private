from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

from app.api.v2.services.performance_evaluation_service import PerformanceEvaluationService
from app.services.crystallization_service import CrystallizationService
from app.services.predictive_intelligence import PredictiveIntelligenceService 
from app.api.v2.services.proposal_service import ProposalService, Proposal
from app.api.v2.models.knowledge_gap import KnowledgeGap
from app.config import Config as settings

logger = logging.getLogger(__name__)

@dataclass
class OptimizationProposal:
    """Represents a proposed optimization to the system."""
    parameter: str
    current_value: Any
    proposed_value: Any
    rationale: str
    expected_improvement: float
    risk: str  # low, medium, high
    validation_required: bool = True

@dataclass
class OptimizationResult:
    """Result of applying an optimization."""
    parameter: str
    old_value: Any
    new_value: Any
    status: str  # applied, rejected, pending_validation
    metrics_before: Dict[str, float]
    metrics_after: Optional[Dict[str, float]] = None

class AlgorithmOptimizationService:
    """
    Dynamically adjusts system parameters based on performance metrics.
    
    This is the core of V2.4 Adaptive Learning.
    """
    
    def __init__(
        self,
        performance_service: PerformanceEvaluationService,
        crystallization_service: CrystallizationService,
        prediction_service: PredictiveIntelligenceService,
        proposal_service: ProposalService
    ):
        self.performance_service = performance_service
        self.crystallization_service = crystallization_service
        self.prediction_service = prediction_service
        self.proposal_service = proposal_service
        self._optimization_history: List[OptimizationResult] = []
        self._proposals: List[OptimizationProposal] = []
        # In-memory storage for parameters
        self._params = {
            "confidence_threshold": 0.7,
            "calibration_factor": 1.0,
            "retrieval_threshold": 0.5
        }
    
    async def get_parameter(self, environment_id: str, parameter: str) -> Any:
        return self._params.get(parameter)
    
    async def propose_optimization(
        self,
        environment_id: str,
        optimization: OptimizationProposal
    ) -> Proposal:
        """
        Propose an optimization through the proposal service.
        """
        return await self.proposal_service.create_proposal(
            environment_id=environment_id,
            optimization=optimization,
            created_by="system"
        )
    
    async def apply_optimization_with_proposal(
        self,
        proposal_id: str,
        deployer_id: str
    ) -> OptimizationResult:
        """
        Apply an optimization that has been approved.
        """
        proposal = await self.proposal_service.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        
        # Deploy the proposal
        await self.proposal_service.deploy_proposal(
            proposal_id=proposal_id,
            deployer_id=deployer_id
        )
        
        # Apply the actual parameter change
        result = await self._apply_parameter_change(
            proposal.parameter,
            proposal.proposed_value
        )
        
        return OptimizationResult(
            parameter=proposal.parameter,
            old_value=proposal.current_value,
            new_value=proposal.proposed_value,
            status="applied",
            metrics_before={}
        )

    async def analyze_optimization_opportunities(
        self,
        environment_id: str,
        metrics: Dict[str, Any]
    ) -> List[OptimizationProposal]:
        """
        Analyze performance metrics and generate optimization proposals.
        """
        proposals = []
        
        # 1. Analyze crystallization thresholds
        if "crystallization" in metrics:
            crystallization_metrics = metrics["crystallization"]
            proposals.extend(
                await self._analyze_crystallization_parameters(
                    environment_id,
                    crystallization_metrics
                )
            )
        
        # 2. Analyze prediction parameters
        if "prediction" in metrics:
            prediction_metrics = metrics["prediction"]
            proposals.extend(
                await self._analyze_prediction_parameters(
                    environment_id,
                    prediction_metrics
                )
            )
        
        # 3. Analyze retrieval parameters
        if "retrieval" in metrics:
            retrieval_metrics = metrics["retrieval"]
            proposals.extend(
                await self._analyze_retrieval_parameters(
                    environment_id,
                    retrieval_metrics
                )
            )
        
        # Store proposals for later reference
        self._proposals.extend(proposals)
        logger.info(f"Generated {len(proposals)} optimization proposals for environment {environment_id}")
        
        return proposals
    
    async def _analyze_crystallization_parameters(
        self,
        environment_id: str,
        metrics: Dict[str, Any]
    ) -> List[OptimizationProposal]:
        """Analyze and propose optimizations for crystallization parameters."""
        proposals = []
        
        # Analyze confidence threshold
        current_threshold = self._params["confidence_threshold"]
        accuracy = metrics.get("pattern_accuracy", 0.0)
        noise_ratio = metrics.get("noise_ratio", 0.0)
        
        # If accuracy is high but noise ratio is also high, threshold might be too low
        if accuracy > 0.8 and noise_ratio > 0.2:
            new_threshold = min(current_threshold + 0.05, 0.95)
            proposals.append(OptimizationProposal(
                parameter="confidence_threshold",
                current_value=current_threshold,
                proposed_value=new_threshold,
                rationale="High accuracy with high noise suggests threshold is too low",
                expected_improvement=noise_ratio * 0.5,  # Expected noise reduction
                risk="medium",
                validation_required=True
            ))
        
        # If accuracy is low and noise is low, threshold might be too high
        if accuracy < 0.6 and noise_ratio < 0.1:
            new_threshold = max(current_threshold - 0.05, 0.5)
            proposals.append(OptimizationProposal(
                parameter="confidence_threshold",
                current_value=current_threshold,
                proposed_value=new_threshold,
                rationale="Low accuracy with low noise suggests threshold is too high",
                expected_improvement=0.15,  # Expected accuracy improvement
                risk="medium",
                validation_required=True
            ))
        
        return proposals
    
    async def _analyze_prediction_parameters(
        self,
        environment_id: str,
        metrics: Dict[str, Any]
    ) -> List[OptimizationProposal]:
        """Analyze and propose optimizations for prediction parameters."""
        proposals = []
        
        calibration_error = metrics.get("calibration_error", 0.0)
        accuracy = metrics.get("prediction_accuracy", 0.0)
        
        # If calibration error is high, adjust confidence calibration
        if calibration_error > 0.2:
            current_calibration = self._params["calibration_factor"]
            new_calibration = current_calibration * 1.1  # Simple adjustment
            proposals.append(OptimizationProposal(
                parameter="calibration_factor",
                current_value=current_calibration,
                proposed_value=new_calibration,
                rationale="High calibration error suggests predictions are miscalibrated",
                expected_improvement=0.1,
                risk="low",
                validation_required=True
            ))
        
        return proposals
    
    async def _analyze_retrieval_parameters(
        self,
        environment_id: str,
        metrics: Dict[str, Any]
    ) -> List[OptimizationProposal]:
        """Analyze and propose optimizations for retrieval parameters."""
        proposals = []
        
        hit_rate = metrics.get("retrieval_hit_rate", 0.0)
        relevance_score = metrics.get("avg_relevance", 0.0)
        
        # If hit rate is low, adjust retrieval threshold
        if hit_rate < 0.5 and relevance_score > 0.7:
            current_threshold = self._params["retrieval_threshold"]
            new_threshold = max(current_threshold - 0.05, 0.3)
            proposals.append(OptimizationProposal(
                parameter="retrieval_threshold",
                current_value=current_threshold,
                proposed_value=new_threshold,
                rationale="Low hit rate with high relevance suggests threshold is too high",
                expected_improvement=0.15,  # Expected hit rate improvement
                risk="low",
                validation_required=True
            ))
        
        return proposals
    
    async def apply_optimization(
        self,
        environment_id: str,
        proposal: OptimizationProposal
    ) -> OptimizationResult:
        """
        Apply a single optimization proposal.
        """
        old_value = proposal.current_value
        new_value = proposal.proposed_value
        
        if proposal.validation_required:
            validation_result = await self._validate_optimization(
                environment_id,
                proposal
            )
            
            if validation_result["approved"]:
                result = await self._apply_parameter_change(
                    proposal.parameter,
                    new_value
                )
                status = "applied"
            else:
                status = "rejected"
        else:
            result = await self._apply_parameter_change(
                proposal.parameter,
                new_value
            )
            status = "applied"
        
        return OptimizationResult(
            parameter=proposal.parameter,
            old_value=old_value,
            new_value=new_value,
            status=status,
            metrics_before={} # placeholder
        )
    
    async def _validate_optimization(
        self,
        environment_id: str,
        proposal: OptimizationProposal
    ) -> Dict[str, Any]:
        """Validate an optimization proposal."""
        # Simple placeholder validation
        return {"approved": True}
    
    async def _apply_parameter_change(
        self,
        parameter: str,
        value: Any,
        sandbox: bool = False
    ) -> Dict[str, Any]:
        """Apply a parameter change."""
        self._params[parameter] = value
        logger.info(f"Applied {parameter} = {value}")
        return {"status": "applied", "parameter": parameter, "value": value}
