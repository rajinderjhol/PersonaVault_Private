"""
Tests for AIRouter.
"""
import pytest

from app.swarm.core.router import AIRouter

class TestAIRouter:
    """Test suite for AIRouter."""
    
    def test_init(self):
        """Test AIRouter initialization."""
        router = AIRouter(engine_mode="Local-First (Ollama)")
        assert router is not None
        assert router.engine_mode == "Local-First (Ollama)"
    
    @pytest.mark.asyncio
    async def test_get_route_local_first(self):
        """Test routing in Local-First mode."""
        router = AIRouter(engine_mode="Local-First (Ollama)")
        result = await router.get_route("test query")
        assert result is not None
        assert result["provider"] == "ollama"
        assert result["tier"] == "local"

    @pytest.mark.asyncio
    async def test_get_route_high_sensitivity(self):
        """Test routing with high sensitivity."""
        router = AIRouter(engine_mode="Hybrid")
        result = await router.get_route("sensitive query", sensitivity="high")
        assert result["provider"] == "ollama"
        assert result["tier"] == "local"

    @pytest.mark.asyncio
    async def test_get_route_hybrid_complex(self):
        """Test routing in Hybrid mode with complex query."""
        router = AIRouter(engine_mode="Hybrid")
        result = await router.get_route("complex query", complexity=0.9, sensitivity="low")
        assert result["provider"] == "gemini"
        assert result["tier"] == "cloud"

if __name__ == "__main__":
    pytest.main(["-v", __file__])

