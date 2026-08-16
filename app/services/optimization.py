"""
Optimization Service for Constrained Environments
"""
import gc
import asyncio
import psutil
import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OptimizationService:
    """Optimizes resource usage in constrained environments."""
    
    def __init__(self):
        self.memory_limit_mb = 1536  # 1.5 GB
        self._semaphore = asyncio.Semaphore(2)  # Max 2 concurrent requests
    
    async def execute_with_limit(self, coro):
        """Execute a coroutine with concurrency limit."""
        async with self._semaphore:
            return await coro
    
    def check_memory(self) -> bool:
        """Check if memory is within limits."""
        mem = psutil.virtual_memory()
        used_mb = mem.used / (1024 * 1024)
        if used_mb > self.memory_limit_mb:
            logger.warning(f"Memory usage high: {used_mb:.0f}MB")
            self._clear_memory()
            return False
        return True
    
    def _clear_memory(self):
        """Clear memory by running garbage collection."""
        gc.collect()
        logger.info("🧹 Garbage collection triggered")
