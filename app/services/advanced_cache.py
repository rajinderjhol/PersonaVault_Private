"""
Advanced Caching Service with Smart Invalidation
"""
import json
import time
import hashlib
from typing import Dict, Any, Optional
from collections import OrderedDict

class AdvancedCache:
    """
    Multi-level cache with TTL, LRU, and pattern-based invalidation.
    """
    
    def __init__(self, max_size=100, default_ttl=300):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    def _get_key(self, query: str, context: Dict = None) -> str:
        """Generate a cache key from query and context."""
        key_data = {"query": query, "context": context or {}}
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get a cached value with TTL check."""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.default_ttl:
                # Move to end (LRU)
                self.cache.move_to_end(key)
                self.hits += 1
                return value
            del self.cache[key]
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any):
        """Set a cached value."""
        if len(self.cache) >= self.max_size:
            # Remove oldest (LRU)
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        self.cache[key] = (value, time.time())
    
    def get_or_compute(self, query: str, compute_func, context: Dict = None) -> Any:
        """Get from cache or compute and cache."""
        key = self._get_key(query, context)
        cached = self.get(key)
        if cached is not None:
            return cached
        result = compute_func(query, context)
        self.set(key, result)
        return result
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern."""
        keys_to_remove = [k for k in self.cache if pattern in k]
        for k in keys_to_remove:
            del self.cache[k]
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0,
            "ttl": self.default_ttl
        }
