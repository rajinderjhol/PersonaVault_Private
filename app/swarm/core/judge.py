import logging
from typing import List, Optional, Dict, Any
import httpx
import json
from app.schemas.memory_schemas import EvaluationMetrics, MemoryResult # Assuming schemas.py is in app/services
from app.config import Config
logger = logging.getLogger(__name__)

class JudgeAgent:
    """
    Evaluates the quality of generated answers based on RAG metrics.
    Uses a local LLM to cross-examine the Generator.
    """
    
    def __init__(self, ollama_url: Optional[str] = None, client: Optional[httpx.AsyncClient] = None):
        self.ollama_url = ollama_url or Config.OLLAMA_BASE_URL
        self.ollama_model = Config.OLLAMA_JUDGE_MODEL
        self._client = client or httpx.AsyncClient(timeout=30.0)

    async def evaluate(self, query: str, answer: str, context: List[MemoryResult]) -> EvaluationMetrics:
        """
        Evaluate the answer on Faithfulness, Coverage, and Relevance.
        """
        logger.info(f"Judging answer for query: {query[:50]}...")
        
        default_scores = {"faithfulness": 0.0, "coverage": 0.0, "relevance": 0.0}
        llm_results = await self._llm_evaluate(query, answer, context)
        scores = {**default_scores, **llm_results}
        
        confidence = llm_results.get("confidence", 0.8)
        hedging = self._detect_hedging(answer)
        
        passed = all([
            scores.get("faithfulness", 0) > 0.7,
            scores.get("coverage", 0) > 0.6,
            scores["relevance"] > 0.7,
            confidence > 0.6
        ])
        
        feedback = ""
        if not passed:
            if scores["faithfulness"] < 0.7:
                feedback = "The answer includes information not found in your memories."
            elif scores["coverage"] < 0.6:
                feedback = "The answer missed several parts of your request."
            elif scores["relevance"] < 0.7:
                feedback = "The answer doesn't directly address your question."
            elif confidence < 0.6:
                feedback = "The system has low confidence in this specific reasoning path."

        return EvaluationMetrics(
            coverage=scores["coverage"],
            relevance=scores["relevance"],
            faithfulness=scores["faithfulness"],
            confidence=confidence,
            passed=passed,
            needs_human=not passed or hedging,
            hedging_detected=hedging,
            feedback=feedback
        )

    def _detect_hedging(self, text: str) -> bool:
        """Detects if the AI is using non-committal language."""
        hedge_words = ["i think", "i believe", "maybe", "perhaps", 
                       "i'm not sure", "might be", "could be", "possibly"]
        return any(word in text.lower() for word in hedge_words)

    async def _llm_evaluate(self, query: str, answer: str, context: List[MemoryResult]) -> Dict[str, Any]:
        """Use LLM to evaluate the answer quality."""
        context_summary = "\n".join([c.content[:200] for c in context[:5]])
        
        prompt = f"""
Evaluate AI answer:
CONTEXT: {context_summary}
QUERY: {query}
AI ANSWER: {answer}

Rate 0-1 for: Faithfulness, Coverage, Relevance, and your own Confidence in the accuracy.
Return JSON only: {{"faithfulness": 0.9, "coverage": 0.8, "relevance": 0.9, "confidence": 0.85}}
"""
        try:
            res = await self._client.post(f"{self.ollama_url}/api/generate", json={
                "model": self.ollama_model, "prompt": prompt, "stream": False,
                "options": {"temperature": 0.1}
            })
            
            if res.status_code == 200:
                return json.loads(res.json().get("response", "{}"))
        except Exception as e:
            logger.error(f"JudgeAgent LLM call failed: {e}")
        return {"faithfulness": 0.5, "coverage": 0.5, "relevance": 0.5}

    def detect_hallucination_pattern(self, entry: EvaluationMetrics) -> bool:
        """Flag if this is a hallucination pattern."""
        return entry.faithfulness < 0.5