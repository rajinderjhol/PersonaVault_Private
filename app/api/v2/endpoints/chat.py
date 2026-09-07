import asyncio
import json
import logging
import re
from datetime import datetime  
from typing import Dict, Any, Optional, List, AsyncGenerator
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.api.v2.models.environment import Environment
from app.api.v2.dependencies import require_authority
from app.swarm.core.generator import GeneratorAgent
from app.services.memory.retrieval import MemoryRetrievalService
from app.services.crystallization.crystallization_service import crystallization_service
from app.services.packs.executor import PackExecutor


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/{env_id}/chat", tags=["v2-chat"])

class V2ChatRequest(BaseModel):
    message: str
    pack_ids: Optional[List[str]] = None
    show_reasoning: Optional[bool] = False  # User-controlled

class ReasoningProcessor:
    """Process streaming chunks to separate reasoning from answer."""
    
    def __init__(self):
        self.reasoning_buffer = []
        self.answer_buffer = []
        self.is_in_think = False
        self.is_thinking_done = False
        self.think_started = False
        self.current_chunk_buffer = ""
        self.reasoning_captured = ""

    def process_chunk(self, chunk: str) -> List[Dict[str, Any]]:
        """Process a single chunk and return events."""
        events = []
        self.current_chunk_buffer += chunk
        
        # Check for <think> tag
        if not self.think_started and "<think>" in self.current_chunk_buffer:
            self.think_started = True
            self.is_in_think = True
            parts = self.current_chunk_buffer.split("<think>", 1)
            before_think = parts[0] if parts else ""
            self.current_chunk_buffer = parts[1] if len(parts) > 1 else ""
            
            if before_think.strip():
                events.append({"type": "content", "content": before_think})
        
        # Check for </think> tag
        if self.is_in_think and "</think>" in self.current_chunk_buffer:
            self.is_in_think = False
            self.is_thinking_done = True
            parts = self.current_chunk_buffer.split("</think>", 1)
            
            if parts[0].strip():
                self.reasoning_buffer.append(parts[0])
                self.reasoning_captured = parts[0]
                events.append({"type": "thinking", "content": parts[0]})
            
            self.current_chunk_buffer = parts[1] if len(parts) > 1 else ""
            events.append({"type": "thinking_end"})
        
        # Handle content after thinking is done
        if self.is_thinking_done and self.current_chunk_buffer.strip():
            self.answer_buffer.append(self.current_chunk_buffer)
            events.append({"type": "content", "content": self.current_chunk_buffer})
            self.current_chunk_buffer = ""
        
        # If we captured reasoning, add a crystallization event
        if self.is_thinking_done and self.reasoning_captured:
            events.append({
                "type": "reasoning_captured",
                "reasoning": self.reasoning_captured,
                "length": len(self.reasoning_captured)
            })
            self.reasoning_captured = ""  # Reset after capturing
        
        return events

    def get_reasoning(self) -> str:
        """Get the complete reasoning."""
        return "".join(self.reasoning_buffer)

    def get_answer(self) -> str:
        """Get the complete answer."""
        return "".join(self.answer_buffer)


class ChatPipeline:
    def __init__(self, env_id: str):
        self.env_id = env_id
        self.generator = GeneratorAgent()
        self.processor = ReasoningProcessor()
        self.retrieved_memories = []
        self.reasoning_trace = None
        self.active_packs = []

    async def load_packs(self, pack_ids: List[str]) -> List[Dict[str, Any]]:
        """Load and activate intelligence packs."""
        # TODO: Implement actual pack loading
        if pack_ids:
            logger.info(f"Loading packs: {pack_ids}")
            # Placeholder - will be implemented with PackExecutor
        return []

    async def retrieve_context(self, query: str, pack_ids: List[str]) -> Dict[str, Any]:
        """Retrieve relevant memories and context."""
        try:
            memory_service = MemoryRetrievalService()
            memories = await memory_service.retrieve(
                query=query,
                env_id=self.env_id,
                pack_ids=pack_ids,
                layers=["gas", "liquid", "ice"]
            )
            self.retrieved_memories = memories
            return {
                "memories": memories,
                "has_context": len(memories) > 0,
                "count": len(memories)
            }
        except Exception as e:
            logger.warning(f"Memory retrieval failed: {e}")
            return {"memories": [], "has_context": False, "count": 0}

    def _build_memory_context(self, memories: List[Dict]) -> str:
        """Build a context string from retrieved memories."""
        if not memories:
            return ""
        
        context_parts = []
        context_parts.append("Relevant institutional knowledge:\n")
        
        for mem in memories[:10]:  # Limit to top 10
            content = mem.get('content', '') or mem.get('text', '')
            if content:
                context_parts.append(f"- {content}")
                if mem.get('confidence'):
                    context_parts.append(f"  (Confidence: {mem['confidence']}%)")
        
        return "\n".join(context_parts)

    async def crystallize_pattern(self, query: str, reasoning: str, pack_ids: List[str]):
        """Crystallize the reasoning pattern."""
        if not reasoning or len(reasoning) < 50:
            return
        
        try:
            pattern = {
                "query": query,
                "reasoning": reasoning,
                "pack_ids": pack_ids,
                "active_packs": self.active_packs,
                "confidence": 0.75,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await crystallization_service.crystallize(
                env_id=self.env_id,
                pattern=pattern,
                source="chat_reasoning"
            )
            logger.info(f"✅ Crystallized pattern: {result.get('pattern_id', 'unknown')}")
        except Exception as e:
            logger.warning(f"Failed to crystallize pattern: {e}")

    async def store_reasoning_trace(self, query: str, trace: Dict[str, Any]):
        """Store reasoning trace in memory."""
        try:
            from app.services.memory.episodic import EpisodicMemoryService
            episodic = EpisodicMemoryService()
            await episodic.store(
                env_id=self.env_id,
                event_type="reasoning_trace",
                query=query,
                trace=trace,
                timestamp=datetime.utcnow().isoformat()
            )
            logger.info(f"✅ Stored reasoning trace for query: {query[:50]}...")
        except Exception as e:
            logger.warning(f"Failed to store reasoning trace: {e}")

    # In app/api/v2/endpoints/chat.py

    async def generate_stream(self, query: str, pack_ids: List[str], show_reasoning: bool = False) -> AsyncGenerator:
        yield {"type": "status", "message": "🔍 Analyzing..."}
        
        # ✅ Build context as a list, not a string
        context_list = []
        
        # Add memory context if available
        if self.retrieved_memories:
            for mem in self.retrieved_memories[:5]:
                content = mem.get('content', '') or mem.get('text', '')
                if content:
                    context_list.append({
                        "role": "system",
                        "content": f"Relevant memory: {content}"
                    })
        
        # Directly stream from generator with correct parameters
        raw_stream = self.generator.generate_stream_with_trace(
            query=query,
            provider="ollama",
            context=context_list,  # ✅ Pass as list
            user_id=1
        )
        
        has_content = False
        
        async for chunk in raw_stream:
            if chunk.get("type") == "content":
                content = chunk.get("content", "")
                # ✅ Yield content directly
                yield {"type": "content", "content": content}
                has_content = True
            elif chunk.get("type") == "trace":
                self.reasoning_trace = chunk.get("trace")
                if show_reasoning:
                    yield {"type": "trace", "trace": self.reasoning_trace}
            else:
                yield chunk
        
        if not has_content:
            yield {"type": "content", "content": "I processed your request but couldn't generate a specific response. Please try rephrasing."}
        
        yield {"type": "done"}

@router.post("/stream")
async def stream_chat(
    env_id: str,
    request_body: V2ChatRequest,
    env: Environment = Depends(lambda env_id: require_authority(env_id, "read"))
):
    """V2 stream chat response with full intelligence pipeline."""
    
    pipeline = ChatPipeline(env_id)
    
    async def event_generator():
        try:
            async for event in pipeline.generate_stream(
                query=request_body.message,
                pack_ids=request_body.pack_ids or [],
                show_reasoning=request_body.show_reasoning or False
            ):
                yield f"data: {json.dumps(event)}\n\n"
                
        except Exception as e:
            logger.error(f"V2 Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )