import logging
import json
from typing import List, Dict, Any, Optional
from app.swarm.core.generator import GeneratorAgent

logger = logging.getLogger(__name__)

class PolicyInferenceAgent:
    """
    V3 Policy Inference Agent: Infers implicit governance rules 
    from human corrections and decision outcomes.
    """
    
    def __init__(self, generator: Optional[GeneratorAgent] = None):
        self.generator = generator or GeneratorAgent()

    async def infer_policies(self, corrections: List[Dict[str, Any]], existing_policies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze corrections and existing policies to propose new governance rules.
        """
        if not corrections:
            return []

        prompt = f"""
        You are the PersonaVault V3 Policy Inference Agent.
        Your goal is to infer implicit governance rules (Policies) from human corrections.
        
        EXISTING POLICIES:
        {json.dumps(existing_policies, indent=2)}
        
        HUMAN CORRECTIONS:
        {json.dumps(corrections, indent=2)}
        
        GOAL:
        1. Identify recurring themes or requirements in the corrections that are NOT covered by existing policies.
        2. Infer the underlying "Implicit Rule" that the human is enforcing.
        3. Draft new PersonaVault Policy objects to automate this governance.
        4. Each policy must have clear conditions and an actionable description.
        
        OUTPUT FORMAT (Strict JSON List):
        [
            {{
                "name": "Policy Name",
                "description": "The inferred governance rule",
                "conditions": ["When context contains X", "If outcome was Y"],
                "reasoning": "Why this policy was inferred from the corrections",
                "confidence": 0.85
            }}
        ]
        """

        response = await self.generator.generate(
            query=prompt,
            context=[],
            provider="ollama"
        )

        try:
            text = response.get("answer", "")
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "[" in text:
                text = text[text.find("["):text.rfind("]")+1]
            
            inferred_policies = json.loads(text)
            return inferred_policies
        except Exception as e:
            logger.error(f"Failed to parse policy inference: {e}")
            return []

policy_inference_agent = PolicyInferenceAgent()
