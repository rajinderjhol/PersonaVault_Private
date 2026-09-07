"""
Generator Agent - Supports streaming and Auditable Traces with Domain Awareness
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
from app.swarm.routing.domain_router import DomainRouter
from app.services.memory.ice_repository import IceMemoryRepository
from app.services.lineage.lineage_service import LineageService
from app.models.lineage import SourceType
from app.services.trace_service import TraceStep

logger = logging.getLogger(__name__)

class GeneratorAgent(BaseAgent):
    def __init__(self, client: Optional[httpx.AsyncClient] = None, session_factory: Any = None):
        super().__init__("generator", client)
        from app.db.session import SessionLocal
        self.session_factory = session_factory or SessionLocal
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_LLM_MODEL", "tinydolphin:latest")
        self.router = ReasoningRouter()
        self.domain_router = DomainRouter()
        self.ice_repo = IceMemoryRepository(self.session_factory)
        self.lineage_service = LineageService(self.session_factory)
        self._last_provider_used = "unknown"
        self._last_model_used = "unknown"
        self.memory_layer = None
        self.confidence = 0
        self.pattern_id = None
        logger.info(f"GeneratorAgent initialized (airgapped: {self.router.airgapped})")
        logger.info(f"Available domains: {list(self.domain_router.detector.pack_keywords.keys())}")

    async def generate_stream(
        self, 
        prompt: str, 
        context: dict,
        memory_service: Any,
        yield_chunk: callable
    ):
        """Generate response with memory layer attribution"""
        
        # 1. Check for crystallized patterns first (ICE layer)
        pattern = await memory_service.find_crystallized_pattern(prompt, context)
        
        if pattern and pattern.confidence > 0.85:
            # Using ICE layer (10,000:1 compression)
            self.memory_layer = "ice"
            self.confidence = pattern.confidence
            self.pattern_id = pattern.id
            
            # Send memory attribution first
            await yield_chunk({
                "type": "memory",
                "data": {
                    "layer": self.memory_layer,
                    "confidence": int(self.confidence * 100),
                    "source": f"Pattern: {pattern.name}",
                    "patternId": self.pattern_id
                }
            })
            
            # Then stream the response (placeholder for pattern streaming)
            await yield_chunk({"type": "text", "data": "Pattern applied: " + pattern.name})
                
        else:
            # 2. Check liquid memory (recent context)
            self.memory_layer = "gas"
            self.confidence = 0.6
            await yield_chunk({
                "type": "memory",
                "data": {
                    "layer": self.memory_layer,
                    "confidence": int(self.confidence * 100),
                    "source": "Working memory (current session)"
                }
            })
                
            # Stream direct inference
            async for chunk in self.generate_stream_with_trace(query=prompt, context=context.get("context")):
                if chunk.get("type") == "content":
                    await yield_chunk({"type": "text", "data": chunk.get("content")})
        
        # Send completion
        await yield_chunk({"type": "complete", "data": None})
    
    async def generate_stream_with_trace(
        self, 
        query: str, 
        provider: str = "auto",
        context: Optional[List[Any]] = None,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream generation with structured decision trace and domain awareness.
        
        Yields:
            Dict with 'content' (chunk) and 'trace' (complete trace at end)
        """
        # Start timing
        start_time = datetime.now()
        user_id = user_id or 1
        
        # 0. DOMAIN DETECTION FIRST
        domain_result = await self.domain_router.route(query=query)
        logger.info(f"Domain detected: {domain_result.domain} ({domain_result.confidence:.2%})")
        if domain_result.matched_keywords:
            logger.debug(f"Matched keywords: {domain_result.matched_keywords}")
        
        # 1. Determine routing
        if provider == "auto":
            chosen_provider, route_metadata = await self.router.route(query, context)
            target_model = route_metadata.get("model")
        else:
            chosen_provider = provider
            route_metadata = {"mode": "manual", "provider": provider, "complexity": {"score": 0.5}}
            target_model = None

        self._last_provider_used = chosen_provider
        self._last_model_used = target_model or (self.ollama_model if chosen_provider == "ollama" else "qwen/qwen3.6-27b")

        # 2. Build DOMAIN-AWARE prompt
        full_prompt = self._build_domain_prompt(
            query=query,
            domain_result=domain_result,
            context=context
        )
        
        # 3. Stream response
        response_chunks = []
        response_complete = ""
        
        if chosen_provider == "ollama":
            async for chunk in self._stream_ollama(full_prompt, model=target_model):
                response_chunks.append(chunk)
                response_complete += chunk
                yield {"content": chunk, "type": "content"}
        elif chosen_provider == "groq":
            async for chunk in self._stream_groq(full_prompt, model=target_model):
                response_chunks.append(chunk)
                response_complete += chunk
                yield {"content": chunk, "type": "content"}
        else:
            error_msg = f"Unknown provider: {chosen_provider}"
            yield {"content": error_msg, "type": "content"}
            response_complete = error_msg
        
        # 4. Build decision trace
        end_time = datetime.now()
        trace = self._build_decision_trace(
            query=query,
            response=response_complete,
            routing_info=route_metadata,
            context=context,
            start_time=start_time,
            end_time=end_time
        )
        
        # Persist to database
        target_session = session_id or user_id # session_id is preferred
        if self.trace_service and target_session:
            try:
                await self.trace_service.capture_step(
                    session_id=target_session,
                    step=TraceStep.AI_RECOMMENDATION,
                    data=trace,
                    agent_id="generator",
                    confidence_score=route_metadata.get("complexity", {}).get("score", 0.7),
                    query=query,
                    pack_name=domain_result.domain
                )
            except Exception as e:
                logger.error(f"Failed to persist streaming trace: {e}")
        # 5. Get memory status and suggestions
        memory_status = await self._get_memory_status(user_id=user_id)
        suggestions = self._get_suggested_actions(
            query=query,
            context=context,
            memory_status=memory_status
        )
        
        # 6. Yield the complete trace with domain info
        yield {
            "type": "trace", 
            "trace": trace,
            "memory_status": memory_status,
            "suggestions": suggestions,
            "domain": domain_result.domain,
            "domain_confidence": domain_result.confidence,
            "domain_matched_keywords": domain_result.matched_keywords[:5] if domain_result.matched_keywords else []
        }
        
        # 7. Crystallize if appropriate
        if route_metadata.get("mode") == "reasoning" and len(response_complete) > 50:
            memory_id = await self._crystallize_reasoning(
                query=query,
                reasoning_path=full_prompt,
                response=response_complete,
                complexity=route_metadata.get("complexity", {}),
                user_id=user_id
            )
            # Track lineage
            if memory_id:
                await self.lineage_service.track_node(
                    node_type=SourceType.PATTERN,
                    user_id=user_id,
                    source_id=memory_id,
                    content_summary=f"Crystallized: {query[:50]}",
                    metadata={"domain": domain_result.domain}
                )
    
    def _build_domain_prompt(
        self,
        query: str,
        domain_result: Any,
        context: Optional[List]
    ) -> str:
        """Build a domain-aware prompt with persona and context."""
        
        prompt_parts = []
        
        # 1. Domain context and persona
        if domain_result.domain != "general":
            prompt_parts.append(f"[Domain: {domain_result.domain} - Confidence: {domain_result.confidence:.2%}]")
            
            # Add domain persona
            persona = self._get_domain_persona(domain_result.domain)
            if persona:
                prompt_parts.append(persona)
        else:
            prompt_parts.append("You are a helpful AI assistant. Provide clear, accurate, and helpful responses.")
        
        # 2. Domain patterns (crystallized insights)
        if domain_result.patterns:
            prompt_parts.append("\n## Relevant Crystallized Patterns")
            prompt_parts.append("Use these patterns to inform your response:")
            for i, pattern in enumerate(domain_result.patterns[:3], 1):
                query_text = pattern.get("query", f"Pattern {i}")
                response_text = pattern.get("response", "")[:150]
                prompt_parts.append(f"- {i}. {query_text}: {response_text}...")
        
        # 3. User context
        if context:
            safe_context = []
            for item in context:
                if isinstance(item, dict):
                    safe_context.append(item.get("content", str(item)))
                else:
                    safe_context.append(str(item))
            
            if safe_context:
                prompt_parts.append("\n## Context")
                prompt_parts.append("Here is relevant information to consider:")
                for ctx in safe_context:
                    prompt_parts.append(f"- {ctx}")
        
        # 4. User query
        prompt_parts.append(f"\n## Query\n{query}")
        
        return "\n\n".join(prompt_parts)
    
    def _get_domain_persona(self, domain: str) -> str:
        """Get the persona for a domain."""
        personas = {
            "clinical": """You are a Clinical Intelligence Assistant. 
Provide evidence-based, cautious clinical insights. 
Always consider:
- Patient safety as the top priority
- HIPAA and medical privacy compliance
- Evidence-based medicine and clinical guidelines
- Clear, actionable recommendations
- Appropriate disclaimers for clinical decisions""",

            "security": """You are a Security Intelligence Assistant. 
Provide actionable security insights with clear risk assessments. 
Always consider:
- NIST frameworks and security best practices
- Risk assessment and mitigation strategies
- Compliance requirements (GDPR, HIPAA, PCI, etc.)
- Threat modeling and vulnerability assessment""",

            "compliance": """You are a Compliance Intelligence Assistant. 
Provide clear compliance guidance with verifiable policy matches. 
Always consider:
- Regulatory frameworks (GDPR, HIPAA, SOX, etc.)
- Compliance verification and audit readiness
- Risk-based compliance approach
- Clear documentation and evidence requirements""",

            "contracts": """You are a Legal Intelligence Assistant. 
Provide clear legal insights with contract expertise. 
Always consider:
- Legal frameworks and contract law
- Risk allocation and liability
- Key contract terms and conditions
- Best practices for contract negotiation""",

            "education": """You are an Education Intelligence Assistant. 
Provide clear explanations with appropriate examples. 
Always consider:
- Learning objectives and outcomes
- Student engagement and understanding
- Clear, progressive explanations
- Examples and analogies""",

            "procurement": """You are a Procurement Intelligence Assistant. 
Provide supply chain insights with procurement expertise. 
Always consider:
- Cost optimization and value analysis
- Vendor management and relationships
- Supply chain risk assessment
- Contract negotiation best practices""",

            "insurance": """You are an Insurance Intelligence Assistant. 
Provide actuarial and risk management insights. 
Always consider:
- Insurance frameworks and underwriting principles
- Risk assessment and quantification
- Policy coverage and exclusions
- Claims management best practices"""
        }
        return personas.get(domain, "You are a helpful intelligence assistant.")

    async def _get_memory_status(self, user_id: int) -> Dict[str, Any]:
        """Get the current memory status for a user."""
        try:
            from app.services.memory.ice_repository import IceMemoryRepository
            from app.services.episodic_memory import EpisodicMemory
            
            ice_repo = IceMemoryRepository(self.session_factory)
            episodic_repo = EpisodicMemory(self.session_factory)
            
            ice_patterns = await ice_repo.count_patterns(user_id)
            liquid_episodes = await episodic_repo.count_episodes(user_id)
            
            return {
                "gas": {"active": True, "items": 1, "tokens": 0},
                "liquid": {
                    "active": liquid_episodes > 0,
                    "items": liquid_episodes,
                },
                "ice": {
                    "active": ice_patterns > 0,
                    "patterns": ice_patterns,
                    "confidence": 0.8
                }
            }
        except Exception as e:
            logger.warning(f"Could not retrieve memory status: {e}")
            return {
                "gas": {"active": True, "items": 1, "tokens": 0},
                "liquid": {"active": False, "items": 0},
                "ice": {"active": False, "patterns": 0, "confidence": 0.0}
            }

    def _get_suggested_actions(
        self,
        query: str,
        context: Optional[List],
        memory_status: Dict
    ) -> List[Dict[str, str]]:
        """Generate context-aware suggested actions."""
        has_memories = memory_status.get("liquid", {}).get("items", 0) > 0
        has_patterns = memory_status.get("ice", {}).get("patterns", 0) > 0
        
        if not has_memories and not has_patterns:
            return [
                {"label": "Tell me about yourself", "prompt": "I'd like to introduce myself. I work in AI and data science."},
                {"label": "What can you do?", "prompt": "What are your capabilities and how can you help me?"},
                {"label": "Set up my preferences", "prompt": "I want to set up my preferences for how we work together."}
            ]
        elif not has_patterns:
            return [
                {"label": "Test your reasoning", "prompt": "I want to test your reasoning capabilities. Here's a complex question..."},
                {"label": "Save this conversation", "prompt": "Please save this conversation to my memory."},
                {"label": "View my memories", "prompt": "What do you remember about me?"}
            ]
        else:
            return [
                {"label": "Deep reasoning test", "prompt": "Let's do a deep reasoning test. Here's a complex scenario..."},
                {"label": "Find patterns", "prompt": "What patterns have you crystallized about me?"},
                {"label": "Export intelligence", "prompt": "Can you export my crystallized patterns?"}
            ]

    def _build_decision_trace(
        self,
        query: str,
        response: str,
        routing_info: Dict,
        context: Optional[List],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Build structured decision trace for UI display."""
        
        # Analyze context
        has_memories = context and len(context) > 0
        memory_count = len(context) if context else 0
        
        # Build trace
        return {
            "timestamp": datetime.now().isoformat(),
            "decision_id": f"D-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{hash(query) % 10000:04d}",
            
            "perception": {
                "type": "user_query",
                "query": query[:200] + ("..." if len(query) > 200 else ""),
                "length": len(query),
                "has_context": has_memories,
                "context_count": memory_count
            },
            
            "policy_match": {
                "matched": routing_info.get("policy", "default"),
                "found": memory_count > 0,
                "confidence": routing_info.get("confidence", 0.0),
                "mode": routing_info.get("mode", "fast")
            },
            
            "ai_recommendation": {
                "provider": routing_info.get("provider", "unknown"),
                "model": routing_info.get("model", "default"),
                "confidence": routing_info.get("confidence", 0.5),
                "mode": routing_info.get("mode", "fast"),
                "reason": routing_info.get("reason", "Default routing")
            },
            
            "decision": {
                "type": "generate_response",
                "action": "stream",
                "severity": "low",
                "autonomy_level": "observe"
            },
            
            "provenance": {
                "trace_id": f"TRACE-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_ms": (end_time - start_time).total_seconds() * 1000,
                "source": "personavault",
                "verified": True
            },
            
            "memory_layers": {
                "gas": {
                    "active": True,
                    "items": 1,
                    "tokens": len(query.split())
                },
                "liquid": {
                    "active": has_memories,
                    "items": memory_count,
                },
                "ice": {
                    "active": False,
                    "patterns": 0,
                    "confidence": 0.0
                }
            }
        }

    async def generate(self, query: str, context: list = None, **kwargs) -> Dict[str, Any]:
        """Non-streaming generation with context and Auditable Trace"""
        
        user_id = kwargs.get("user_id", 1)
        provider = kwargs.get("provider", "auto")
        
        # Domain detection
        domain_result = await self.domain_router.route(query=query)
        
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
        
        # Build domain-aware prompt
        full_prompt = self._build_domain_prompt(
            query=query,
            domain_result=domain_result,
            context=context
        )
            
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
            memory_id = await self._crystallize_reasoning(
                query=query,
                reasoning_path=full_prompt,
                response=answer,
                complexity=route_metadata.get("complexity", {}),
                user_id=user_id
            )
            # Track lineage
            if memory_id:
                await self.lineage_service.track_node(
                    node_type=SourceType.PATTERN,
                    user_id=user_id,
                    source_id=memory_id,
                    content_summary=f"Crystallized: {query[:50]}",
                    metadata={"domain": domain_result.domain}
                )
            logger.info("🧠 Reasoning crystallized to Layer 3")

        # Generate trace with routing metadata and domain info
        trace = await self.create_trace_async(
            input_data=query,
            explanation=f"Generated answer via {source} (domain: {domain_result.domain})",
            confidence=confidence,
            decision="generate_response",
            metadata={
                "routing": route_metadata,
                "domain": domain_result.domain,
                "domain_confidence": domain_result.confidence
            },
            session_id=kwargs.get("session_id"),
            step=TraceStep.AI_RECOMMENDATION
        )

        return {
            "answer": answer, 
            "source": source, 
            "confidence": confidence,
            "trace": trace,
            "domain": domain_result.domain,
            "domain_confidence": domain_result.confidence
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
                "trigger": query[:200],
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
