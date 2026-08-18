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
    
    def __init__(self, vector_repo: IVectorRepository = None, graph_repo: IGraphRepository = None):
        self.vector_repo = vector_repo
        self.graph_repo = graph_repo
        self.keyword_search = KeywordSearch()
    
    async def hybrid_search(self, plan: RetrievalPlan, user_id: int) -> List[MemoryResult]:
        results = []
        
        # 1. Use local retriever as primary (works without embeddings)
        if plan.semantic_queries:
            try:
                from app.services.local_retriever import LocalRetriever
                retriever = LocalRetriever()
                query = plan.semantic_queries[0]
                logger.info(f"RetrievalAgent: Searching with local retriever: '{query}'")
                local_results = await retriever.search(query, user_id, limit=20)
                logger.info(f"RetrievalAgent: Local retriever found {len(local_results)} results")
                for r in local_results:
                    results.append(MemoryResult(
                        content=r.get("content", ""),
                        source="local",
                        score=r.get("score", 0.5),
                        metadata={"memory_id": r.get("id")}
                    ))
            except Exception as e:
                logger.warning(f"Local retriever failed: {e}")
        
        # 2. Try semantic search (Vector Repository) as fallback
        if plan.semantic_queries and not results:
            semantic_results = await self._semantic_search(plan.semantic_queries, user_id)
            results.extend(semantic_results)
        
        # 3. Keyword search (BM25)
        if plan.keyword_queries:
            keyword_results = await self._keyword_search(plan.keyword_queries, user_id)
            results.extend(keyword_results)
        
        # 4. Graph traversal (Graph Repository)
        if plan.graph_traversals:
            graph_results = await self._graph_search(plan.graph_traversals, user_id)
            results.extend(graph_results)
        
        return self._normalize_and_deduplicate(results)
    
    async def _semantic_search(self, queries: List[str], user_id: int) -> List[MemoryResult]:
        results = []
        for query in queries:
            if self.vector_repo:
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
        if self.graph_repo:
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
