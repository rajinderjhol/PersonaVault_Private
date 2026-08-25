"""
Generator Agent - Supports streaming
"""
import logging
import json
import httpx
import os
from typing import Dict, Any, Optional, AsyncGenerator, List

logger = logging.getLogger(__name__)

class GeneratorAgent:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.client = client or httpx.AsyncClient()
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_LLM_MODEL", "tinydolphin")
        logger.info("GeneratorAgent initialized")
    
    async def generate_stream(
        self, 
        query: str, 
        provider: str = "groq",
        context: Optional[List[str]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream generation from the provider with injected context"""
        
        # Construct structured prompt
        if context:
            context_str = "\n".join(context)
            full_prompt = f"""## Relevant Context / Memories
{context_str}

## User Query
{query}

Please answer based on the provided context.
"""
        else:
            full_prompt = query

        if provider == "ollama":
            async for chunk in self._stream_ollama(full_prompt):
                yield chunk
        elif provider == "groq":
            async for chunk in self._stream_groq(full_prompt):
                yield chunk
        else:
            yield f"Unknown provider: {provider}"
    
    async def _stream_ollama(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream from Ollama"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": True
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if data.get("response"):
                                    yield data["response"]
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            yield f"Error: {str(e)}"
    
    async def _stream_groq(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream from Groq"""
        if not self.groq_key:
            yield "GROQ_API_KEY not set"
            return
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "qwen/qwen3.6-27b",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 500,
                        "stream": True
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if line and line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Groq streaming failed: {e}")
            yield f"Error: {str(e)}"
    
    async def generate(self, query: str, context: list = None, **kwargs) -> Dict[str, Any]:
        """Non-streaming generation with context"""
        
        # Construct structured prompt
        if context:
            context_str = "\n".join(context)
            full_prompt = f"""## Relevant Context / Memories
{context_str}

## User Query
{query}

Please answer based on the provided context.
"""
        else:
            full_prompt = query
            
        # Use Groq for non-streaming
        if self.groq_key:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.groq_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "qwen/qwen3.6-27b",
                            "messages": [{"role": "user", "content": full_prompt}],
                            "temperature": 0.7,
                            "max_tokens": 500
                        }
                    )
                    if res.status_code == 200:
                        content = res.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                        return {"answer": content, "source": "groq", "confidence": 0.9}
            except Exception as e:
                logger.error(f"Groq generation failed: {e}")
        
        # Fallback
        return {"answer": "I'm having trouble generating a response. Please try again.", "source": "fallback", "confidence": 0.3}
