"""
Generator Agent - Supports streaming and Auditable Traces
"""
import logging
import json
import httpx
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator, List
from app.swarm.base import BaseAgent
from app.swarm.routing.reasoning_router import ReasoningRouter
from app.services.memory.ice_repository import IceMemoryRepository

logger = logging.getLogger(__name__)

class GeneratorAgent(BaseAgent):
    def __init__(self, client: Optional[httpx.AsyncClient] = None, session_factory: Any = None):
        super().__init__("generator", client)
        from app.db.session import SessionLocal
        self.session_factory = session_factory or SessionLocal
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_LLM_MODEL", "tinydolphin")
        self.router = ReasoningRouter()
        self.ice_repo = IceMemoryRepository(self.session_factory)
        self._last_provider_used = "unknown"
        self._last_model_used = "unknown"
        logger.info(f"GeneratorAgent initialized (airgapped: {self.router.airgapped})")
    
    async def generate_stream(
        self, 
        query: str, 
        provider: str = "auto",
        context: Optional[List[Any]] = None,
        user_id: int = 1
    ) -> AsyncGenerator[str, None]:
        """Stream generation from the provider with injected context"""
        
        # Determine routing
        if provider == "auto":
            chosen_provider, route_metadata = await self.router.route(query, context)
            logger.info(f"Auto-routed to {chosen_provider}: {route_metadata}")
            target_model = route_metadata.get("model")
        else:
            chosen_provider = provider
            route_metadata = {"mode": "manual", "provider": provider, "complexity": {"score": 0.5}}
            target_model = None

        self._last_provider_used = chosen_provider
        self._last_model_used = target_model or (self.ollama_model if chosen_provider == "ollama" else "qwen/qwen3.6-27b")

        logger.info(f"GeneratorAgent using {chosen_provider} (model: {target_model}) received context with {len(context) if context else 0} items.")
        
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

        full_response_chunks = []
        if chosen_provider == "ollama":
            async for chunk in self._stream_ollama(full_prompt, model=target_model):
                full_response_chunks.append(chunk)
                yield chunk
        elif chosen_provider == "groq":
            async for chunk in self._stream_groq(full_prompt, model=target_model):
                full_response_chunks.append(chunk)
                yield chunk
        else:
            yield f"Unknown provider: {chosen_provider}"

        # After streaming completes, check if we should crystallize
        if route_metadata.get("mode") == "reasoning":
            full_response = "".join(full_response_chunks)
            await self._crystallize_reasoning(
                query=query,
                reasoning_path=full_prompt,
                response=full_response,
                complexity=route_metadata.get("complexity", {}),
                user_id=user_id
            )
            logger.info("🧠 Reasoning crystallized to Layer 3")
    
    async def generate(self, query: str, context: list = None, **kwargs) -> Dict[str, Any]:
        """Non-streaming generation with context and Auditable Trace"""
        
        user_id = kwargs.get("user_id", 1)
        # Auto-route if provider not specified or is 'auto'
        provider = kwargs.get("provider", "auto")
        if provider == "auto":
            chosen_provider, route_metadata = await self.router.route(query, context)
            target_model = route_metadata.get("model")
        else:
            chosen_provider = provider
            route_metadata = {"mode": "manual", "provider": provider, "complexity": {"score": 0.5}}
            target_model = None

        self._last_provider_used = chosen_provider
        self._last_model_used = target_model or (self.ollama_model if chosen_provider == "ollama" else "qwen/qwen3.6-27b")

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
        if chosen_provider == "groq" and self.groq_key:
            try:
                model_name = target_model or "qwen/qwen3.6-27b"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.groq_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model_name,
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
        elif chosen_provider == "ollama":
             try:
                model_name = target_model or self.ollama_model
                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.post(
                        f"{self.ollama_url}/api/generate",
                        json={
                            "model": model_name,
                            "prompt": full_prompt,
                            "stream": False
                        }
                    )
                    if res.status_code == 200:
                        answer = res.json().get("response", "")
                        source = "ollama"
                        confidence = 0.8
             except Exception as e:
                logger.error(f"Ollama generation failed: {e}")
        
        # Crystallize reasoning if mode was reasoning
        if route_metadata.get("mode") == "reasoning":
            await self._crystallize_reasoning(
                query=query,
                reasoning_path=full_prompt,
                response=answer,
                complexity=route_metadata.get("complexity", {}),
                user_id=user_id
            )
            logger.info("🧠 Reasoning crystallized to Layer 3")

        # Generate trace with routing metadata
        trace = self.create_trace(
            input_data=query,
            explanation=f"Generated answer via {source}",
            confidence=confidence,
            decision="generate_response",
            metadata=route_metadata
        )

        return {
            "answer": answer, 
            "source": source, 
            "confidence": confidence,
            "trace": trace
        }

    async def _crystallize_reasoning(
        self, 
        query: str, 
        reasoning_path: str, 
        response: str, 
        complexity: Dict[str, Any],
        user_id: int = 1
    ) -> Optional[str]:
        """
        Promote a successful reasoning path to Layer 3 (Ice Memory).
        Returns the memory ID if successful.
        """
        try:
            # 1. Extract the reasoning pattern
            reasoning_pattern = await self._extract_reasoning_pattern(
                query, reasoning_path, response
            )
            
            # 2. Check if this pattern already exists (avoid duplicates)
            existing = await self._find_similar_crystallized_pattern(reasoning_pattern, user_id)
            if existing and existing.get("score", 0) > 0.9:
                logger.info(f"Crystallized pattern already exists with score {existing['score']}")
                return str(existing.get("id"))
            
            # 3. Store in Layer 3 (Ice Memory)
            memory_record = {
                "type": "crystallized_reasoning",
                "layer": 3,  # Ice
                "user_id": user_id,
                "trigger": query[:200], # Trigger for SQL search
                "correction": response,
                "confidence": self._calculate_pattern_confidence(reasoning_path),
                "raw_text": f"Query: {query}\nReasoning: {reasoning_path}\nAnswer: {response}",
                "content": {
                    "query_pattern": query,
                    "reasoning_path": reasoning_path,
                    "response": response,
                    "complexity_score": complexity.get("score", 0),
                    "complexity_signals": complexity.get("signals", {}),
                    "provider_used": self._last_provider_used,
                    "model_used": self._last_model_used,
                    "timestamp": datetime.now().isoformat()
                },
                "metadata": {
                    "crystallized_from": "reasoning_session",
                    "replay_count": 0,
                    "success_rate": 1.0,
                    "semantic_version": "1.0"
                }
            }
            
            # Store in Ice Memory repository
            memory_id = await self.ice_repo.store(memory_record)
            
            logger.info(f"✅ Crystallized reasoning pattern: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to crystallize reasoning: {e}")
            return None
    
    async def _extract_reasoning_pattern(
        self, 
        query: str, 
        reasoning_path: str, 
        response: str
    ) -> Dict[str, Any]:
        """
        Extract the essential reasoning pattern from a deep thought session.
        """
        # Simple keyword extraction
        keywords = re.findall(r'\b\w{4,}\b', query + " " + reasoning_path)
        
        return {
            "summary": f"Reasoning about: {query[:100]}...",
            "keywords": list(set(keywords))[:20],
            "reasoning_depth": self._calculate_reasoning_depth(reasoning_path),
            "response_length": len(response)
        }
    
    def _calculate_reasoning_depth(self, reasoning_path: str) -> float:
        """
        Calculate how "deep" the reasoning was.
        """
        decision_markers = ["therefore", "however", "moreover", "consequently", "because", "since", "so"]
        count = sum(1 for marker in decision_markers if marker in reasoning_path.lower())
        return min(count / 10, 1.0)
    
    def _calculate_pattern_confidence(self, reasoning_path: str) -> float:
        """
        Calculate confidence based on reasoning path coherence.
        """
        base = min(len(reasoning_path) / 1000, 0.8)
        return min(base + 0.1, 1.0)
    
    async def _find_similar_crystallized_pattern(self, pattern: Dict[str, Any], user_id: int) -> Optional[Dict]:
        """
        Check if a similar reasoning pattern already exists in Layer 3.
        """
        try:
            similar = await self.ice_repo.search_similar(
                query=pattern["summary"],
                threshold=0.85,
                limit=1,
                user_id=user_id
            )
            return similar[0] if similar else None
        except Exception as e:
            logger.error(f"Error finding similar pattern: {e}")
            return None

    async def _stream_groq(self, prompt: str, model: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Internal helper for streaming from Groq API"""
        if not self.groq_key:
            yield "[Error: Groq API Key not found]"
            return

        try:
            model_name = model or "qwen/qwen3.6-27b"
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 1024,
                        "stream": True
                    }
                ) as response:
                    if response.status_code != 200:
                        yield f"[Error: Groq API returned {response.status_code}]"
                        return

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                chunk = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if chunk:
                                    yield chunk
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Groq stream failed: {e}")
            yield f"[Error: {str(e)}]"

    async def _stream_ollama(self, prompt: str, model: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Internal helper for streaming from Ollama local API"""
        try:
            model_name = model or self.ollama_model
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": True
                    }
                ) as response:
                    if response.status_code != 200:
                        yield f"[Error: Ollama API returned {response.status_code}]"
                        return

                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                chunk = data.get("response", "")
                                if chunk:
                                    yield chunk
                                if data.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Ollama stream failed: {e}")
            yield f"[Error: {str(e)}]"
