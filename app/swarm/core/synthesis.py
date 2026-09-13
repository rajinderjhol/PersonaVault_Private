import logging
import json
from typing import List, Dict, Any, Optional
from app.swarm.core.generator import GeneratorAgent

logger = logging.getLogger(__name__)

class SynthesisAgent:
    """
    V3 Synthesis Agent: Reviews individual domain patterns and synthesizes 
    high-level "Master Rules" (Meta-Patterns) for 100,000:1 compression.
    """
    
    def __init__(self, generator: Optional[GeneratorAgent] = None):
        self.generator = generator or GeneratorAgent()

    async def synthesize_meta_patterns(self, domain_patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze a list of crystallized patterns and synthesize them into 
        fewer, more abstract meta-patterns.
        """
        if not domain_patterns:
            return []

        # Prepare patterns for LLM analysis
        patterns_summary = []
        for p in domain_patterns:
            patterns_summary.append({
                "id": str(p.get("id")),
                "content": p.get("content") or p.get("trigger", ""),
                "domain": p.get("metadata", {}).get("domain", "general")
            })

        prompt = f"""
        You are the PersonaVault V3 Synthesis Agent.
        Your goal is to achieve 100,000:1 Intelligence Compression.
        
        INPUT PATTERNS:
        {json.dumps(patterns_summary, indent=2)}
        
        GOAL:
        1. Review the input patterns.
        2. Identify common logical structures, shared constraints, or overlapping reasoning paths.
        3. Synthesize these into "Meta-Patterns" (Master Rules) that capture the essence of multiple patterns.
        4. Each Meta-Pattern should be abstract enough to cover multiple specific cases but specific enough to remain verifiable.
        
        OUTPUT FORMAT (Strict JSON List):
        [
            {{
                "title": "Meta-Pattern Title",
                "content": "The synthesized master rule content",
                "derived_from": ["id1", "id2"],
                "abstraction_level": "high",
                "reasoning": "Why this meta-pattern replaces the individual ones"
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
            # JSON block extraction
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "[" in text:
                text = text[text.find("["):text.rfind("]")+1]
            
            meta_patterns = json.loads(text)
            return meta_patterns
        except Exception as e:
            logger.error(f"Failed to parse meta-pattern synthesis: {e}")
            return []

synthesis_agent = SynthesisAgent()
