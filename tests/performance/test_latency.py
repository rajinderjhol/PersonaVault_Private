import pytest
import time
import asyncio
from runtime.pack_executor import PackExecutor

class TestPerformance:
    @pytest.mark.asyncio
    async def test_execution_latency(self):
        """Verify that pack execution is within real-time limits (< 50ms)"""
        executor = PackExecutor()
        
        # Warm up
        await executor.process_with_best_pack("test value $500", 1)
        
        latencies = []
        for i in range(20):
            start = time.perf_counter()
            await executor.process_with_best_pack(f"test value ${100 + i}", 1)
            latencies.append((time.perf_counter() - start) * 1000)
            
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        print(f"\nAvg Latency: {avg_latency:.2f}ms")
        print(f"Max Latency: {max_latency:.2f}ms")
        
        # Target: Average latency should be under 10ms for these simple compiled packs
        assert avg_latency < 10, f"Average latency {avg_latency:.2f}ms exceeds 10ms target"
        assert max_latency < 50, f"Max latency {max_latency:.2f}ms exceeds 50ms threshold"
