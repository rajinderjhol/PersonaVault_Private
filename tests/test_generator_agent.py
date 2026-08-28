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

    @pytest.mark.asyncio
    async def test_generate_stream_groq_success(self):
        agent = GeneratorAgent()
        agent.groq_key = "test_key"
        
        # Mock SSE response for Groq
        mock_response_lines = [
            'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            'data: {"choices": [{"delta": {"content": " world"}}]}',
            'data: [DONE]'
        ]
        
        async def mock_aiter_lines():
            for line in mock_response_lines:
                yield line

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = mock_aiter_lines
        
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        
        with patch("httpx.AsyncClient.stream", return_value=mock_stream_ctx):
            chunks = []
            async for chunk in agent.generate_stream(query="Hi", provider="groq"):
                chunks.append(chunk)
            
            assert "".join(chunks) == "Hello world"

    @pytest.mark.asyncio
    async def test_generate_stream_ollama_success(self):
        agent = GeneratorAgent()
        
        # Mock Ollama streaming response
        mock_response_lines = [
            '{"response": "Ollama", "done": false}',
            '{"response": " says", "done": false}',
            '{"response": " hi", "done": true}'
        ]
        
        async def mock_aiter_lines():
            for line in mock_response_lines:
                yield line

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = mock_aiter_lines
        
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        
        with patch("httpx.AsyncClient.stream", return_value=mock_stream_ctx):
            chunks = []
            async for chunk in agent.generate_stream(query="Hi", provider="ollama"):
                chunks.append(chunk)
            
            assert "".join(chunks) == "Ollama says hi"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
