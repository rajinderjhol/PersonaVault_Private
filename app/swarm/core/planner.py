import logging
from typing import List, Dict, Any
from app.schemas.memory_schemas import RetrievalPlan, SemanticPattern
from app.services.semantic_memory import SemanticMemory

logger = logging.getLogger(__name__)

class PlannerAgent:
    """
    Analyzes query intent and creates a retrieval strategy.
    Uses Semantic Memory to apply learned patterns.
    """
    
    def __init__(self, semantic_memory: SemanticMemory):
        self.semantic_memory = semantic_memory
    
    async def create_plan(self, query: str, context: Dict[str, Any] = None) -> RetrievalPlan:
        """
        Creates a structured retrieval plan based on query analysis.
        """
        # 1. Analyze query intent
        intent = self._analyze_intent(query)
        
        # 2. Get learned patterns from Semantic Memory
        learned_patterns = await self.semantic_memory.get_patterns()
        
        # 3. Apply patterns to refine query
        refined_query = self._apply_patterns(query, learned_patterns)
        
        # 4. Determine if retrieval is needed
        needs_retrieval = self._needs_retrieval(query, context)
        
        # 5. Generate specific queries for each search type
        plan = RetrievalPlan(
            needs_retrieval=needs_retrieval,
            semantic_queries=self._generate_semantic_queries(refined_query, intent),
            keyword_queries=self._generate_keyword_queries(refined_query, intent),
            graph_traversals=self._generate_graph_traversals(refined_query, intent),
            reasoning=self._explain_planning(refined_query, intent),
            complexity_score=intent.get("complexity", 0.3)
        )
        
        logger.info(f"Created retrieval plan for query: {query[:50]}...")
        return plan
    
    def _analyze_intent(self, query: str) -> Dict[str, Any]:
        """Determine query intent: factual, relational, temporal, or mixed."""
        intent = {
            "type": "mixed", 
            "entities": [],  
            "time_reference": None,
            "complexity": self._calculate_complexity(query)
        }
            
        return intent

    def _calculate_complexity(self, query: str) -> float:
        """
        Heuristic to determine query complexity from 0.0 to 1.0.
        Higher scores suggest the need for cloud-based reasoning (Gemini).
        """
        score = 0.2  # Base score
        
        # 1. Structural Complexity: Sentence length
        words = query.split()
        if len(words) > 25:
            score += 0.4
        elif len(words) > 12:
            score += 0.2
            
        # 2. Reasoning Complexity: Analytical keywords
        heavy_reasoning_words = [
            "compare", "contrast", "summarize", "analyze", "evaluate", 
            "predict", "synthesize", "relationship", "why", "how does"
        ]
        if any(word in query.lower() for word in heavy_reasoning_words):
            score += 0.3
            
        # 3. Logical Complexity: Conditional indicators
        logical_markers = ["if", "then", "because", "unless", "consequently", "however"]
        if sum(1 for w in words if w.lower() in logical_markers) >= 2:
            score += 0.15
            
        # Ensure normalized range
        return min(1.0, round(score, 2))
    
    def _apply_patterns(self, query: str, patterns: List[SemanticPattern]) -> str:
        """Apply learned patterns to refine the query."""
        modified = query
        for pattern in patterns:
            if pattern.pattern_type == "query_refinement":
                if pattern.trigger.lower() in query.lower():
                    modified = f"{modified} {pattern.correction}"
        return modified
    
    def _needs_retrieval(self, query: str, context: Dict) -> bool:
        """Determine if we need to retrieve memories."""
        if query.lower() in ["hello", "hi", "hey"]:
            return False
        return True
    
    def _generate_semantic_queries(self, query: str, intent: Dict) -> List[str]:
        """Generate variations for semantic (vector) search."""
        variations = [query]
        for entity in intent.get("entities", []):
            variations.append(f"{entity} {query}")
        return variations
    
    def _generate_keyword_queries(self, query: str, intent: Dict) -> List[str]:
        """Generate queries for BM25 keyword search."""
        terms = query.split()
        return [" ".join(terms[:3])] 
    
    def _generate_graph_traversals(self, query: str, intent: Dict) -> List[str]:
        """Generate Neo4j traversal patterns."""
        if intent["type"] == "relational":
            return [f"MATCH (m:Memory)-[:RELATED_TO]->(t:Tag) WHERE t.name CONTAINS '{query}'"]
        return []
    
    def _explain_planning(self, query: str, intent: Dict) -> str:
        """Generate human-readable explanation of the plan."""
        return f"Query classified as {intent['type']}."