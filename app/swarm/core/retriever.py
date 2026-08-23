"""
Retrieval Agent - Handles memory retrieval
"""
import logging
from typing import List, Dict, Any, Optional
from app.schemas.memory_schemas import MemoryResult, RetrievalPlan

logger = logging.getLogger(__name__)

class RetrievalAgent:
    def __init__(self, vector_repo=None, graph_repo=None):
        self.vector_repo = vector_repo
        self.graph_repo = graph_repo
        logger.info("RetrievalAgent initialized")
    
    async def hybrid_search(self, plan: RetrievalPlan, user_id: int) -> List[MemoryResult]:
        results = []
        if self.vector_repo:
            try:
                vector_results = await self.vector_repo.search(
                    query=plan.semantic_queries[0] if plan.semantic_queries else "",
                    limit=10
                )
                results.extend(vector_results)
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        
        if self.graph_repo:
            try:
                graph_results = await self.graph_repo.search(
                    query=plan.keyword_queries[0] if plan.keyword_queries else "",
                    limit=10
                )
                results.extend(graph_results)
            except Exception as e:
                logger.warning(f"Graph search failed: {e}")
        
        if not results:
            logger.info("Using mock retrieval results")
            results = [
                MemoryResult(
                    content="Sample retrieval result. The system is ready.",
                    source="mock",
                    score=0.5
                )
            ]
        
        return results
    
    async def search(self, query: str, user_id: int, limit: int = 10) -> List[MemoryResult]:
        plan = RetrievalPlan(
            needs_retrieval=True,
            semantic_queries=[query],
            keyword_queries=[],
            reasoning="Simple search"
        )
        return await self.hybrid_search(plan, user_id)
