"""
Retrieval Agent - Handles memory retrieval with Auditable Traces
"""
import logging
from typing import List, Dict, Any, Optional
from app.schemas.memory_schemas import MemoryResult, RetrievalPlan
from app.swarm.base import BaseAgent

logger = logging.getLogger(__name__)

class RetrievalAgent(BaseAgent):
    def __init__(self, vector_repo=None, graph_repo=None, confidence_threshold: float = 0.6):
        super().__init__("retriever")
        self.vector_repo = vector_repo
        self.graph_repo = graph_repo
        self.confidence_threshold = confidence_threshold
        self.max_results = 10
        logger.info(f"RetrievalAgent initialized with threshold: {confidence_threshold}")
    
    async def hybrid_search(self, plan: RetrievalPlan, user_id: int) -> List[MemoryResult]:
        results = []
        vector_results_raw = []
        if self.vector_repo:
            try:
                vector_results_raw = await self.vector_repo.search(
                    query=plan.semantic_queries[0] if plan.semantic_queries else "",
                    user_id=user_id,
                    limit=self.max_results
                )
                for res in vector_results_raw:
                    # Apply confidence threshold
                    if res.get('score', 0) >= self.confidence_threshold:
                        results.append(MemoryResult(
                            content=res['content'],
                            source='faiss',
                            score=res['score']
                        ))
                    else:
                        logger.debug(f"Filtered low-confidence result: score={res.get('score', 0)}")
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        
        if self.graph_repo:
            try:
                graph_results = await self.graph_repo.search(
                    query=plan.keyword_queries[0] if plan.keyword_queries else "",
                    limit=self.max_results
                )
                results.extend(graph_results)
            except Exception as e:
                logger.warning(f"Graph search failed: {e}")
        
        logger.info(f"Retrieved {len(results)} results (filtered from {len(vector_results_raw)})")
        
        # Fallback if no results
        if not results:
            logger.warning(f"No high-confidence results found (threshold: {self.confidence_threshold})")
            results = [
                MemoryResult(
                    content="No relevant high-confidence memories found.",
                    source="fallback",
                    score=0.0
                )
            ]
        
        return results
    
    async def search(self, query: str, user_id: int, limit: int = 10) -> Dict[str, Any]:
        logger.info(f"RetrievalAgent searching for: {query}, user_id: {user_id}")
        plan = RetrievalPlan(
            needs_retrieval=True,
            semantic_queries=[query],
            keyword_queries=[],
            reasoning="Simple search"
        )
        results = await self.hybrid_search(plan, user_id)
        
        # Generate trace
        trace = self.create_trace(
            input_data=query,
            explanation=f"Retrieved {len(results)} memory items",
            confidence=max([r.score for r in results]) if results else 0.0,
            decision="retrieve_memories"
        )

        return {
            "results": results,
            "trace": trace
        }
    
    def set_confidence_threshold(self, threshold: float):
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold
            logger.info(f"Confidence threshold updated to: {threshold}")
