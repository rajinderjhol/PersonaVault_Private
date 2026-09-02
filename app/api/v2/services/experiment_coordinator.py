from typing import List, Optional, Dict, Any
from app.api.v2.models.environment import Environment
from app.api.v2.models.hypothesis import Hypothesis, HypothesisStatus
from app.api.v2.models.experiment import Experiment, ExperimentStatus
from app.api.v2.models.experiment_observation import ExperimentObservation
from app.api.v2.models.knowledge_gap import KnowledgeGap
from app.api.v2.services.hypothesis_service import HypothesisService
from app.api.v2.services.experiment_service import ExperimentService
from app.api.v2.services.experiment_bridge import ExperimentBridge
from app.swarm.specialized.knowledge_agent import KnowledgeAgent
from app.swarm.specialized.prediction_agent import PredictionAgent
from app.swarm.specialized.simulation_agent import SimulationAgent
from app.swarm.context import AgentEnvironmentContext

class ExperimentCoordinator:
    """
    Orchestrates the Experimentation Loop:
    Knowledge Gap → Hypothesis → Experiment → Observation → Learning
    """
    
    def __init__(
        self,
        hypothesis_service: HypothesisService,
        experiment_service: ExperimentService,
        experiment_bridge: ExperimentBridge,
        knowledge_agent: KnowledgeAgent,
        prediction_agent: PredictionAgent,
        simulation_agent: SimulationAgent
    ):
        self.hypothesis_service = hypothesis_service
        self.experiment_service = experiment_service
        self.experiment_bridge = experiment_bridge
        self.knowledge_agent = knowledge_agent
        self.prediction_agent = prediction_agent
        self.simulation_agent = simulation_agent
    
    async def run_experimentation_cycle(
        self,
        context: AgentEnvironmentContext,
        max_hypotheses: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Execute one full iteration of the experimentation loop.
        
        Returns:
            List of results for each experiment run
        """
        results = []
        
        # 1. Identify knowledge gaps
        gaps = await self._identify_knowledge_gaps(context)
        if not gaps:
            return []
        
        # 2. Prioritize gaps
        prioritized_gaps = sorted(gaps, key=lambda g: g.importance, reverse=True)[:max_hypotheses]
        
        for gap in prioritized_gaps:
            # 3. Form hypothesis
            hypothesis = await self._form_hypothesis(context, gap)
            if not hypothesis:
                continue
            
            # 4. Design experiment
            experiment = await self._design_experiment(context, hypothesis)
            if not experiment:
                continue
            
            # 5. Run experiment
            observation = await self._run_experiment(context, experiment)
            if not observation:
                continue
            
            # 6. Learn from results
            learning_result = await self._learn_from_experiment(context, hypothesis, observation)
            
            results.append({
                "gap": gap.id,
                "hypothesis": hypothesis.id,
                "experiment": experiment.id,
                "observation": observation.id,
                "learning": learning_result
            })
        
        return results
    
    async def _identify_knowledge_gaps(
        self,
        context: AgentEnvironmentContext
    ) -> List[KnowledgeGap]:
        """
        Identify knowledge gaps in the current environment.
        """
        # Use KnowledgeAgent to find gaps
        gaps = await self.knowledge_agent.identify_gaps(
            context=context,
            min_importance=0.5  # Only gaps with significance
        )
        return gaps
    
    async def _form_hypothesis(
        self,
        context: AgentEnvironmentContext,
        gap: KnowledgeGap
    ) -> Optional[Hypothesis]:
        """
        Form a hypothesis to address a knowledge gap.
        """
        # Use PredictionAgent + KnowledgeAgent to generate hypothesis
        hypothesis_data = await self.knowledge_agent.generate_hypothesis(
            context=context,
            question=gap.question,
            evidence=gap.evidence_needed
        )
        
        if not hypothesis_data:
            return None
        
        return await self.hypothesis_service.create_hypothesis(
            environment_id=context.environment.id,
            statement=hypothesis_data["statement"],
            premise=hypothesis_data["premise"],
            expected_outcome=hypothesis_data["expected_outcome"],
            testability_criteria=hypothesis_data["testability_criteria"],
            priority=gap.importance
        )
    
    async def _design_experiment(
        self,
        context: AgentEnvironmentContext,
        hypothesis: Hypothesis
    ) -> Optional[Experiment]:
        """
        Design an experiment to test a hypothesis.
        """
        # Use SimulationAgent to design experiment
        experiment_design = await self.simulation_agent.design_experiment(
            context=context,
            hypothesis=hypothesis
        )
        
        if not experiment_design:
            return None
        
        return await self.experiment_service.create_experiment(
            environment_id=context.environment.id,
            hypothesis_id=hypothesis.id,
            description=experiment_design["description"],
            intervention=experiment_design["intervention"],
            control=experiment_design["control"],
            metrics=experiment_design["metrics"]
        )
    
    async def _run_experiment(
        self,
        context: AgentEnvironmentContext,
        experiment: Experiment
    ) -> Optional[ExperimentObservation]:
        """
        Run the experiment in a sandbox and observe results.
        """
        # 1. Run simulation
        simulation_result = await self.simulation_agent.simulate(
            context=context,
            scenario=experiment.intervention
        )
        
        # 2. Create observation
        observation = await self.experiment_bridge.process_experiment_results(
            context=context,
            experiment=experiment,
            results=simulation_result
        )
        
        return observation
    
    async def _learn_from_experiment(
        self,
        context: AgentEnvironmentContext,
        hypothesis: Hypothesis,
        observation: ExperimentObservation
    ) -> Dict[str, Any]:
        """
        Learn from experiment outcomes and crystallize knowledge.
        """
        # Use ExperimentBridge to decide if learning should occur
        learning_result = await self.experiment_bridge.learn_from_experiment(
            context=context,
            hypothesis=hypothesis,
            observation=observation
        )
        
        return learning_result
