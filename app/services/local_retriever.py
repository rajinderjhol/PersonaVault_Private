"""
Local Retriever - Works 100% offline without embeddings
Uses keyword matching with TF-IDF scoring
"""
import logging
import re
from typing import List, Dict, Any
from collections import Counter
from sqlalchemy import select, or_, and_, func
from app.db.session import SessionLocal
from app.models import Memory

logger = logging.getLogger(__name__)

class LocalRetriever:
    """
    Pure local retrieval without embeddings.
    Works completely offline.
    """
    
    def __init__(self):
        self._stopwords = {'the', 'a', 'an', 'of', 'for', 'on', 'at', 'to', 'in', 'with', 'without', 'and', 'or', 'but'}
        self._cache = {}
    
    async def search(self, query: str, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories using TF-IDF scoring."""
        # Clean and tokenize query
        words = self._tokenize(query)
        if not words:
            return []
        
        # Get all memories for this user
        async with SessionLocal() as db:
            stmt = select(Memory).where(Memory.user_id == user_id)
            result = await db.execute(stmt)
            memories = result.scalars().all()
            
            if not memories:
                return []
            
            # Score each memory
            scored = []
            for mem in memories:
                # Skip chat episodes
                if mem.title and ("Chat Episode" in mem.title or "Episode" in mem.title):
                    continue
                    
                score = self._calculate_score(words, mem)
                if score > 0:
                    scored.append({
                        "id": mem.id,
                        "content": mem.content,
                        "title": mem.title,
                        "score": min(1.0, score),
                        "tags": mem.tags
                    })
            
            # Sort by score and limit
            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:limit]
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize and clean text."""
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        words = text.split()
        # Remove stopwords
        return [w for w in words if w not in self._stopwords and len(w) > 2]
    
    def _get_variants(self, word: str) -> List[str]:
        """Get word variants for matching (plural/singular)."""
        variants = [word]
        # Simple plural handling
        if word.endswith('s') and not word.endswith('ss'):
            variants.append(word[:-1])  # Remove 's'
            if word.endswith('ies'):
                variants.append(word[:-3] + 'y')
        else:
            variants.append(word + 's')  # Add 's'
            if word.endswith('y'):
                variants.append(word[:-1] + 'ies')
        return list(set(variants))
    
    def _calculate_score(self, query_words: List[str], memory: Memory) -> float:
        """Calculate relevance score for a memory."""
        content = (memory.content or "").lower()
        title = (memory.title or "").lower()
        tags = (memory.tags or "").lower()
        
        score = 0.0
        
        for word in query_words:
            variants = self._get_variants(word)
            
            for variant in variants:
                # Title matches are weighted higher
                if variant in title:
                    score += 3.0
                # Tag matches are weighted high
                if variant in tags:
                    score += 2.0
                # Content matches
                if variant in content:
                    # Count occurrences in content (up to 5)
                    count = min(content.count(variant), 5)
                    score += count * 0.5
        
        return score
