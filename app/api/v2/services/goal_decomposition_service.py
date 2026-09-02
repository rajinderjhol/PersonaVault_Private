from typing import List, Optional, Dict, Any
from app.api.v2.models.environment import Environment
from app.api.v2.models.goal import Goal, GoalStatus
# Assuming a GoalService exists or will be created/mocked as needed based on context
# I will proceed with the assumption of a generic goal_service interface
# from app.api.v2.services.goal_service import GoalService
from app.swarm.specialized.knowledge_agent import KnowledgeAgent
from app.swarm.specialized.prediction_agent import PredictionAgent

class GoalDecompositionService:
    """
    Decomposes complex goals into sub-goals and identifies dependencies.
    """
    
    def __init__(
        self,
        goal_service, # Using generic until service is fully defined
        knowledge_agent: KnowledgeAgent,
        prediction_agent: PredictionAgent
    ):
        self.goal_service = goal_service
        self.knowledge_agent = knowledge_agent
        self.prediction_agent = prediction_agent
    
    async def decompose_goal(
        self,
        environment: Environment,
        goal_statement: str,
        context: Dict[str, Any],
        max_sub_goals: int = 5
    ) -> Goal:
        """
        Decompose a complex goal into manageable sub-goals.
        
        Args:
            environment: The environment context
            goal_statement: The goal to decompose
            context: Additional context for decomposition
            max_sub_goals: Maximum number of sub-goals to create
            
        Returns:
            The parent goal with sub-goals attached
        """
        # 1. Create the parent goal
        parent_goal = await self.goal_service.create_goal(
            environment_id=environment.id,
            statement=goal_statement,
            description=context.get("description"),
            priority=1,
            status=GoalStatus.PROPOSED,
            owner_principal_id=context.get("principal_id")
        )
        
        # 2. Retrieve relevant knowledge
        knowledge = await self.knowledge_agent.retrieve_relevant(
            environment=environment,
            query=goal_statement
        )
        
        # 3. Generate sub-goals
        sub_goal_statements = await self._generate_sub_goals(
            environment=environment,
            goal_statement=goal_statement,
            knowledge=knowledge,
            max_sub_goals=max_sub_goals
        )
        
        # 4. Create sub-goals
        sub_goals = []
        for i, sub_statement in enumerate(sub_goal_statements):
            sub_goal = await self.goal_service.create_goal(
                environment_id=environment.id,
                statement=sub_statement,
                description=f"Sub-goal {i+1} of: {goal_statement}",
                parent_goal_id=parent_goal.id,
                priority=i + 1,
                status=GoalStatus.PROPOSED
            )
            sub_goals.append(sub_goal)
        
        # 5. Identify dependencies
        dependencies = await self._identify_dependencies(
            environment=environment,
            sub_goals=sub_goals,
            knowledge=knowledge
        )
        
        # 6. Update parent goal with sub-goals
        parent_goal.sub_goals = [g.id for g in sub_goals]
        await self.goal_service.update_goal(parent_goal)
        
        # 7. Store dependency information
        for dep in dependencies:
            await self.goal_service.add_dependency(
                goal_id=dep["goal_id"],
                depends_on_id=dep["depends_on_id"]
            )
        
        return parent_goal
    
    async def _generate_sub_goals(
        self,
        environment: Environment,
        goal_statement: str,
        knowledge: List[Any],
        max_sub_goals: int
    ) -> List[str]:
        """
        Generate sub-goals using the PredictionAgent.
        """
        # Use PredictionAgent to generate sub-goals
        result = await self.prediction_agent.predict_outcome(
            environment=environment,
            scenario={
                "type": "goal_decomposition",
                "goal": goal_statement,
                "knowledge": [k.statement for k in knowledge[:10]],
                "max_sub_goals": max_sub_goals
            }
        )
        
        # Extract sub-goal statements
        sub_goals = result.get("sub_goals", [])
        return sub_goals[:max_sub_goals]
    
    async def _identify_dependencies(
        self,
        environment: Environment,
        sub_goals: List[Goal],
        knowledge: List[Any]
    ) -> List[Dict[str, str]]:
        """
        Identify dependencies between sub-goals.
        """
        dependencies = []
        
        # Analyze each pair of sub-goals
        for i, goal_a in enumerate(sub_goals):
            for j, goal_b in enumerate(sub_goals):
                if i == j:
                    continue
                
                # Check if goal_a depends on goal_b
                if await self._check_dependency(
                    environment=environment,
                    goal_a=goal_a,
                    goal_b=goal_b,
                    knowledge=knowledge
                ):
                    dependencies.append({
                        "goal_id": goal_a.id,
                        "depends_on_id": goal_b.id
                    })
        
        return dependencies
    
    async def _check_dependency(
        self,
        environment: Environment,
        goal_a: Goal,
        goal_b: Goal,
        knowledge: List[Any]
    ) -> bool:
        """
        Check if goal_a depends on goal_b.
        """
        # Use PredictionAgent to check dependency
        result = await self.prediction_agent.predict_outcome(
            environment=environment,
            scenario={
                "type": "dependency_check",
                "goal_a": goal_a.statement,
                "goal_b": goal_b.statement,
                "knowledge": [k.statement for k in knowledge[:10]]
            }
        )
        
        return result.get("depends_on", False)
    
    async def prioritize_sub_goals(
        self,
        sub_goals: List[Goal]
    ) -> List[Goal]:
        """
        Prioritize sub-goals based on dependencies and urgency.
        """
        # Sort by priority (lower number = higher priority)
        return sorted(sub_goals, key=lambda g: g.priority)
    
    async def get_decomposition_tree(
        self,
        goal: Goal
    ) -> Dict[str, Any]:
        """
        Get the full decomposition tree for a goal.
        """
        tree = {
            "id": goal.id,
            "statement": goal.statement,
            "status": goal.status,
            "sub_goals": []
        }
        
        for sub_id in goal.sub_goals:
            sub_goal = await self.goal_service.get_goal(sub_id)
            if sub_goal:
                tree["sub_goals"].append(
                    await self.get_decomposition_tree(sub_goal)
                )
        
        return tree
