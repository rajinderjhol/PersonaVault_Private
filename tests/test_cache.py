import pytest
from app.services.cache import SemanticCache

def test_cache_set_get():
    cache = SemanticCache(ttl_seconds=1)
    cache.set("test", "value")
    assert cache.get("test") == "value"

def test_cache_expiry():
    cache = SemanticCache(ttl_seconds=0)
    cache.set("test", "value")
    assert cache.get("test") is None

def test_cache_stats():
    cache = SemanticCache()
    cache.set("q1", "v1")
    cache.get("q1")
    cache.get("q2")
    stats = cache.stats()
    assert stats["size"] == 1
    assert stats["hits"] == 1
    assert stats["misses"] == 1
