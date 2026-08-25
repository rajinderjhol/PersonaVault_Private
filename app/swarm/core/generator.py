"""
Generator Agent - Supports streaming and Auditable Traces
"""
import logging
import json
import httpx
import os
from typing import Dict, Any, Optional, AsyncGenerator, List
from app.swarm.base import BaseAgent

logger = logging.getLogger(__name__)

class GeneratorAgent(BaseAgent):
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        super().__init__("generator", client)
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_LLM_MODEL", "tinydolphin")
        logger.info("GeneratorAgent initialized")
    
    async def generate_stream(
        self, 
        query: str, 
        provider: str = "groq",
        context: Optional[List[Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream generation from the provider with injected context"""
        logger.info(f"GeneratorAgent received context with {len(context) if context else 0} items.")
        
        # Ensure context items are strings
        safe_context = []
        if context:
            for item in context:
                if isinstance(item, dict):
                    safe_context.append(item.get("content", str(item)))
                else:
                    safe_context.append(str(item))
        
        # Construct structured prompt
        if safe_context:
            context_str = "\n".join(safe_context)
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
    
    async def generate(self, query: str, context: list = None, **kwargs) -> Dict[str, Any]:
        """Non-streaming generation with context and Auditable Trace"""
        
        # Ensure context items are strings
        safe_context = []
        if context:
            for item in context:
                if isinstance(item, dict):
                    safe_context.append(item.get("content", str(item)))
                else:
                    safe_context.append(str(item))
        
        # Construct structured prompt
        if safe_context:
            context_str = "\n".join(safe_context)
            full_prompt = f"""## Relevant Context / Memories
{context_str}

## User Query
{query}

Please answer based on the provided context.
"""
        else:
            full_prompt = query
            
        answer = "I'm having trouble generating a response. Please try again."
        source = "fallback"
        confidence = 0.3

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
                        answer = content
                        source = "groq"
                        confidence = 0.9
            except Exception as e:
                logger.error(f"Groq generation failed: {e}")
        
        # Generate trace
        trace = self.create_trace(
            input_data=query,
            explanation=f"Generated answer via {source}",
            confidence=confidence,
            decision="generate_response"
        )

        return {
            "answer": answer, 
            "source": source, 
            "confidence": confidence,
            "trace": trace
        }
