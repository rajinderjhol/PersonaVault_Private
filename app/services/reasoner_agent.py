import logging
import httpx
from typing import Dict, Any, Optional
from app.config import Config

logger = logging.getLogger(__name__)

class ReasonerAgent:
    """
    Cognitive Reasoning Agent for PersonaVault.
    Analyzes query intent and provides logical grounding for the generation phase.
    """
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.ollama_url = Config.OLLAMA_BASE_URL
        self.client = client or httpx.AsyncClient(timeout=60.0)
        self.model = Config.OLLAMA_REASONER_MODEL

    async def analyze(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        Synthesizes a logical reasoning path based on the user query and situational context.
        """
        logger.info(f"ReasonerAgent: Analyzing query complexity and logical requirements.")
        
        # Extract situational awareness from context if provided
        situational_summary = "None provided"
        if context and "situational_awareness" in context:
            situational_summary = str(context["situational_awareness"])

        prompt = f"""
### TASK: LOGICAL REASONING & COGNITIVE GROUNDING
Analyze the following query and provide a high-level reasoning insight. 
This insight will be used to ground the final answer generation.

USER QUERY: {query}
SITUATIONAL CONTEXT: {situational_summary}

### INSTRUCTIONS:
1. Identify the core intent and logical constraints of the request.
2. Determine if the request implies a specific tone, persona, or behavioral rule.
3. Provide a concise summary of how the system should approach this reasoning task.

REASONING INSIGHT:
"""
        try:
            res = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2}
                }
            )
            if res.status_code == 200:
                return res.json().get("response", "").strip()
        except Exception as e:
            logger.warning(f"ReasonerAgent: Local reasoning failed, falling back: {e}")
        
        return "Standard logical approach: Analyze memory matches and generate grounded response."