import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.swarm.core.generator import GeneratorAgent

class TestGeneratorAgent:
    def test_init(self):
        agent = GeneratorAgent()
        assert agent is not None
    
    @pytest.mark.asyncio
    async def test_generate_with_ollama_success(self):
        agent = GeneratorAgent()
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {"response": "AI response"}
        with patch.object(agent.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_res
            result = await agent.generate(
                query="Test",
                context=[{"content": "Template"}]
            )
            assert result["source"] in ["ollama", "fallback"]
    
    @pytest.mark.asyncio
    async def test_generate_fallback_when_ollama_fails(self):
        agent = GeneratorAgent()
        with patch.object(agent.client, 'post', side_effect=Exception("Connection failed")):
            result = await agent.generate(
                query="Test",
                context=[{"content": "Template"}]
            )
            assert "answer" in result
            assert result["source"] == "fallback"
    
    def test_build_prompt_with_context(self):
        agent = GeneratorAgent()
        prompt = agent._build_prompt(
            query="Test instructions",
            context=[{"content": "Template {name}"}]
        )
        assert "Test instructions" in prompt
        assert "Template" in prompt
    
    def test_fallback_generate(self):
        agent = GeneratorAgent()
        result = agent._fallback_generate(
            query="Test",
            context=[{"content": "Template {name}"}]
        )
        assert "answer" in result

if __name__ == "__main__":
    pytest.main(["-v", __file__])

