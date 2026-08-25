import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.swarm.core.generator import GeneratorAgent

class TestGeneratorAgent:
    def test_init(self):
        agent = GeneratorAgent()
        assert agent is not None
    
    @pytest.mark.asyncio
    async def test_generate_with_groq_success(self):
        agent = GeneratorAgent()
        # Set groq key to simulate capability
        agent.groq_key = "test_key"
        
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {
            "choices": [{"message": {"content": "AI response"}}]
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_res
            result = await agent.generate(
                query="Test",
                context=[{"content": "Template"}]
            )
            assert result["source"] == "groq"
            assert result["answer"] == "AI response"
            assert "trace" in result
            assert result["trace"]["agent"] == "generator"
    
    @pytest.mark.asyncio
    async def test_generate_fallback_when_all_fails(self):
        agent = GeneratorAgent()
        agent.groq_key = None # Force fallback
        
        result = await agent.generate(
            query="Test",
            context=[{"content": "Template"}]
        )
        assert "answer" in result
        assert result["source"] == "fallback"
        assert "trace" in result

if __name__ == "__main__":
    pytest.main(["-v", __file__])
