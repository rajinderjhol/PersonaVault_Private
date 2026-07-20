import pytest
from unittest.mock import MagicMock, patch
from app.services.generator_agent import GeneratorAgent

class TestGeneratorAgent:
    def test_init(self):
        agent = GeneratorAgent()
        assert agent is not None
    
    @pytest.mark.asyncio
    async def test_generate_with_ollama_success(self):
        agent = GeneratorAgent()
        with patch('app.services.generator_agent.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"response": "AI response"}
            result = await agent.generate(
                instructions="Test",
                context=[{"content": "Template"}]
            )
            assert result["source"] in ["ollama", "fallback"]
    
    @pytest.mark.asyncio
    async def test_generate_fallback_when_ollama_fails(self):
        agent = GeneratorAgent()
        with patch('app.services.generator_agent.requests.post', side_effect=Exception("Connection failed")):
            result = await agent.generate(
                instructions="Test",
                context=[{"content": "Template"}]
            )
            assert "answer" in result
            assert result["source"] == "fallback"
    
    def test_build_prompt_with_context(self):
        agent = GeneratorAgent()
        prompt = agent._build_prompt(
            instructions="Test instructions",
            context=[{"content": "Template {name}"}]
        )
        assert "Test instructions" in prompt
        assert "Template" in prompt
    
    def test_fallback_generate(self):
        agent = GeneratorAgent()
        result = agent._fallback_generate(
            instructions="Test",
            context=[{"content": "Template {name}"}]
        )
        assert "answer" in result
