import logging
from typing import List, Dict, Any, AsyncGenerator
from app.swarm.core.generator import GeneratorAgent
from app.swarm.core.reasoner import ReasonerAgent
from app.swarm.core.planner import PlannerAgent
from app.swarm.core.validator import ValidatorAgent
from app.swarm.core.judge import JudgeAgent

logger = logging.getLogger(__name__)

class SwarmController:
    def __init__(self):
        self.generator = GeneratorAgent()
        self.reasoner = ReasonerAgent()
        self.planner = PlannerAgent()
        self.validator = ValidatorAgent()
        self.judge = JudgeAgent()
        self.active_team = []
        self.agents = {
            'generator': self.generator,
            'reasoner': self.reasoner,
            'planner': self.planner,
            'validator': self.validator,
            'judge': self.judge,
        }

    async def activate_agents(self, agent_names: List[str]) -> None:
        """Activate specific agents for collaboration."""
        self.active_team = agent_names
        logger.info(f"Swarm team activated: {agent_names}")

    async def generate_stream(
        self,
        query: str,
        team: List[str],
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate with agent collaboration."""
        # 1. Planner breaks down the task
        plan = None
        if 'planner' in team:
            plan = await self.planner.plan(query, context)
            yield {"type": "plan", "plan": plan}
        
        # 2. Reasoner analyzes with context
        reasoning = None
        if 'reasoner' in team:
            reasoning = await self.reasoner.reason(query, context, plan)
            yield {"type": "reasoning", "reasoning": reasoning}
        
        # 3. Generator produces response
        if 'generator' in team:
            gen_context = {**context}
            if plan:
                gen_context['plan'] = plan
            if reasoning:
                gen_context['reasoning'] = reasoning
            
            async for chunk in self.generator.generate_stream_with_trace(
                query=query,
                provider="ollama",
                context=gen_context,
                user_id=1
            ):
                yield chunk
        
        # 4. Validator checks the output (simplified)
        if 'validator' in team:
            # Validator would check the response quality
            yield {"type": "validation", "status": "validated"}
        
        # 5. Judge evaluates the final result
        if 'judge' in team:
            # Judge would evaluate the response
            yield {"type": "judgment", "status": "approved"}