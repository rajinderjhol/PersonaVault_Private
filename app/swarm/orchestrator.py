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
from app.services.perception import RoboticsPerceptionService
from app.services.trace_service import get_trace_service, DecisionTrace
import uuid

logger = logging.getLogger(__name__)

from app.swarm.context import AgentEnvironmentContext
from app.services.memory_service import MemoryService
from app.api.v2.services.authority_service import AuthorityService
from app.api.v2.services.crystallization_service import CrystallizationService

class MultiAgentOrchestrator:
    def __init__(self, db_session, blackboard, 
                 memory_service: Optional[MemoryService] = None, 
                 authority_service: Optional[AuthorityService] = None, 
                 crystallization_service: Optional[CrystallizationService] = None,
                 agents: Dict[str, Any] = None, 
                 confidence_threshold: float = 0.6):
        self.db = db_session
        self.blackboard = blackboard
        self.agents = agents or {}
        self.memory_service = memory_service
        self.authority_service = authority_service
        self.crystallization_service = crystallization_service
        self.working_memory = WorkingMemory()
        self.trace_service = get_trace_service(db_session)
        self.perception = RoboticsPerceptionService(db_session, self.trace_service)
        self.pack_executor = PackExecutor(trace_service=self.trace_service)
        
        logger.info(f"Agents initialized: {list(self.agents.keys())}")

        # Inject trace service into all agents
        for agent in self.agents.values():
            if hasattr(agent, 'trace_service'):
                agent.trace_service = self.trace_service

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
    
    async def get_swarm_status(self) -> Dict[str, Any]:
        """Get real-time status of all agents in the swarm."""
        active_agents = []
        idle_agents = []
        agent_tasks = {}
        
        for agent_name, agent in self.agents.items():
            status = await self._get_agent_activity(agent_name)
            if status.get("active"):
                active_agents.append({
                    "name": agent_name,
                    "status": "active",
                    "task": status.get("task", "Processing"),
                    "provider": status.get("provider", "local"),
                    "confidence": status.get("confidence", 0.0),
                    "started_at": status.get("started_at")
                })
            else:
                idle_agents.append(agent_name)
            
            agent_tasks[agent_name] = status.get("task", "idle")
        
        # Determine collaboration pipeline
        pipeline = self._detect_collaboration_pipeline(agent_tasks)
        
        return {
            "active_agents": active_agents,
            "idle_agents": idle_agents,
            "total_agents": len(self.agents),
            "active_count": len(active_agents),
            "collaboration": {
                "pipeline": pipeline,
                "current_step": pipeline[0] if pipeline else None,
                "active": len(active_agents) > 0
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def list_agents(self) -> List[Dict]:
        """List all agents in the swarm."""
        swarm_status = await self.get_swarm_status()
        active_agent_names = [a["name"] for a in swarm_status["active_agents"]]
        
        return [
            {
                "name": name,
                "type": agent.__class__.__name__,
                "capabilities": await self._get_agent_capabilities(agent),
                "status": "active" if name in active_agent_names else "idle"
            }
            for name, agent in self.agents.items()
        ]

    async def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get detailed status of a specific agent."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        agent = self.agents[agent_name]
        return {
            "name": agent_name,
            "type": agent.__class__.__name__,
            "status": "active" if await self._is_agent_active(agent_name) else "idle",
            "capabilities": await self._get_agent_capabilities(agent),
            "current_task": await self._get_agent_task(agent_name),
            "performance": await self._get_agent_performance(agent_name)
        }

    async def _get_agent_activity(self, agent_name: str) -> Dict:
        """Get current activity of an agent."""
        # Integrates with existing agent activity map
        activity = self.agent_activity.get(agent_name, "idle")
        return {
            "active": activity != "idle",
            "task": activity,
            "provider": "local",
            "confidence": 0.0
        }

    async def _is_agent_active(self, agent_name: str) -> bool:
        """Check if an agent is currently active."""
        status = await self._get_agent_activity(agent_name)
        return status.get("active", False)

    async def _get_agent_capabilities(self, agent) -> List[str]:
        """Get agent capabilities."""
        capabilities = []
        if hasattr(agent, 'model'):
            capabilities.append(f"Model: {agent.model}")
        return capabilities

    async def _get_agent_task(self, agent_name: str) -> str:
        """Get current task of an agent."""
        status = await self._get_agent_activity(agent_name)
        return status.get("task", "idle")

    async def _get_agent_performance(self, agent_name: str) -> Dict:
        """Get agent performance metrics."""
        return {"avg_latency": 0.5, "success_rate": 0.95}

    def _detect_collaboration_pipeline(self, agent_tasks: Dict[str, str]) -> List[str]:
        """Detect the collaboration pipeline from agent tasks."""
        order = ["RetrievalAgent", "GeneratorAgent", "ValidatorAgent", "SecurityAgent"]
        return [agent for agent in order if agent in agent_tasks and agent_tasks[agent] != "idle"]

    
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

        # Inject Environment Context if provided
        env_id = context.get("environment_id")
        if env_id and self.memory_service and self.authority_service and self.crystallization_service:
            agent_context = AgentEnvironmentContext(
                env_id, 
                self.memory_service, 
                self.authority_service, 
                self.crystallization_service
            )
            for agent in self.agents.values():
                if hasattr(agent, 'set_context'):
                    agent.set_context(agent_context)

        all_traces = []
        start_time = datetime.now()

        try:
            # ... rest of the original run method ...

            user_val = context.get("user_id", 1)
            user_id = user_val.id if hasattr(user_val, 'id') else user_val
            session_id = context.get("session_id")
            provider = context.get("provider", "ollama")
            
            # Step 1.5: Perception Step
            perception_result = await self.perception.process_robot_observation(
                observation_data={"raw_text": query},
                robot_id="orchestrator",
                user_id=user_id,
                session_id=session_id
            )
            all_traces.append(perception_result.get("trace"))
            
            # Step 2: Broadcast status
            await self._broadcast_agent_status()
            await self._broadcast_thought("Orchestrator", f"📝 Processing: '{query[:50]}...'")
            
            # Step 3: Behavior Pack Policy Check (Dominant Policy)
            pack_result = await self.pack_executor.process_with_best_pack(query, user_id, session_id=session_id)
            all_traces.append(pack_result.get("trace"))
            
            # Step 4: Get memory context
            memory_context = []
            if self.retriever:
                try:
                    search_data = await self.retriever.search(query, user_id, limit=5, session_id=session_id)
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
                user_id=user_id,
                session_id=session_id
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
                session_id=session_id,
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                user_id=user_id,
                query=query,
                response=response_text,
                trace={"all_traces": all_traces},
                explanation=pack_result["decision"].get("explanation", "Agent response generated"),
                pack_name=pack_result["metadata"].get("pack", "unknown"),
                pack_version=pack_result["metadata"].get("version", "1.0.0"),
                latency_ms=latency_ms
            )
            await self.trace_service.store_trace(trace_obj)

            # Integrate with GraphService
            from app.services.graph_service import graph_service
            # Create Decision Node
            graph_service.create_decision_node(
                decision_id=decision_id,
                query=query,
                pack=pack_result["metadata"].get("pack", "unknown"),
                timestamp=datetime.now().isoformat(),
                confidence=confidence
            )
            # Link to Policy
            policy_id = pack_result["decision"].get("policy")
            if policy_id and policy_id != "no_match":
                graph_service.link_decision_to_policy(decision_id, f"policy_{policy_id}")

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
            pack_result = await self.pack_executor.process_with_best_pack(query, user_id, session_id=session_id)
            
            # Step 2: Memory retrieval
            memory_context = []
            retrieval_trace = None
            if self.retriever:
                try:
                    yield {"type": "thought", "data": {"step": "🔍", "label": "Searching memory...", "status": "active"}}
                    search_data = await self.retriever.search(query, user_id=user_id, session_id=session_id)
                    search_results = search_data.get("results", [])
                    retrieval_trace = search_data.get("trace")
                    
                    memory_context = [r.dict() for r in search_results]
                    
                    if pack_result["decision"]["policy"] != "no_match":
                        memory_context.append(f"[POLICY: {pack_result['decision']['policy']}] Decision: {pack_result['decision']['explanation']}")
                except Exception as e:
                    logger.warning(f"Memory search failed: {e}")
            
            # Step 3: Generate with streaming trace
            self.agent_activity["generator"] = "active"
            await self._broadcast_agent_status()
            
            yield {"type": "thought", "data": {"step": "🤖", "label": f"Generating using {provider}...", "status": "active"}}
            
            full_response = ""
            gen_trace = None
            gen_memory_status = None
            gen_suggestions = None
            
            async for item in self.generator.generate_stream_with_trace(query, provider, context=memory_context, user_id=user_id, session_id=session_id):
                if item["type"] == "content":
                    full_response += item["content"]
                    yield {"type": "content", "data": item["content"]}
                elif item["type"] == "trace":
                    gen_trace = item["trace"]
                    gen_memory_status = item.get("memory_status")
                    gen_suggestions = item.get("suggestions")
            
            # Step 4: Complete and Store Trace
            
            # Aggregate traces
            all_traces = [pack_result.get("trace"), retrieval_trace, gen_trace]
            
            decision_id = f"D-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{hash(query) % 10000:04d}"
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Store in TraceService
            trace_obj = DecisionTrace(
                decision_id=decision_id,
                session_id=session_id,
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                user_id=user_id,
                query=query,
                response=full_response,
                trace={"all_traces": all_traces},
                explanation=pack_result["decision"].get("explanation", "Agent response generated"),
                pack_name=pack_result["metadata"].get("pack", "unknown"),
                pack_version=pack_result["metadata"].get("version", "1.0.0"),
                latency_ms=latency_ms
            )
            
            await self.trace_service.store_trace(trace_obj)
            
            self.agent_activity["generator"] = "idle"
            await self._broadcast_agent_status()
            
            yield {"type": "thought", "data": {"step": "✅", "label": "Complete!", "status": "complete"}}
            yield {"type": "done", "data": {
                "message": "Generation complete", 
                "decision": pack_result.get("decision"),
                "decision_id": decision_id,
                "trace": gen_trace,
                "memory_status": gen_memory_status,
                "suggestions": gen_suggestions
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
