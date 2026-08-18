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
        self.pattern_threshold = 0.5

    async def plan(self, query: str, context: Dict[str, Any] = None) -> RetrievalPlan:
        return await self.create_plan(query, context)
    
    async def create_plan(self, query: str, context: Dict[str, Any] = None) -> RetrievalPlan:
        """Creates a structured retrieval plan with applied patterns."""
        intent = self._analyze_intent(query)
        learned_patterns = await self.semantic_memory.get_patterns()
        
        active_patterns = [p for p in learned_patterns if (p.weight or 0) >= self.pattern_threshold and p.is_active]

        # Track applied patterns/instructions without modifying the query
        applied_patterns = []
        applied_instructions = []
        for pattern in active_patterns:
            if self._should_apply_pattern(query, pattern):
                applied_patterns.append(pattern.trigger[:30])
                applied_instructions.append(pattern.correction)
                logger.info(f"📌 Pattern matched: {pattern.trigger[:30]} (weight: {pattern.weight})")
        
        needs_retrieval = self._needs_retrieval(query, context)
        
        # Use the original query for semantic search
        plan = RetrievalPlan(
            needs_retrieval=needs_retrieval,
            semantic_queries=[query],  # Use original query, not modified
            keyword_queries=self._generate_keyword_queries(query, intent),
            graph_traversals=self._generate_graph_traversals(query, intent),
            instructions=applied_instructions,
            reasoning=self._explain_planning(query, intent, applied_patterns),
            complexity_score=intent.get("complexity", 0.3)
        )
        
        logger.info(f"Created retrieval plan with {len(applied_patterns)} patterns")
        return plan
    
    def _should_apply_pattern(self, query: str, pattern: SemanticPattern) -> bool:
        if pattern.trigger.lower() in query.lower():
            return True
        return False
    
    def _apply_pattern(self, query: str, pattern: SemanticPattern) -> str:
        # Keep this method but don't use it for retrieval
        return query
    
    def _analyze_intent(self, query: str) -> Dict[str, Any]:
        return {"type": "mixed", "entities": [], "time_reference": None, "complexity": self._calculate_complexity(query)}
    
    def _calculate_complexity(self, query: str) -> float:
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
        if query.lower() in ["hello", "hi", "hey"]:
            return False
        return True
    
    def _generate_semantic_queries(self, query: str, intent: Dict) -> List[str]:
        return [query]
    
    def _generate_keyword_queries(self, query: str, intent: Dict) -> List[str]:
        # Extract keywords for BM25 search
        terms = query.lower().split()
        # Keep meaningful words (remove stopwords)
        stopwords = {'the', 'a', 'an', 'of', 'for', 'on', 'at', 'to', 'in', 'with', 'without', 'and', 'or', 'but'}
        keywords = [t for t in terms if t not in stopwords and len(t) > 2]
        return [" ".join(keywords[:5])]
    
    def _generate_graph_traversals(self, query: str, intent: Dict) -> List[str]:
        if intent.get("type") == "relational":
            return [f"MATCH (m:Memory)-[:RELATED_TO]->(t:Tag) WHERE t.name CONTAINS '{query}'"]
        return []
    
    def _explain_planning(self, query: str, intent: Dict, applied_patterns: List[str]) -> str:
        patterns_str = f" (applied {len(applied_patterns)} patterns)" if applied_patterns else ""
        return f"Query classified as {intent['type']}{patterns_str}."

PlanningAgent = PlannerAgent
