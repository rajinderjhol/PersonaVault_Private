from typing import Dict, Any, List, Optional
from app.swarm.base import BaseAgent
from app.swarm.context import AgentEnvironmentContext
from app.api.v2.models.decision import Decision

class DecisionAgent(BaseAgent):
    """
    Universal Decision Agent: Selects an option under constraints.
    """
    def __init__(self, name: str = "DecisionAgent"):
        super().__init__(name)
    
    async def decide(
        self,
        context: AgentEnvironmentContext,
        options: List[Dict[str, Any]]
    ) -> Decision:
        # Authority check
        if not await context.check_authority("make_decision"):
            return Decision(
                id="null", environment_id=context.environment.id,
                decision="Rejected: No Authority",
                decided_by=self.name,
                status="rejected",
                policy_ids=[],
                trace_id="none"
            )
        # Decision logic
        return Decision(
            id="dec_123", environment_id=context.environment.id,
            decision="Selected Option A",
            decided_by=self.name,
            status="approved",
            policy_ids=[],
            trace_id="trace_123"
        )
