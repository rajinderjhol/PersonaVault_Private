import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

class WorkingMemory:
    """Layer 1 Memory - Volatile Context (Gas) with eviction and TTL."""
    def __init__(self, ttl_seconds: int = 600, max_size: int = 50):
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, datetime] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size

    def set(self, key: str, value: Any):
        """Store a value with a new expiration timestamp."""
        if len(self._data) >= self._max_size:
            self._evict_oldest()
            
        self._data[key] = value
        self._expiry[key] = datetime.now(timezone.utc) + timedelta(seconds=self._ttl)

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value if not expired."""
        if key not in self._data:
            return None
            
        if datetime.now(timezone.utc) > self._expiry[key]:
            self.delete(key)
            return None
            
        return self._data[key]

    def delete(self, key: str):
        self._data.pop(key, None)
        self._expiry.pop(key, None)

    def _evict_oldest(self):
        """Removes the oldest entry based on expiry time."""
        if not self._expiry:
            return
        oldest_key = min(self._expiry, key=self._expiry.get)
        self.delete(oldest_key)