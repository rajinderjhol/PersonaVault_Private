"""
Safe Caching with Surgical Invalidation
"""
import json
import hashlib
import time
from typing import Dict, Any, Optional
from collections import OrderedDict

class SafeCache:
    """
    Cache with surgical invalidation and versioning.
    """
    
    def __init__(self, max_size=100, default_ttl=300):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.version = 1
    
    def _get_key(self, query: str, context: Dict = None) -> str:
        """Generate cache key with version and config awareness."""
        from app.services.intelligence_gateway import gateway
        
        # Get current provider and model
        provider = context.get("provider", "ollama") if context else "ollama"
        model = gateway.ai_tool.providers.get(provider, {}).get("model", "unknown")
        
        key_data = {
            "query": query,
            "provider": provider,
            "model": model,
            "version": self.version,
            "user": context.get("user_id", "anonymous") if context else "anonymous"
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value with TTL check."""
        if key in self.cache:
            value, timestamp, version = self.cache[key]
            if version == self.version and (time.time() - timestamp) < self.default_ttl:
                self.cache.move_to_end(key)
                return value
            del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set cached value with current version."""
        if len(self.cache) >= self.max_size:
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        self.cache[key] = (value, time.time(), self.version)
    
    def invalidate_all(self):
        """Invalidate all cache - use sparingly!"""
        self.version += 1
        self.cache.clear()
    
    def invalidate_provider(self, provider: str):
        """Surgically invalidate cache for a specific provider."""
        keys_to_remove = []
        for key in self.cache:
            if f'"{provider}"' in key or f':{provider}:' in key:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self.cache[key]
    
    def invalidate_model(self, provider: str, model: str):
        """Surgically invalidate cache for a specific model."""
        keys_to_remove = []
        target = f'{provider}:{model}'
        for key in self.cache:
            if target in key:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self.cache[key]
    
    def invalidate_user(self, user_id: int):
        """Surgically invalidate cache for a specific user."""
        keys_to_remove = []
        target = f'"user":{user_id}'
        for key in self.cache:
            if target in key:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self.cache[key]
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "version": self.version,
            "ttl": self.default_ttl,
            "keys": list(self.cache.keys())[:5]
        }
