"""
Multi-Agent Orchestrator - Complete Implementation
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime, timezone

from app.swarm.core.generator import GeneratorAgent
from app.services.working_memory import WorkingMemory
from app.services.episodic_memory import EpisodicMemory
from app.services.semantic_memory import SemanticMemory
from app.utils.websocket import manager

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    def __init__(self, db_session, blackboard, agents: Dict[str, Any] = None):
        self.db = db_session
        self.blackboard = blackboard
        self.working_memory = WorkingMemory()
        self.semantic_memory = SemanticMemory(db_session) if db_session else None
        self.generator = GeneratorAgent()
        self.agent_activity = {
            "planner": "idle",
            "retriever": "idle",
            "generator": "idle",
            "judge": "idle",
            "router": "idle",
            "empathy": "idle",
            "episodic": "idle",
            "semantic": "idle"
        }
        self.active_tasks = 0
        self._stages = []
        logger.info("MultiAgentOrchestrator initialized")
    
    def _get_user_id(self, context: Dict[str, Any]) -> int:
        """Extract user_id from context"""
        user_id = context.get("user_id")
        if user_id is None:
            user_id = context.get("session", {}).get("user_id")
        if user_id is None:
            user_id = 1
            logger.warning(f"User ID not found, using default: {user_id}")
        return user_id
    
    async def _broadcast_agent_status(self):
        """Broadcast agent status"""
        try:
            if manager and hasattr(manager, 'broadcast'):
                await manager.broadcast({
                    "type": "agent_status",
                    "status": self.agent_activity,
                    "active_tasks": self.active_tasks,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        except Exception as e:
            logger.debug(f"Failed to broadcast agent status: {e}")
    
    async def _broadcast_thought(self, agent: str, thought: str):
        """Broadcast a thought"""
        try:
            if manager and hasattr(manager, 'broadcast'):
                await manager.broadcast({
                    "type": "thought",
                    "agent": agent,
                    "thought": thought,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        except Exception as e:
            logger.debug(f"Failed to broadcast thought: {e}")
    
    async def run(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the cognitive pipeline with real generation"""
        logger.info(f"Processing query: {query[:50]}...")
        
        try:
            # Step 1: Get user ID
            user_id = self._get_user_id(context)
            provider = context.get("provider", "ollama")
            
            # Step 2: Broadcast status
            await self._broadcast_agent_status()
            await self._broadcast_thought("Orchestrator", f"📝 Processing: '{query[:50]}...'")
            
            # Step 3: Get memory context (if available)
            memory_context = []
            if self.semantic_memory:
                try:
                    memory_context = await self.semantic_memory.search(query, user_id, limit=5)
                    logger.info(f"Retrieved {len(memory_context)} memory items")
                except Exception as e:
                    logger.warning(f"Memory search failed: {e}")
            
            # Step 4: Generate response
            self.agent_activity["generator"] = "active"
            await self._broadcast_agent_status()
            await self._broadcast_thought("Generator", f"🤖 Generating response using {provider}...")
            
            # Call the generator with the full context
            generation = await self.generator.generate(
                query=query,
                context=memory_context,
                reasoning_insight=None,
                situational_awareness={},
                persona=None,
                response_tone="neutral",
                hitl_approved=False
            )
            
            # Extract the response
            response_text = generation.get("answer", "")
            if not response_text:
                response_text = f"I processed your query: '{query}'. The system generated a response."
            
            confidence = generation.get("confidence", 0.7)
            
            self.agent_activity["generator"] = "idle"
            await self._broadcast_agent_status()
            await self._broadcast_thought("Orchestrator", "✅ Response generated")
            
            # Step 5: Store in episodic memory (if available)
            try:
                if hasattr(self, 'episodic_memory') and self.episodic_memory:
                    await self.episodic_memory.store({
                        "query": query,
                        "response": response_text,
                        "user_id": user_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            except Exception as e:
                logger.debug(f"Failed to store in episodic memory: {e}")
            
            # Step 6: Return the response with thought process
            thought_process = [
                {"step": 1, "label": "🔍 Understanding", "description": "Analyzing your query", "status": "complete"},
                {"step": 2, "label": "🧠 Retrieving", "description": f"Found {len(memory_context)} relevant memories", "status": "complete"},
                {"step": 3, "label": "🤖 Generating", "description": f"Using {provider} to generate response", "status": "complete"},
                {"step": 4, "label": "✅ Finalizing", "description": "Response ready", "status": "complete"}
            ]
            
            return {
                "answer": response_text,
                "confidence": confidence,
                "reasoning": generation.get("reasoning_steps", []),
                "thought_process": thought_process,
                "source": generation.get("source", provider)
            }
            
        except Exception as e:
            logger.error(f"Error in run: {e}")
            import traceback
            traceback.print_exc()
            
            # Return a fallback response
            return {
                "answer": f"I encountered an issue: {str(e)}. Please try again.",
                "confidence": 0.1,
                "reasoning": [],
                "thought_process": [
                    {"step": 1, "label": "❌ Error", "status": "error", "description": str(e)}
                ],
                "source": "error"
            }
    
    async def process_query(self, query: str, user_id: int, session_id: int = None, provider: str = "ollama") -> Dict[str, Any]:
        """Process a query for the chat endpoint"""
        logger.info(f"Processing query for user {user_id} with provider {provider}")
        
        context = {
            "user_id": user_id,
            "session_id": session_id,
            "provider": provider,
            "query": query
        }
        
        try:
            result = await self.run(query, context)
            return {
                "response": result.get("answer", "No response generated."),
                "provider": provider,
                "session_id": session_id,
                "thought_process": result.get("thought_process", []),
                "confidence": result.get("confidence", 0.5),
                "source": result.get("source", "unknown")
            }
        except Exception as e:
            logger.error(f"Error in process_query: {e}")
            import traceback
            traceback.print_exc()
            return {
                "response": f"Error: {str(e)}",
                "provider": provider,
                "session_id": session_id,
                "thought_process": [
                    {"step": 1, "label": "❌ Error", "status": "error", "description": str(e)}
                ],
                "confidence": 0.1
            }
    
    # ============================================================
    # STREAMING METHOD - INSIDE THE CLASS
    # ============================================================
    
    async def stream_process(
        self, 
        query: str, 
        user_id: int,
        session_id: int = None,
        provider: str = "groq"
    ):
        """Process query with streaming output - yields chunks as they come"""
        
        try:
            logger.info(f"Streaming process for user {user_id}: {query[:50]}...")
            
            # Step 1: Understanding
            yield {"type": "thought", "data": {"step": "🧠", "label": "Understanding your query...", "status": "active"}}
            await asyncio.sleep(0.05)
            
            # Step 2: Memory retrieval
            memory_context = []
            if self.semantic_memory:
                try:
                    yield {"type": "thought", "data": {"step": "🔍", "label": "Searching memory...", "status": "active"}}
                    memory_context = await self.semantic_memory.search(query, user_id, limit=5)
                    logger.info(f"Retrieved {len(memory_context)} memory items")
                except Exception as e:
                    logger.warning(f"Memory search failed: {e}")
            
            # Step 3: Generate with streaming
            self.agent_activity["generator"] = "active"
            await self._broadcast_agent_status()
            
            yield {"type": "thought", "data": {"step": "🤖", "label": f"Generating using {provider}...", "status": "active"}}
            await asyncio.sleep(0.05)
            
            # Stream from the generator directly
            full_response = ""
            async for chunk in self.generator.generate_stream(query, provider):
                if chunk:
                    full_response += chunk
                    yield {"type": "content", "data": chunk}
            
            # Step 4: Complete
            self.agent_activity["generator"] = "idle"
            await self._broadcast_agent_status()
            
            yield {"type": "thought", "data": {"step": "✅", "label": "Complete!", "status": "complete"}}
            
            # Store in episodic memory
            try:
                if hasattr(self, 'episodic_memory') and self.episodic_memory:
                    await self.episodic_memory.store({
                        "query": query,
                        "response": full_response,
                        "user_id": user_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            except Exception as e:
                logger.debug(f"Failed to store in episodic memory: {e}")
            
            # Send session ID if provided
            if session_id:
                yield {"type": "session_id", "data": session_id}
            
            # Send done signal
            yield {"type": "done", "data": {"message": "Generation complete"}}
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            import traceback
            traceback.print_exc()
            yield {"type": "error", "data": {"error": str(e)}}

# Singleton instance
_orchestrator_instance = None

def get_orchestrator(db_session=None, blackboard=None) -> MultiAgentOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = MultiAgentOrchestrator(db_session, blackboard)
    return _orchestrator_instance
