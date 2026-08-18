import logging
from typing import List, Dict, Any
from app.schemas.memory_schemas import RetrievalPlan, MemoryResult
from app.repositories.interfaces import IVectorRepository, IGraphRepository
from app.services.keyword_search import KeywordSearch

logger = logging.getLogger(__name__)

class RetrievalAgent:
    """
    Executes the retrieval plan using hybrid search via repositories.
    """
    
    def __init__(self, vector_repo: IVectorRepository, graph_repo: IGraphRepository):
        self.vector_repo = vector_repo
        self.graph_repo = graph_repo
        self.keyword_search = KeywordSearch()
    
    async def hybrid_search(self, plan: RetrievalPlan, user_id: int) -> List[MemoryResult]:
        results = []
        
        # 1. Semantic search (Vector Repository)
        if plan.semantic_queries:
            semantic_results = await self._semantic_search(plan.semantic_queries, user_id)
            results.extend(semantic_results)
        
        # 2. Keyword search (BM25 - Still via service for now as it's an algorithm)
        if plan.keyword_queries:
            keyword_results = await self._keyword_search(plan.keyword_queries, user_id)
            results.extend(keyword_results)
        
        # 3. Graph traversal (Graph Repository)
        if plan.graph_traversals:
            graph_results = await self._graph_search(plan.graph_traversals, user_id)
            results.extend(graph_results)
        
        return self._normalize_and_deduplicate(results)
    
    async def _semantic_search(self, queries: List[str], user_id: int) -> List[MemoryResult]:
        results = []
        for query in queries:
            vectors = await self.vector_repo.search(query, user_id, limit=10)
            for v in vectors:
                results.append(MemoryResult(
                    content=v.get("content", ""),
                    source="semantic",
                    score=v.get("score", 0.9),
                    metadata={"memory_id": v.get("id")}
                ))
        return results
    
    async def _keyword_search(self, queries: List[str], user_id: int) -> List[MemoryResult]:
        """Search using BM25 keyword matching."""
        results = []
        for query in queries:
            matches = self.keyword_search.search(query, user_id, limit=5)
            for match in matches:
                results.append(MemoryResult(
                    content=match["content"],
                    source="keyword",
                    score=match["score"],
                    metadata={"memory_id": match["id"]}
                ))
        return results
    
    async def _graph_search(self, traversals: List[str], user_id: int) -> List[MemoryResult]:
        """Search using Graph traversal via repository."""
        results = []
        for traversal in traversals:
            nodes = self.graph_repo.execute_query(traversal)
            for node in nodes:
                results.append(MemoryResult(
                    content=node.get("content", node.get("name", "")),
                    source="graph",
                    score=0.8,
                    metadata={"memory_id": node.get("id")}
                ))
        return results
    
    def _normalize_and_deduplicate(self, results: List[MemoryResult]) -> List[MemoryResult]:
        seen = set()
        unique = []
        for r in results:
            if r.content not in seen:
                seen.add(r.content)
                r.score = min(1.0, r.score)
                unique.append(r)
        
        unique.sort(key=lambda x: x.score, reverse=True)
        return unique[:20]