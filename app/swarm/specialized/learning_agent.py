from typing import Dict, Any, Optional
from app.swarm.base import BaseAgent
from app.swarm.context import AgentEnvironmentContext
from app.api.v2.models.outcome import Outcome

class LearningAgent(BaseAgent):
    """
    Universal Learning Agent: Closes the loop: identifies patterns, triggers crystallization.
    """
    def __init__(self, name: str = "LearningAgent"):
        super().__init__(name)
    
    async def learn(self, context: AgentEnvironmentContext, outcome: Outcome) -> Optional[str]:
        # Uses the crystallization service via context
        return await context.learn_pattern({
            "content": str(outcome.result),
            "confidence": outcome.metrics.get("confidence", 0.8) if outcome.metrics else 0.8
        })
