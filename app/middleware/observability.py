"""
Observability Middleware - Tracks memory hit rates, token efficiency, and governance latency.
"""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Tracks performance metrics for each request.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip for WebSockets
        if request.scope.get("type") == "websocket":
            return await call_next(request)

        # Start timing
        start_time = time.time()
        
        # Track memory hits (placeholder logic for now)
        # In a real implementation, these would be tracked via a shared context or service
        memory_hits = 0
        memory_misses = 0
        
        # Track token usage (placeholder)
        tokens_used = 0
        
        # Process the request
        response = await call_next(request)
        
        # Calculate metrics
        duration_ms = (time.time() - start_time) * 1000
        
        # Calculate memory hit rate
        total_memory_requests = memory_hits + memory_misses
        memory_hit_rate = memory_hits / total_memory_requests if total_memory_requests > 0 else 0
        
        # Add metrics to response headers
        response.headers["X-Memory-Hit-Rate"] = str(memory_hit_rate)
        response.headers["X-Duration-Ms"] = str(duration_ms)
        
        # Log metrics
        logger.info(f"📊 Metrics: Path={request.url.path} Duration={duration_ms:.2f}ms, Memory Hit Rate={memory_hit_rate:.2f}")
        
        return response
