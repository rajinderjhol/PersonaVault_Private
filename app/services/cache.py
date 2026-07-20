"""
Semantic caching service for query results.
"""
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class SemanticCache:
    """Simple semantic cache for query results."""
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        self.cache: Dict[str, Dict] = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        logger.info(f"SemanticCache initialized with TTL={ttl_seconds}s, max_size={max_size}")
    
    def _get_key(self, query: str) -> str:
        """Generate cache key from query."""
        return hashlib.md5(query.encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Any]:
        """Get cached result if exists and not expired."""
        key = self._get_key(query)
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() - entry["timestamp"] < timedelta(seconds=self.ttl):
                self.hits += 1
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return entry["value"]
            else:
                del self.cache[key]
        self.misses += 1
        logger.debug(f"Cache miss for query: {query[:50]}...")
        return None
    
    def set(self, query: str, value: Any):
        """Cache a result."""
        key = self._get_key(query)
        
        # Evict oldest if at max size
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
            logger.debug(f"Evicted oldest cache entry: {oldest_key}")
        
        self.cache[key] = {
            "value": value,
            "timestamp": datetime.now()
        }
        logger.debug(f"Cached query: {query[:50]}...")
    
    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")
    
    def stats(self) -> Dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        return {
            "size": len(self.cache),
            "ttl": self.ttl,
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0
        }
    
    def remove(self, query: str):
        """Remove specific query from cache."""
        key = self._get_key(query)
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Removed query from cache: {query[:50]}...")
    
    def get_all(self) -> Dict[str, Dict]:
        """Get all cached entries (for debugging)."""
        return {
            key: {
                "value": entry["value"],
                "timestamp": entry["timestamp"].isoformat()
            }
            for key, entry in self.cache.items()
        }

# Global instance
cache_service = SemanticCache()
