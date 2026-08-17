"""
Hybrid Retriever - Works with or without embeddings
Uses BM25 keyword search as fallback when Ollama embeddings aren't available
"""
import logging
import numpy as np
from typing import List, Dict, Any
from sqlalchemy import select, or_, and_
from app.db.session import SessionLocal
from app.models import Memory

logger = logging.getLogger(__name__)

class HybridRetriever:
    """Hybrid retriever that works with or without embeddings."""
    
    def __init__(self):
        self._embedding_model = None
        self._use_embeddings = False
        self._check_ollama_embeddings()
    
    def _check_ollama_embeddings(self):
        """Check if Ollama embeddings are available."""
        import asyncio
        import httpx
        
        try:
            # Quick check if Ollama supports embeddings
            import requests
            response = requests.post(
                "http://localhost:11434/api/embeddings",
                json={"model": "tinydolphin", "prompt": "test"},
                timeout=2
            )
            if response.status_code == 200 and response.json().get("embedding"):
                self._use_embeddings = True
                logger.info("✅ Ollama embeddings available")
                return
        except:
            pass
        
        logger.info("ℹ️ Ollama embeddings not available, using BM25 fallback")
        self._use_embeddings = False
    
    async def search(self, query: str, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories using the best available method."""
        if self._use_embeddings:
            return await self._search_with_embeddings(query, user_id, limit)
        else:
            return await self._search_with_bm25(query, user_id, limit)
    
    async def _search_with_embeddings(self, query: str, user_id: int, limit: int) -> List[Dict[str, Any]]:
        """Search using vector embeddings."""
        from app.services.vector_service import vector_service
        
        try:
            results = await vector_service.search_similar(query, user_id, limit)
            return results
        except Exception as e:
            logger.warning(f"Embedding search failed: {e}, falling back to BM25")
            return await self._search_with_bm25(query, user_id, limit)
    
    async def _search_with_bm25(self, query: str, user_id: int, limit: int) -> List[Dict[str, Any]]:
        """Search using BM25 keyword matching."""
        from app.services.keyword_search import KeywordSearch
        
        try:
            keyword_search = KeywordSearch()
            results = keyword_search.search(query, user_id, limit)
            return results
        except Exception as e:
            logger.warning(f"BM25 search failed: {e}, using simple keyword match")
            return await self._simple_keyword_search(query, user_id, limit)
    
    async def _simple_keyword_search(self, query: str, user_id: int, limit: int) -> List[Dict[str, Any]]:
        """Simple keyword search as last resort."""
        async with SessionLocal() as db:
            # Split query into keywords
            keywords = query.lower().split()
            if not keywords:
                return []
            
            # Build search conditions
            conditions = []
            for kw in keywords:
                if len(kw) > 2:  # Ignore short words
                    conditions.append(Memory.content.ilike(f"%{kw}%"))
                    conditions.append(Memory.title.ilike(f"%{kw}%"))
            
            if not conditions:
                return []
            
            # Build query with OR conditions
            stmt = select(Memory).where(
                and_(Memory.user_id == user_id, or_(*conditions))
            ).limit(limit * 2)  # Get extra for scoring
            
            result = await db.execute(stmt)
            memories = result.scalars().all()
            
            # Simple scoring by keyword count
            scored = []
            for mem in memories:
                score = 0
                content = (mem.content or "").lower()
                title = (mem.title or "").lower()
                for kw in keywords:
                    if len(kw) > 2:
                        score += content.count(kw) * 0.5
                        score += title.count(kw) * 1.0
                
                if score > 0:
                    scored.append({
                        "id": mem.id,
                        "content": mem.content,
                        "title": mem.title,
                        "score": min(1.0, score / 20)  # Normalize
                    })
            
            # Sort by score and limit
            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:limit]
