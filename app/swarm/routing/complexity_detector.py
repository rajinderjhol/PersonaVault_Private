import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ComplexityDetector:
    """Detects if a query requires deep reasoning vs. simple retrieval"""
    
    async def assess_complexity(self, query: str, context: List[Dict]) -> Dict[str, Any]:
        """Return complexity score and reasoning requirements"""
        
        # 1. Check if context has crystallized evidence (Layer 3 / Ice)
        has_crystallized = any(
            (mem.get("layer") == 3 or mem.get("source") == "faiss") and mem.get("score", 0) > 0.8
            for mem in context or []
        )
        
        # 2. Check for complex query patterns
        complexity_signals = {
            "requires_reasoning": await self._needs_deep_reasoning(query),
            "contradictory_evidence": await self._has_contradictions(context),
            "novel_situation": len(context or []) == 0,
            "high_stakes": await self._is_high_stakes(query)
        }
        
        # 3. Calculate aggregate complexity score (0.0-1.0)
        # Weights:
        # No crystallized evidence: 0.4
        # Reasoning keywords: 0.3
        # Contradictions: 0.2 (Placeholder)
        # Novel situation: 0.1
        
        score = 0.0
        if not has_crystallized:
            score += 0.4
        if complexity_signals["requires_reasoning"]:
            score += 0.3
        if complexity_signals["contradictory_evidence"]:
            score += 0.2
        if complexity_signals["novel_situation"]:
            score += 0.1
            
        # Ensure we stay in bounds
        final_score = min(score, 1.0)
        
        return {
            "score": final_score,
            "needs_reasoning": final_score > 0.5,
            "signals": complexity_signals,
            "has_crystallized_evidence": has_crystallized
        }
    
    async def _needs_deep_reasoning(self, query: str) -> bool:
        """Simple heuristic: check for complex reasoning keywords"""
        reasoning_keywords = [
            "why", "how", "explain", "analyze", "evaluate",
            "compare", "contrast", "synthesize", "critique",
            "think", "logic", "derive", "prove"
        ]
        q_lower = query.lower()
        return any(keyword in q_lower for keyword in reasoning_keywords)
    
    async def _has_contradictions(self, context: List[Dict]) -> bool:
        """Check for conflicting evidence in context (Placeholder for semantic analysis)"""
        if not context:
            return False
        # Future implementation: Compare semantic embeddings or metadata attributes
        return False
    
    async def _is_high_stakes(self, query: str) -> bool:
        """Identify if query involves security, compliance, or sensitive domains"""
        high_stakes_domains = [
            "security", "compliance", "safety", "legal", "medical", 
            "financial", "privacy", "governance"
        ]
        q_lower = query.lower()
        return any(domain in q_lower for domain in high_stakes_domains)
