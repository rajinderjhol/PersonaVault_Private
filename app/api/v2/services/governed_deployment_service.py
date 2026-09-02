from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import uuid
import logging
from enum import Enum
from dataclasses import dataclass, field

from app.api.v2.services.proposal_service import Proposal, ProposalStatus
from app.api.v2.services.validation_service import ValidationResult, ValidationStatus
from app.api.v2.services.performance_evaluation_service import PerformanceEvaluationService
from app.services.audit.audit_service import AuditService

logger = logging.getLogger(__name__)

class DeploymentStatus(str, Enum):
    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    PARTIALLY_DEPLOYED = "partially_deployed"
    SUPERSEDED = "superseded"

class DeploymentRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Deployment:
    """Record of a deployment."""
    id: str
    proposal_id: str
    environment_id: str
    status: DeploymentStatus
    risk_level: DeploymentRisk
    deployed_by: str
    deployed_at: datetime
    completed_at: Optional[datetime] = None
    rollback_at: Optional[datetime] = None
    rollback_reason: Optional[str] = None
    validation_id: Optional[str] = None
    parameters_changed: List[Dict[str, Any]] = field(default_factory=list)
    metrics_before: Dict[str, float] = field(default_factory=dict)
    metrics_after: Dict[str, float] = field(default_factory=dict)
    error_details: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert deployment to dictionary."""
        return {
            "id": self.id,
            "proposal_id": self.proposal_id,
            "environment_id": self.environment_id,
            "status": self.status.value,
            "risk_level": self.risk_level.value,
            "deployed_by": self.deployed_by,
            "deployed_at": self.deployed_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "rollback_at": self.rollback_at.isoformat() if self.rollback_at else None,
            "rollback_reason": self.rollback_reason,
            "validation_id": self.validation_id,
            "parameters_changed": self.parameters_changed,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after,
            "error_details": self.error_details
        }

class GovernedDeploymentService:
    """
    Manages secure, audited, and rollback-capable deployments.
    
    This is the final component of V2.4 Adaptive Learning.
    """
    
    def __init__(
        self,
        performance_service: PerformanceEvaluationService,
        audit_service: AuditService
    ):
        self.performance_service = performance_service
        self.audit_service = audit_service
        self._deployments: Dict[str, Deployment] = {}
        self._deployment_history: List[Deployment] = []
        self._current_state: Dict[str, Dict[str, Any]] = {}  # environment_id -> current parameters
    
    async def deploy_proposal(
        self,
        proposal: Proposal,
        validation: Optional[ValidationResult],
        deployed_by: str
    ) -> Deployment:
        """
        Deploy a validated proposal.
        """
        # Create deployment record
        deployment = Deployment(
            id=str(uuid.uuid4()),
            proposal_id=proposal.id,
            environment_id=proposal.environment_id,
            status=DeploymentStatus.PENDING,
            risk_level=self._assess_deployment_risk(proposal),
            deployed_by=deployed_by,
            deployed_at=datetime.utcnow(),
            validation_id=validation.id if validation else None,
            parameters_changed=[{
                "parameter": proposal.parameter,
                "old_value": proposal.current_value,
                "new_value": proposal.proposed_value
            }]
        )
        
        # Check if deployment is allowed
        if not await self._check_deployment_allowed(proposal, deployment):
            deployment.status = DeploymentStatus.FAILED
            deployment.error_details = "Deployment blocked by governance policy"
            self._record_deployment(deployment)
            return deployment
        
        # Get current state before deployment
        try:
            baseline_data = await self.performance_service.get_performance_metrics(days=7)
            deployment.metrics_before = baseline_data.get("metrics", {})
        except Exception as e:
            logger.warning(f"Could not get metrics before deployment: {e}")
            deployment.metrics_before = {}
        
        # Apply the change
        deployment.status = DeploymentStatus.DEPLOYING
        try:
            result = await self._apply_parameter_change(
                environment_id=proposal.environment_id,
                parameter=proposal.parameter,
                new_value=proposal.proposed_value,
                deployment=deployment
            )
            
            if result.get("status") == "success":
                deployment.status = DeploymentStatus.DEPLOYED
                deployment.completed_at = datetime.utcnow()
                
                # Update current state
                self._update_current_state(
                    environment_id=proposal.environment_id,
                    parameter=proposal.parameter,
                    value=proposal.proposed_value
                )
                
                # Record success in audit
                await self.audit_service.log_event(
                    event_type="deployment",
                    environment_id=proposal.environment_id,
                    actor=deployed_by,
                    details={
                        "action": "deploy_proposal",
                        "proposal_id": proposal.id,
                        "parameter": proposal.parameter,
                        "old_value": proposal.current_value,
                        "new_value": proposal.proposed_value
                    }
                )
                
                # Get metrics after deployment
                try:
                    after_data = await self.performance_service.get_performance_metrics(days=1)
                    deployment.metrics_after = after_data.get("metrics", {})
                except Exception as e:
                    logger.warning(f"Could not get metrics after deployment: {e}")
                    deployment.metrics_after = {}
                
                # Update proposal status
                proposal.status = ProposalStatus.DEPLOYED
                proposal.deployed_at = deployment.deployed_at
                
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_details = result.get("error", "Unknown error")
                
        except Exception as e:
            logger.error(f"Deployment failed for proposal {proposal.id}: {e}")
            deployment.status = DeploymentStatus.FAILED
            deployment.error_details = str(e)
            deployment.completed_at = datetime.utcnow()
            
            # Attempt automatic rollback
            await self._attempt_automatic_rollback(deployment)
        
        self._record_deployment(deployment)
        return deployment
    
    async def rollback_deployment(
        self,
        deployment_id: str,
        reason: str,
        rolled_by: str
    ) -> Deployment:
        """
        Rollback a deployment.
        """
        deployment = self._deployments.get(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        if deployment.status not in [DeploymentStatus.DEPLOYED, DeploymentStatus.PARTIALLY_DEPLOYED]:
            raise ValueError(f"Deployment {deployment_id} cannot be rolled back (status: {deployment.status})")
        
        deployment.status = DeploymentStatus.ROLLING_BACK
        
        try:
            # Rollback each parameter
            for change in deployment.parameters_changed:
                await self._apply_parameter_change(
                    environment_id=deployment.environment_id,
                    parameter=change["parameter"],
                    new_value=change["old_value"],
                    deployment=deployment,
                    is_rollback=True
                )
            
            deployment.status = DeploymentStatus.ROLLED_BACK
            deployment.rollback_at = datetime.utcnow()
            deployment.rollback_reason = reason
            
            # Update current state
            for change in deployment.parameters_changed:
                self._update_current_state(
                    environment_id=deployment.environment_id,
                    parameter=change["parameter"],
                    value=change["old_value"]
                )
            
            # Record rollback in audit
            await self.audit_service.log_event(
                event_type="rollback",
                environment_id=deployment.environment_id,
                actor=rolled_by,
                details={
                    "action": "rollback_deployment",
                    "deployment_id": deployment_id,
                    "reason": reason,
                    "parameters": deployment.parameters_changed
                }
            )
            
        except Exception as e:
            logger.error(f"Rollback failed for deployment {deployment_id}: {e}")
            deployment.status = DeploymentStatus.FAILED
            deployment.error_details = f"Rollback failed: {str(e)}"
        
        return deployment
    
    async def _check_deployment_allowed(
        self,
        proposal: Proposal,
        deployment: Deployment
    ) -> bool:
        """Check if a deployment is allowed by governance policy."""
        if deployment.risk_level == DeploymentRisk.CRITICAL:
            return False  # Would require explicit approval
        return True
    
    async def _apply_parameter_change(
        self,
        environment_id: str,
        parameter: str,
        new_value: Any,
        deployment: Deployment,
        is_rollback: bool = False
    ) -> Dict[str, Any]:
        """Apply a parameter change."""
        # Simulated success
        logger.info(f"{'Rolling back' if is_rollback else 'Deploying'} {parameter} to {new_value} in environment {environment_id}")
        return {"status": "success", "parameter": parameter, "value": new_value}
    
    async def _attempt_automatic_rollback(self, deployment: Deployment) -> None:
        """Attempt to automatically rollback a failed deployment."""
        if deployment.parameters_changed:
            try:
                await self.rollback_deployment(
                    deployment_id=deployment.id,
                    reason="Automatic rollback due to deployment failure",
                    rolled_by="system"
                )
            except Exception as e:
                logger.error(f"Automatic rollback failed for deployment {deployment.id}: {e}")
    
    def _assess_deployment_risk(self, proposal: Proposal) -> DeploymentRisk:
        """Assess the risk level of a deployment."""
        if proposal.risk_level == "high":
            return DeploymentRisk.HIGH
        elif proposal.risk_level == "medium":
            return DeploymentRisk.MEDIUM
        return DeploymentRisk.LOW
    
    def _update_current_state(
        self,
        environment_id: str,
        parameter: str,
        value: Any
    ) -> None:
        """Update the current state of a parameter."""
        if environment_id not in self._current_state:
            self._current_state[environment_id] = {}
        self._current_state[environment_id][parameter] = value
    
    def _record_deployment(self, deployment: Deployment) -> None:
        """Record a deployment in the history."""
        self._deployments[deployment.id] = deployment
        self._deployment_history.append(deployment)
