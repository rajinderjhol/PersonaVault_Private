import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.discovery.benchmarker import CompressionBenchmarker

@pytest.mark.asyncio
async def test_compression_benchmark():
    benchmarker = CompressionBenchmarker()
    
    env_id = "env-test-001"
    raw_memories = [
        {"id": 1, "content": "Security alert: failed login from IP 1.2.3.4"},
        {"id": 2, "content": "Security alert: failed login from IP 5.6.7.8"},
        {"id": 3, "content": "Security alert: failed login from IP 9.0.1.2"}
    ]
    
    meta_patterns = [
        {"id": "meta-1", "content": "META: Multiple failed login attempts observed across distinct IPs.", "metadata": {"type": "meta_pattern"}}
    ]
    
    result = await benchmarker.run_benchmark(env_id, raw_memories, meta_patterns)
    
    assert result["environment_id"] == env_id
    assert result["metrics"]["raw_event_count"] == 3
    assert result["metrics"]["meta_pattern_count"] == 1
    assert result["metrics"]["logical"]["ratio"] == 3.0
    assert result["metrics"]["storage"]["ratio"] > 1.0
    
    print("\n✅ Compression benchmark verified.")

if __name__ == "__main__":
    asyncio.run(test_compression_benchmark())
