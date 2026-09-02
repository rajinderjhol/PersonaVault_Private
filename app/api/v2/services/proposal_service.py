from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid
import logging

from app.api.v2.services.algorithm_optimization_service import OptimizationProposal
from app.api.v2.services.performance_evaluation_service import PerformanceEvaluationService
from app.core.config import Config as settings

logger = logging.getLogger(__name__)

class ProposalStatus(str, Enum):
    DRAFT = "draft"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"

class ProposalPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Proposal:
    """A formal improvement proposal."""
    id: str
    environment_id: str
    parameter: str
    current_value: Any
    proposed_value: Any
    rationale: str
    expected_improvement: float
    risk_level: str  # low, medium, high
    impact_analysis: Dict[str, Any]
    status: ProposalStatus
    priority: ProposalPriority
    created_by: str  # system, admin, etc.
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    deployed_at: Optional[datetime] = None
    validation_results: Optional[Dict[str, Any]] = None
    rollback_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert proposal to dictionary."""
        return {
            "id": self.id,
            "environment_id": self.environment_id,
            "parameter": self.parameter,
            "current_value": self.current_value,
            "proposed_value": self.proposed_value,
            "rationale": self.rationale,
            "expected_improvement": self.expected_improvement,
            "risk_level": self.risk_level,
            "impact_analysis": self.impact_analysis,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewed_by": self.reviewed_by,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "validation_results": self.validation_results,
            "rollback_reason": self.rollback_reason
        }

class ProposalService:
    """
    Manages the lifecycle of improvement proposals.
    
    This service translates optimization insights into structured,
    reviewable proposals that can be validated and deployed.
    """
    
    def __init__(
        self,
        performance_service: PerformanceEvaluationService
    ):
        self.performance_service = performance_service
        self._proposals: Dict[str, Proposal] = {}
        self._deployment_history: List[Dict[str, Any]] = []
    
    async def create_proposal(
        self,
        environment_id: str,
        optimization: OptimizationProposal,
        created_by: str = "system"
    ) -> Proposal:
        """
        Create a formal proposal from an optimization candidate.
        """
        # Validate the optimization
        if not self._validate_optimization(optimization):
            raise ValueError(f"Invalid optimization proposal: {optimization.parameter}")
        
        # Assess priority
        priority = self._assess_priority(optimization)
        
        # Determine risk level
        risk_level = self._assess_risk(optimization)
        
        # Generate impact analysis
        impact_analysis = await self._generate_impact_analysis(
            environment_id,
            optimization
        )
        
        # Create proposal
        proposal = Proposal(
            id=str(uuid.uuid4()),
            environment_id=environment_id,
            parameter=optimization.parameter,
            current_value=optimization.current_value,
            proposed_value=optimization.proposed_value,
            rationale=optimization.rationale,
            expected_improvement=optimization.expected_improvement,
            risk_level=risk_level,
            impact_analysis=impact_analysis,
            status=ProposalStatus.DRAFT,
            priority=priority,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        
        # Store proposal
        self._proposals[proposal.id] = proposal
        
        logger.info(f"Created proposal {proposal.id} for environment {environment_id}: {proposal.parameter}")
        return proposal
    
    async def review_proposal(
        self,
        proposal_id: str,
        reviewer_id: str,
        decision: str,  # approved or rejected
        review_notes: Optional[str] = None
    ) -> Proposal:
        """
        Review a proposal.
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        
        if decision not in ["approved", "rejected"]:
            raise ValueError("Decision must be 'approved' or 'rejected'")
        
        proposal.reviewed_at = datetime.utcnow()
        proposal.reviewed_by = reviewer_id
        
        if decision == "approved":
            proposal.status = ProposalStatus.APPROVED
            # Store review notes in validation_results
            proposal.validation_results = {"review_notes": review_notes, "decision": decision}
        else:
            proposal.status = ProposalStatus.REJECTED
            proposal.rollback_reason = review_notes or "Rejected during review"
        
        logger.info(f"Proposal {proposal_id} {decision} by {reviewer_id}")
        return proposal
    
    async def deploy_proposal(
        self,
        proposal_id: str,
        deployer_id: str
    ) -> Proposal:
        """
        Deploy an approved proposal.
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        
        if proposal.status != ProposalStatus.APPROVED:
            raise ValueError(f"Proposal {proposal_id} is not approved (status: {proposal.status})")
        
        # Apply the change
        try:
            # This would call the AlgorithmOptimizationService to apply the change
            proposal.status = ProposalStatus.DEPLOYED
            proposal.deployed_at = datetime.utcnow()
            
            # Record deployment
            self._deployment_history.append({
                "proposal_id": proposal.id,
                "parameter": proposal.parameter,
                "old_value": proposal.current_value,
                "new_value": proposal.proposed_value,
                "deployed_by": deployer_id,
                "deployed_at": proposal.deployed_at
            })
            
            logger.info(f"Deployed proposal {proposal_id} by {deployer_id}")
            
        except Exception as e:
            proposal.status = ProposalStatus.FAILED
            proposal.rollback_reason = str(e)
            logger.error(f"Failed to deploy proposal {proposal_id}: {e}")
        
        return proposal
    
    async def rollback_proposal(
        self,
        proposal_id: str,
        reason: str
    ) -> Proposal:
        """
        Rollback a deployed proposal.
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        
        if proposal.status != ProposalStatus.DEPLOYED:
            raise ValueError(f"Proposal {proposal_id} is not deployed (status: {proposal.status})")
        
        # Rollback the change
        try:
            # This would call the AlgorithmOptimizationService to revert the change
            proposal.status = ProposalStatus.ROLLED_BACK
            proposal.rollback_reason = reason
            
            logger.info(f"Rolled back proposal {proposal_id}: {reason}")
            
        except Exception as e:
            logger.error(f"Failed to rollback proposal {proposal_id}: {e}")
            raise
        
        return proposal
    
    async def get_proposal(
        self,
        proposal_id: str
    ) -> Optional[Proposal]:
        """Get a proposal by ID."""
        return self._proposals.get(proposal_id)
    
    def _validate_optimization(
        self,
        optimization: OptimizationProposal
    ) -> bool:
        """Validate an optimization proposal."""
        # Check that value changed
        if optimization.current_value == optimization.proposed_value:
            return False
        
        # Check that expected improvement is positive
        if optimization.expected_improvement <= 0:
            return False
        
        return True
    
    def _assess_priority(
        self,
        optimization: OptimizationProposal
    ) -> ProposalPriority:
        """Assess the priority of a proposal."""
        if optimization.expected_improvement > 0.5:
            return ProposalPriority.CRITICAL
        elif optimization.expected_improvement > 0.3:
            return ProposalPriority.HIGH
        elif optimization.expected_improvement > 0.1:
            return ProposalPriority.MEDIUM
        else:
            return ProposalPriority.LOW
    
    def _assess_risk(
        self,
        optimization: OptimizationProposal
    ) -> str:
        """Assess the risk level of a proposal."""
        return optimization.risk
    
    async def _generate_impact_analysis(
        self,
        environment_id: str,
        optimization: OptimizationProposal
    ) -> Dict[str, Any]:
        """Generate a detailed impact analysis for a proposal."""
        return {
            "estimated_improvement": optimization.expected_improvement,
            "affected_components": [optimization.parameter],
            "estimated_implementation_cost": "low",
            "estimated_rollback_cost": "medium"
        }
