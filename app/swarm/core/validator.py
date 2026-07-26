import logging
import httpx
import json
from typing import List, Dict, Any, Optional
from app.config import Config
from app.schemas.memory_schemas import MemoryResult

logger = logging.getLogger(__name__)

class ValidatorAgent:
    """
    Cognitive Validation Agent for PersonaVault.
    Cross-references reasoning insights with retrieved evidence to prevent hallucinations.
    """
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.ollama_url = Config.OLLAMA_BASE_URL
        self.client = client or httpx.AsyncClient(timeout=60.0)
        self.model = "llama3"

    async def validate(self, query: str, evidence: List[MemoryResult], logic: str) -> Dict[str, Any]:
        """
        Performs a logical cross-check.
        Returns a results dictionary containing validity and risk assessment.
        """
        # Prepare evidence context (top 5 results for clarity)
        evidence_text = "\n".join([f"FACT {i+1}: {m.content}" for i, m in enumerate(evidence[:5])])
        
        if not evidence_text:
            logger.debug("ValidatorAgent: No factual evidence provided; passing logic by default.")
            return {"is_valid": True, "risk_score": 0.0, "explanation": "No evidence to cross-check."}

        prompt = f"""
### TASK: COGNITIVE LOGIC VALIDATION
Verify if the PROPOSED REASONING is factually supported by the RETRIEVED EVIDENCE for the given query.

USER QUERY: {query}

RETRIEVED EVIDENCE:
{evidence_text}

PROPOSED REASONING:
{logic}

### INSTRUCTIONS:
1. Determine if the reasoning claims facts that are NOT in the evidence (hallucinations).
2. Check if the reasoning path contradicts the evidence.
3. Return 'is_valid: true' only if the logic is safe and grounded.

Return result as JSON only:
{{
  "is_valid": true/false,
  "explanation": "concise reasoning for validation status"
}}
"""
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0} # Ensure deterministic validation
                }
            )
            if response.status_code == 200:
                raw_res = response.json().get("response", "{}")
                # Extract JSON from potential LLM chatter
                if "{" in raw_res:
                    raw_res = raw_res[raw_res.find("{"):raw_res.rfind("}")+1]
                
                result = json.loads(raw_res)
                # Ensure defaults for safety
                result.setdefault("is_valid", True)
                result.setdefault("risk_score", 0.0)
                
                return result
        except Exception as e:
            logger.error(f"ValidatorAgent: Error during validation cross-check: {e}")
            
        return {"is_valid": True, "risk_score": 0.0, "explanation": "Validator error; failing open."}