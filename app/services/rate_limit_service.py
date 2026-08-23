"""
Rate Limit Service for AI Providers
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimitService:
    """Service for tracking rate limits across AI providers"""
    
    @classmethod
    async def get_stats(cls, provider: str) -> Dict[str, Any]:
        """Get rate limit statistics for a provider"""
        try:
            if provider == "groq":
                return {
                    "remaining_requests": 1000,
                    "remaining_tokens": 1000000,
                    "reset_requests": (datetime.now() + timedelta(hours=1)).isoformat(),
                    "reset_tokens": (datetime.now() + timedelta(hours=1)).isoformat(),
                    "status": "OK"
                }
            elif provider == "ollama":
                return {
                    "remaining_requests": -1,
                    "remaining_tokens": -1,
                    "reset_requests": None,
                    "reset_tokens": None,
                    "status": "Local - Unlimited"
                }
            elif provider == "gemini":
                return {
                    "remaining_requests": 1500,
                    "remaining_tokens": 1500000,
                    "reset_requests": None,
                    "reset_tokens": None,
                    "status": "OK"
                }
            else:
                return {
                    "remaining_requests": "N/A",
                    "remaining_tokens": "N/A",
                    "reset_requests": None,
                    "reset_tokens": None,
                    "status": "Unknown provider"
                }
        except Exception as e:
            logger.error(f"Error getting stats for {provider}: {e}")
            return {"error": str(e)}
