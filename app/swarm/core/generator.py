"""
Generator Agent - Supports streaming with intelligence packs integration
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
        self._packs = []
        logger.info("GeneratorAgent initialized")
    
    def set_packs(self, packs: List[Dict]):
        """Set intelligence packs for context enhancement."""
        self._packs = packs
        logger.info(f"GeneratorAgent loaded {len(packs)} packs")
    
    def _build_pack_context(self, query: str) -> str:
        """Build context from intelligence packs based on query."""
        if not self._packs:
            return ""
        
        context_parts = []
        query_lower = query.lower()
        
        for pack in self._packs:
            if not pack.get('is_active', True):
                continue
            
            pack_name = pack.get('name', '').lower()
            pack_domain = pack.get('domain', '').lower()
            pack_desc = pack.get('description', '').lower()
            
            # Check relevance
            relevance_score = 0
            if pack_domain in query_lower:
                relevance_score += 3
            if any(word in query_lower for word in pack_name.split()):
                relevance_score += 2
            if any(word in query_lower for word in pack_desc.split()[:10]):
                relevance_score += 1
            
            if relevance_score >= 2:
                context_parts.append(f"--- {pack.get('name')} Pack ---")
                context_parts.append(f"Domain: {pack.get('domain')}")
                context_parts.append(f"Description: {pack.get('description')}")
                
                # Add entities if available
                entities = pack.get('entities', [])
                if entities:
                    # Extract names from entity dictionaries or use as-is if strings
                    entity_names = []
                    for entity in entities[:5]:
                        if isinstance(entity, dict):
                            # Get 'name' field, fallback to 'id' or 'label'
                            name = entity.get('name', entity.get('id', entity.get('label', '')))
                            if name:
                                entity_names.append(str(name))
                            # Also include examples if available
                            examples = entity.get('examples', [])
                            if examples and isinstance(examples, list):
                                for ex in examples[:2]:
                                    if isinstance(ex, str):
                                        entity_names.append(f"({ex})")
                        elif isinstance(entity, str):
                            entity_names.append(entity)
                    if entity_names:
                        context_parts.append(f"Key concepts: {', '.join(entity_names)}")
                    else:
                        # Fallback: show the first few entities as JSON strings
                        context_parts.append(f"Key concepts: {str(entities[:3])}")
                context_parts.append("")
        
        return "\n".join(context_parts) if context_parts else ""
    
    async def generate(
        self, 
        query: str, 
        context: list = None, 
        provider: str = "groq",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a response using intelligence packs for context."""
        try:
            # Build pack context
            pack_context = self._build_pack_context(query)
            
            # Build the full prompt with context
            full_prompt = query
            if pack_context:
                full_prompt = f"""Use the following domain intelligence to answer the question. 
If the question can be answered using this context, use it. Otherwise, use your general knowledge.

{pack_context}

Question: {query}

Answer:"""
            
            logger.info(f"🧠 Generator using pack context: {len(pack_context)} chars")
            
            # Try Groq first
            if provider == "groq" and self.groq_key:
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
                                "messages": [
                                    {"role": "system", "content": "You are PersonaVault, an AI assistant specialized in contract intelligence, security, compliance, and domain-specific knowledge. Use the provided context when available."},
                                    {"role": "user", "content": full_prompt}
                                ],
                                "temperature": 0.7,
                                "max_tokens": 1000
                            }
                        )
                        if res.status_code == 200:
                            content = res.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                            return {
                                "answer": content, 
                                "source": "groq",
                                "confidence": 0.9,
                                "pack_context_used": bool(pack_context)
                            }
                except Exception as e:
                    logger.error(f"Groq generation failed: {e}")
            
            # Fallback to Ollama
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    res = await client.post(
                        f"{self.ollama_url}/api/generate",
                        json={
                            "model": self.ollama_model,
                            "prompt": full_prompt,
                            "stream": False,
                            "options": {"temperature": 0.7}
                        }
                    )
                    if res.status_code == 200:
                        content = res.json().get("response", "")
                        return {
                            "answer": content,
                            "source": "ollama",
                            "confidence": 0.7,
                            "pack_context_used": bool(pack_context)
                        }
            except Exception as e:
                logger.error(f"Ollama generation failed: {e}")
            
            # Final fallback
            return {
                "answer": "I'm having trouble generating a response. Please try again.",
                "source": "fallback",
                "confidence": 0.3,
                "pack_context_used": bool(pack_context)
            }
            
        except Exception as e:
            logger.error(f"Generator error: {e}")
            return {"answer": f"[Error: {str(e)}]", "source": "error", "confidence": 0.0}
    
    async def generate_stream(
        self, 
        query: str, 
        provider: str = "groq",
        context: str = "",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generation from the provider with pack context."""
        
        # Build pack context
        pack_context = self._build_pack_context(query)
        
        # Build the full prompt with context
        full_prompt = query
        if pack_context:
            full_prompt = f"""Use the following domain intelligence to answer the question.
If the question can be answered using this context, use it. Otherwise, use your general knowledge.

{pack_context}

Question: {query}

Answer:"""
        
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
                        "messages": [
                            {"role": "system", "content": "You are PersonaVault, an AI assistant with domain intelligence."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000,
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
