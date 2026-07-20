from rank_bm25 import BM25Okapi
from typing import List, Dict, Any # Ensure typing is imported
import logging # Ensure logging is imported

logger = logging.getLogger(__name__)

class KeywordSearch:
    """BM25-based keyword search for exact matching."""
    
    def __init__(self):
        self.index = None
        self.metadata = []
    
    def build_index(self, documents: List[Dict[str, Any]]):
        """Build BM25 index from provided memories."""
        if not documents:
            return
        
        tokenized_corpus = [doc["content"].lower().split() for doc in documents]
        self.index = BM25Okapi(tokenized_corpus)
        self.metadata = documents
        logger.info(f"Built BM25 index with {len(documents)} documents")
    
    def search(self, query: str, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for documents matching query terms."""
        if not self.index:
            return []
        
        tokenized_query = query.lower().split()
        scores = self.index.get_scores(tokenized_query)
        
        # Rank results by score
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        max_score = max(scores) if any(scores) else 1.0
        for idx, score in indexed_scores[:limit]:
            doc = self.metadata[idx]
            if doc.get("user_id") == user_id or user_id == 0:
                results.append({
                    "id": doc.get("id"),
                    "content": doc.get("content"),
                    "score": score / max_score
                })
        
        return results