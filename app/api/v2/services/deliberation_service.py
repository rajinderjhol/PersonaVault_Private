from typing import List, Dict, Any
from app.api.v2.models.environment import Environment
from app.api.v2.models.deliberation import Deliberation
from app.api.v2.models.reasoning_chain import ReasoningChain
from app.swarm.specialized.prediction_agent import PredictionAgent
import uuid
from datetime import datetime

class DeliberationService:
    """
    Compares alternatives and makes reasoned choices.
    """
    
    def __init__(
        self,
        prediction_agent: PredictionAgent
    ):
        self.prediction_agent = prediction_agent
    
    async def deliberate(
        self,
        environment: Environment,
        reasoning_chain: ReasoningChain,
        alternatives: List[Dict[str, Any]]
    ) -> Deliberation:
        """
        Deliberate between alternatives to reach a decision.
        """
        # 1. Evaluate alternatives
        evaluations = await self.evaluate_alternatives(
            environment=environment,
            alternatives=alternatives
        )
        
        # 2. Choose the best alternative
        chosen = await self.choose_alternative(
            evaluations=evaluations,
            criteria=["score", "confidence", "risk"]
        )
        
        # 3. Generate rationale
        rationale = await self._generate_rationale(
            environment=environment,
            chosen=chosen,
            evaluations=evaluations
        )
        
        # 4. Create deliberation record
        return Deliberation(
            id=str(uuid.uuid4()),
            environment_id=environment.id,
            reasoning_chain_id=reasoning_chain.id,
            alternatives=alternatives,
            chosen_alternative=chosen,
            rationale=rationale,
            confidence=chosen.get("evaluation", {}).get("confidence", 0.5),
            status="completed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def evaluate_alternatives(
        self,
        environment: Environment,
        alternatives: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate alternatives against criteria.
        """
        evaluations = {}
        
        for alt in alternatives:
            result = await self.prediction_agent.predict_outcome(
                environment=environment,
                scenario={
                    "type": "alternative_evaluation",
                    "alternative": alt
                }
            )
            
            evaluations[alt.get("id", "unknown")] = {
                "score": result.get("score", 0.5),
                "confidence": result.get("confidence", 0.5),
                "risk": result.get("risk", 0.5),
                "feasibility": result.get("feasibility", 0.5)
            }
        
        return evaluations
    
    async def choose_alternative(
        self,
        evaluations: Dict[str, Dict[str, float]],
        criteria: List[str]
    ) -> Dict[str, Any]:
        """
        Choose the best alternative based on evaluations.
        """
        best_alt_id = None
        best_score = -1.0
        
        for alt_id, scores in evaluations.items():
            # Compute weighted score
            weighted_score = (
                scores.get("score", 0.5) * 0.4 +
                scores.get("confidence", 0.5) * 0.3 -
                scores.get("risk", 0.5) * 0.3
            )
            
            if weighted_score > best_score:
                best_score = weighted_score
                best_alt_id = alt_id
        
        return {
            "id": best_alt_id,
            "weighted_score": best_score,
            "evaluation": evaluations.get(best_alt_id, {})
        }
    
    async def _generate_rationale(
        self,
        environment: Environment,
        chosen: Dict[str, Any],
        evaluations: Dict[str, Dict[str, float]]
    ) -> str:
        """
        Generate a rationale for the chosen alternative.
        """
        result = await self.prediction_agent.predict_outcome(
            environment=environment,
            scenario={
                "type": "rationale_generation",
                "chosen": chosen,
                "evaluations": evaluations
            }
        )
        
        return result.get("rationale", "No rationale generated")
