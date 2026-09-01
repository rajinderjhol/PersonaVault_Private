from typing import Dict, Any, Optional
from app.swarm.base import BaseAgent
from app.swarm.context import AgentEnvironmentContext
from app.api.v2.services.authority_service import AuthorityService

class GovernanceAgent(BaseAgent):
    """
    Universal Governance Agent: Enforces authority and policy boundaries.
    
    This agent is responsible for validating if a principal is authorized 
    to perform a specific action within a given environment context.
    """
    
    def __init__(self, name: str = "GovernanceAgent"):
        super().__init__(name)
    
    async def validate_action(
        self,
        context: AgentEnvironmentContext,
        capability: str,
        path: Optional[str] = None
    ) -> bool:
        """
        Validate if an action is allowed within the environment context.
        """
        if not context:
            return False
            
        return await context.check_authority(capability)
