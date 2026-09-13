import logging
import json
from typing import List, Dict, Any, Optional
from app.swarm.core.generator import GeneratorAgent

logger = logging.getLogger(__name__)

class PrivacyAbstractionAgent:
    """
    V3 Privacy Abstraction Agent: Anonymizes and abstracts crystallized 
    patterns for safe cross-environment transfer (Differential Privacy).
    """
    
    def __init__(self, generator: Optional[GeneratorAgent] = None):
        self.generator = generator or GeneratorAgent()

    async def abstract_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Strip PII and domain-specific anchors from a pattern, 
        leaving only the abstract logic.
        """
        prompt = f"""
        You are the PersonaVault V3 Privacy Abstraction Agent.
        Your goal is to prepare an intelligence pattern for cross-environment transfer.
        
        ORIGINAL PATTERN:
        {json.dumps(pattern, indent=2)}
        
        GOAL:
        1. STRIP all PII (names, emails, IDs, specific server names).
        2. ABSTRACT domain-specific anchors (e.g., change "Ollama endpoint" to "Inference Provider").
        3. EXTRACT the "Universal Logic" that remains valid across any similar domain.
        4. Apply "Differential Privacy" principles: ensure the resulting pattern cannot be traced back to its specific originating event.
        
        OUTPUT FORMAT (Strict JSON):
        {{
            "abstract_title": "Universal Title",
            "abstract_content": "The logic without specific details",
            "universal_anchors": ["logical-anchor-1", "logical-anchor-2"],
            "privacy_confidence": 0.99,
            "original_id_hash": "hashed-id"
        }}
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
            elif "{" in text:
                text = text[text.find("{"):text.rfind("}")+1]
            
            abstracted = json.loads(text)
            return abstracted
        except Exception as e:
            logger.error(f"Failed to abstract pattern: {e}")
            return {
                "error": "Abstraction failed",
                "raw_response": response.get("answer")
            }

privacy_abstraction_agent = PrivacyAbstractionAgent()
