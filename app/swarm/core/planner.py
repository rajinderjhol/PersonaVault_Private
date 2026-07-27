import logging
from typing import List, Dict, Any
from app.schemas.memory_schemas import RetrievalPlan
from app.models import SemanticPattern
from app.services.semantic_memory import SemanticMemory

logger = logging.getLogger(__name__)

class PlannerAgent:
    """Analyzes query intent and creates a retrieval strategy with pattern weighting."""
    
    def __init__(self, semantic_memory: SemanticMemory):
        self.semantic_memory = semantic_memory
        self.pattern_threshold = 0.5  # Minimum weight to apply a pattern
    
    async def create_plan(self, query: str, context: Dict[str, Any] = None) -> RetrievalPlan:
        """Creates a structured retrieval plan with applied patterns."""
        intent = self._analyze_intent(query)
        learned_patterns = await self.semantic_memory.get_patterns()
        
        # Filter patterns by weight - only apply high-confidence patterns
        active_patterns = [p for p in learned_patterns if (p.weight or 0) >= self.pattern_threshold and p.is_active]

        # Apply patterns with weighting
        refined_query = query
        applied_patterns = []
        for pattern in active_patterns:
            if self._should_apply_pattern(query, pattern):
                refined_query = self._apply_pattern(refined_query, pattern)
                applied_patterns.append(pattern.trigger[:30])
                logger.info(f"📌 Applied pattern: {pattern.trigger[:30]} (weight: {pattern.weight})")
        
        needs_retrieval = self._needs_retrieval(query, context)
        
        plan = RetrievalPlan(
            needs_retrieval=needs_retrieval,
            semantic_queries=self._generate_semantic_queries(refined_query, intent),
            keyword_queries=self._generate_keyword_queries(refined_query, intent),
            graph_traversals=self._generate_graph_traversals(refined_query, intent),
            reasoning=self._explain_planning(refined_query, intent, applied_patterns),
            complexity_score=intent.get("complexity", 0.3)
        )
        
        logger.info(f"Created retrieval plan with {len(applied_patterns)} applied patterns")
        return plan
    
    def _should_apply_pattern(self, query: str, pattern: SemanticPattern) -> bool:
        """Determine if a pattern should be applied to this query."""
        # Simple trigger matching - improve with vector similarity in Phase 4
        if pattern.trigger.lower() in query.lower():
            return True
        return False
    
    def _apply_pattern(self, query: str, pattern: SemanticPattern) -> str:
        """Apply a pattern correction to the query."""
        return f"{query}\n[SYSTEM INSTRUCTION: {pattern.correction}]"
    
    def _analyze_intent(self, query: str) -> Dict[str, Any]:
        """Determine query intent."""
        return {"type": "mixed", "entities": [], "time_reference": None, "complexity": self._calculate_complexity(query)}
    
    def _calculate_complexity(self, query: str) -> float:
        """Heuristic to determine query complexity."""
        score = 0.2
        if len(query.split()) > 25:
            score += 0.4
        elif len(query.split()) > 12:
            score += 0.2
        heavy_words = ["compare", "contrast", "summarize", "analyze", "evaluate", "predict", "synthesize", "relationship", "why", "how does"]
        if any(word in query.lower() for word in heavy_words):
            score += 0.3
        return min(1.0, round(score, 2))
    
    def _needs_retrieval(self, query: str, context: Dict) -> bool:
        """Determine if we need to retrieve memories."""
        if query.lower() in ["hello", "hi", "hey"]:
            return False
        return True
    
    def _generate_semantic_queries(self, query: str, intent: Dict) -> List[str]:
        """Generate variations for semantic (vector) search."""
        return [query]
    
    def _generate_keyword_queries(self, query: str, intent: Dict) -> List[str]:
        """Generate queries for BM25 keyword search."""
        terms = query.split()
        return [" ".join(terms[:3])]
    
    def _generate_graph_traversals(self, query: str, intent: Dict) -> List[str]:
        """Generate Neo4j traversal patterns."""
        if intent.get("type") == "relational":
            return [f"MATCH (m:Memory)-[:RELATED_TO]->(t:Tag) WHERE t.name CONTAINS '{query}'"]
        return []
    
    def _explain_planning(self, query: str, intent: Dict, applied_patterns: List[str]) -> str:
        """Generate human-readable explanation of the plan."""
        patterns_str = f" (applied {len(applied_patterns)} patterns)" if applied_patterns else ""
        return f"Query classified as {intent['type']}{patterns_str}."
