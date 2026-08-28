"""
Multi-Agent Orchestrator - Complete Implementation with Auditable Traces
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
from runtime.pack_executor import PackExecutor
from app.services.trace_service import get_trace_service, DecisionTrace
import uuid

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    def __init__(self, db_session, blackboard, agents: Dict[str, Any] = None, confidence_threshold: float = 0.6):
        self.db = db_session
        self.blackboard = blackboard
        self.agents = agents or {}
        self.working_memory = WorkingMemory()
        self.pack_executor = PackExecutor()  # ✅ Integrated Behavior Pack Compiler
        self.trace_service = get_trace_service(db_session) # ✅ Integrated Trace Service
        logger.info(f"Agents initialized: {list(self.agents.keys())}")

        # Fallback to agents if available, otherwise initialize defaults
        self.retriever = self.agents.get("retriever")
        
        # Configure confidence threshold
        if self.retriever and hasattr(self.retriever, 'set_confidence_threshold'):
            self.retriever.set_confidence_threshold(confidence_threshold)
            logger.info(f"Orchestrator using confidence threshold: {confidence_threshold}")
            
        # For compatibility with methods still using semantic_memory
        self.semantic_memory = self.retriever 
        
        logger.info(f"Retriever agent: {self.retriever}")
        self.generator = self.agents.get("generator") or GeneratorAgent()
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
        logger.info("MultiAgentOrchestrator initialized with swarm agents and PackExecutor")
    
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
        """Execute the cognitive pipeline with Auditable Traces"""
        logger.info(f"Processing query: {query[:50]}...")
        
        all_traces = []
        start_time = datetime.now()
        
        try:
            # Step 1: Get user ID
            user_id = self._get_user_id(context)
            provider = context.get("provider", "ollama")
            
            # Step 2: Broadcast status
            await self._broadcast_agent_status()
            await self._broadcast_thought("Orchestrator", f"📝 Processing: '{query[:50]}...'")
            
            # Step 3: Behavior Pack Policy Check (Dominant Policy)
            pack_result = await self.pack_executor.process_with_best_pack(query, user_id)
            all_traces.append(pack_result.get("trace"))
            
            # Step 4: Get memory context
            memory_context = []
            if self.retriever:
                try:
                    search_data = await self.retriever.search(query, user_id, limit=5)
                    search_results = search_data.get("results", [])
                    all_traces.append(search_data.get("trace"))
                    memory_context = [r.dict() for r in search_results]
                    logger.info(f"Retrieved {len(memory_context)} memory items")
                except Exception as e:
                    logger.warning(f"Memory search failed: {e}")
            
            # Step 5: Generate response
            self.agent_activity["generator"] = "active"
            await self._broadcast_agent_status()
            await self._broadcast_thought("Generator", f"🤖 Generating response using {provider}...")
            
            # Inject pack intelligence into context if a policy matched
            if pack_result["decision"]["policy"] != "no_match":
                policy_context = f"[POLICY: {pack_result['decision']['policy']}] Decision: {pack_result['decision']['explanation']}"
                memory_context.append(policy_context)
            
            # Call the generator
            generation = await self.generator.generate(
                query=query,
                context=memory_context,
                provider=provider,
                user_id=user_id
            )
            
            all_traces.append(generation.get("trace"))
            
            # Extract the response
            response_text = generation.get("answer", "")
            confidence = generation.get("confidence", 0.7)
            
            self.agent_activity["generator"] = "idle"
            await self._broadcast_agent_status()
            await self._broadcast_thought("Orchestrator", "✅ Response generated")
            
            # Step 6: Store in episodic memory
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
            
            # Store Trace
            decision_id = f"D-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{hash(query) % 10000:04d}"
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            trace_obj = DecisionTrace(
                decision_id=decision_id,
                timestamp=datetime.now().isoformat(),
                user_id=user_id,
                query=query,
                response=response_text,
                trace={"all_traces": all_traces},
                explanation=pack_result["decision"].get("explanation", "Agent response generated"),
                pack_name=pack_result["metadata"].get("pack", "unknown"),
                pack_version=pack_result["metadata"].get("version", "1.0.0"),
                latency_ms=latency_ms
            )
            self.trace_service.store_trace(trace_obj)
            
            return {
                "answer": response_text,
                "confidence": confidence,
                "traces": all_traces,
                "decision": pack_result.get("decision"),
                "autonomy": pack_result.get("autonomy"),
                "source": generation.get("source", provider),
                "decision_id": decision_id
            }
            
        except Exception as e:
            logger.error(f"Error in run: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "answer": f"I encountered an issue: {str(e)}. Please try again.",
                "confidence": 0.1,
                "traces": all_traces,
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
                "traces": result.get("traces", []),
                "decision": result.get("decision"),
                "autonomy": result.get("autonomy"),
                "confidence": result.get("confidence", 0.5),
                "decision_id": result.get("decision_id")
            }
        except Exception as e:
            logger.error(f"Error in process_query: {e}")
            return {
                "response": f"Error: {str(e)}",
                "provider": provider,
                "session_id": session_id,
                "confidence": 0.1
            }
    
    async def stream_process(
        self, 
        query: str, 
        user_id: int,
        session_id: int = None,
        provider: str = "auto"
    ):
        """Process query with streaming output and Auditable Traces"""
        
        start_time = datetime.now()
        
        try:
            logger.info(f"Streaming process for user {user_id}: {query[:50]}...")
            
            # Step 1: Policy Check
            yield {"type": "thought", "data": {"step": "🛡️", "label": "Checking policies...", "status": "active"}}
            pack_result = await self.pack_executor.process_with_best_pack(query, user_id)
            # pack_result already contains trace
            
            # Step 2: Memory retrieval
            memory_context = []
            retrieval_trace = None
            if self.retriever:
                try:
                    yield {"type": "thought", "data": {"step": "🔍", "label": "Searching memory...", "status": "active"}}
                    search_data = await self.retriever.search(query, user_id=user_id)
                    search_results = search_data.get("results", [])
                    retrieval_trace = search_data.get("trace")
                    
                    memory_context = [r.dict() for r in search_results]
                    
                    if pack_result["decision"]["policy"] != "no_match":
                        memory_context.append(f"[POLICY: {pack_result['decision']['policy']}] Decision: {pack_result['decision']['explanation']}")
                except Exception as e:
                    logger.warning(f"Memory search failed: {e}")
            
            # Step 3: Generate with streaming
            self.agent_activity["generator"] = "active"
            await self._broadcast_agent_status()
            
            yield {"type": "thought", "data": {"step": "🤖", "label": f"Generating using {provider}...", "status": "active"}}
            
            full_response = ""
            async for chunk in self.generator.generate_stream(query, provider, context=memory_context, user_id=user_id):
                if chunk:
                    full_response += chunk
                    yield {"type": "content", "data": chunk}
            
            # Final trace from generator
            gen_trace = self.generator.create_trace(
                input_data=query,
                explanation=f"Streamed response via {provider}",
                confidence=0.8,
                decision="stream_response"
            )
            
            # Step 4: Complete and Store Trace
            
            # Aggregate traces
            all_traces = [pack_result.get("trace"), retrieval_trace, gen_trace]
            
            decision_id = f"D-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{hash(query) % 10000:04d}"
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Store in TraceService
            trace_obj = DecisionTrace(
                decision_id=decision_id,
                timestamp=datetime.now().isoformat(),
                user_id=user_id,
                query=query,
                response=full_response,
                trace={"all_traces": all_traces},
                explanation=pack_result["decision"].get("explanation", "Agent response generated"),
                pack_name=pack_result["metadata"].get("pack", "unknown"),
                pack_version=pack_result["metadata"].get("version", "1.0.0"),
                latency_ms=latency_ms
            )
            
            self.trace_service.store_trace(trace_obj)
            
            self.agent_activity["generator"] = "idle"
            await self._broadcast_agent_status()
            
            yield {"type": "thought", "data": {"step": "✅", "label": "Complete!", "status": "complete"}}
            yield {"type": "done", "data": {
                "message": "Generation complete", 
                "decision": pack_result.get("decision"),
                "decision_id": decision_id
            }}
            
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
