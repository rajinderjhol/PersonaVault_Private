import logging
import json
from typing import Dict, Any, List
from datetime import datetime, timezone
from app.swarm.core.planner import PlannerAgent
from app.swarm.core.retriever import RetrievalAgent
from app.swarm.core.generator import GeneratorAgent
from app.swarm.core.judge import JudgeAgent
from app.services.working_memory import WorkingMemory
from app.services.episodic_memory import EpisodicMemory
from app.services.semantic_memory import SemanticMemory
from app.schemas.memory_schemas import EpisodicEntry, MemoryResult
from app.models import SemanticPattern
from app.swarm.core.router import AIRouter
from app.services.awareness_service import AwarenessService
from app.api.v1.endpoints.persona import PersonaProfiler
from app.utils.websocket import manager

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    """
    Main closed-loop execution engine for PersonaVault.
    
    Orchestrates the cognitive pipeline by transitioning data through three distinct memory layers:
    Layer 1 (Working): Current query and situational context.
    Layer 2 (Episodic): Task history and short-term interactions.
    Layer 3 (Semantic): Long-term learned patterns and constraints.
    """
    def __init__(self, db_session, agents: Dict[str, Any] = None):
        self.db = db_session
        self.working_memory = WorkingMemory()
        self.episodic_memory = EpisodicMemory(db_session)
        self.semantic_memory = SemanticMemory(db_session)
        
        # Agent status tracking
        self.active_tasks = 0
        self.agent_activity = {
            "planner": "idle",
            "retriever": "idle",
            "reasoner": "idle",
            "validator": "idle",
            "generator": "idle",
            "judge": "idle",
            "router": "idle",
            "empathy": "idle",
            "hitl": "idle",
            "episodic": "idle",
            "semantic": "idle"
        }
        
        # Use provided agents from DI container (main.py) or default to local init
        self.agents = agents or {}
        self.planning = self.agents.get("planner") or PlannerAgent(self.semantic_memory)
        self.retrieval = self.agents.get("retriever") or RetrievalAgent()
        self.generator = self.agents.get("generator") or GeneratorAgent()
        self.judge = self.agents.get("judge") or JudgeAgent()
        self.ai_router = self.agents.get("router") or AIRouter(engine_mode="Local-First (Ollama)")
        self.reasoner = self.agents.get("reasoner")
        self.validator = self.agents.get("validator")
        self.hitl = self.agents.get("hitl")
        self.empathy = self.agents.get("empathy")

        self.awareness = AwarenessService()
        self.persona_profiler = PersonaProfiler(db_session)
    
    async def _broadcast_agent_status(self):
        """Broadcast current agent status to all WebSocket clients."""
        try:
            await manager.broadcast(json.dumps({
                "type": "agent_status",
                "active_tasks": self.active_tasks,
                "agent_activity": self.agent_activity
            }))
        except Exception as e:
            logger.debug(f"Failed to broadcast agent status: {e}")
    
    async def _broadcast_thought(self, agent: str, content: str):
        """Broadcast a thought to the live swarm feed."""
        try:
            await manager.broadcast(json.dumps({
                "type": "thought_stream",
                "agent": agent,
                "content": content
            }))
        except Exception as e:
            logger.debug(f"Failed to broadcast thought: {e}")
    
    async def run(self, query: str, context: Dict[str, Any]):
        """
        Executes a full cognitive cycle for a given user query.
        
        The flow includes:
        1. Intent Planning: Analyzing query to determine search strategies.
        2. Hybrid Retrieval: Combining vector, graph, and keyword searches.
        3. Grounding: Fetching real-time IoT context and user persona.
        4. Routing: Selecting the appropriate AI agent/tier.
        5. Generation: Synthesizing a personalized, grounded response.
        6. Evaluation: Assessing response quality and triggering regeneration if needed.
        7. Memory Graduation: Learning patterns from the interaction.
        """
        
        # Track active task
        self.active_tasks += 1
        await self._broadcast_agent_status()
        
        # Broadcast query received
        await self._broadcast_thought("Orchestrator", f"🚀 Processing query: '{query[:50]}...'")
        
        # Ensure user_id is an integer
        user_id = context.get("user_id")
        if user_id is None:
            user_id = 1
        elif hasattr(user_id, 'id'):
            user_id = user_id.id
        else:
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                user_id = 1
        context["user_id"] = user_id
        
        try:
            # 1. PLAN: Create retrieval plan with learned patterns
            self.agent_activity["planner"] = "active"
            await self._broadcast_agent_status()
            await self._broadcast_thought("Planner", "📝 Creating retrieval plan...")
            plan = await self.planning.create_plan(query, context=context)
            self.agent_activity["planner"] = "idle"
            await self._broadcast_agent_status()
            
            # 2. RETRIEVE: Execute hybrid search (FAISS + BM25 + Neo4j)
            self.agent_activity["retriever"] = "active"
            await self._broadcast_agent_status()
            await self._broadcast_thought("Retriever", "🔍 Searching memories...")
            results = await self.retrieval.hybrid_search(plan, user_id)
            self.agent_activity["retriever"] = "idle"
            await self._broadcast_agent_status()
            await self._broadcast_thought("Retriever", f"📊 Found {len(results)} results")
            
            # 3. CONTEXT: Gather real-time situational awareness
            self.agent_activity["empathy"] = "active"
            await self._broadcast_agent_status()
            await self._broadcast_thought("Empathy", "🎯 Analyzing situational context...")
            async with self.db() as session:
                situational_context = await self.awareness.get_contextual_awareness(user_id, session)
                user_persona = await self.persona_profiler.get_or_create_profile(user_id, session=session)
            self.agent_activity["empathy"] = "idle"
            await self._broadcast_agent_status()

            # 4. ROUTE: Determine the processing path
            self.agent_activity["router"] = "active"
            await self._broadcast_agent_status()
            await self._broadcast_thought("Router", "🔄 Routing to AI provider...")
            route = await self.ai_router.get_route(query)
            self.agent_activity["router"] = "idle"
            await self._broadcast_agent_status()
            
            # 5. GENERATE: Synthesize answer with grounding
            self.agent_activity["generator"] = "active"
            await self._broadcast_agent_status()
            await self._broadcast_thought("Generator", "🤖 Generating response...")
            generation = await self.generator.generate(
                query, 
                context=results, 
                situational_awareness=situational_context, 
                persona=user_persona, 
                route=route
            )
            response_text = generation.get("answer", "")
            self.agent_activity["generator"] = "idle"
            await self._broadcast_agent_status()
            
            # 6. JUDGE: Evaluate the answer quality
            self.agent_activity["judge"] = "active"
            await self._broadcast_agent_status()
            await self._broadcast_thought("Judge", "⚖️ Evaluating response quality...")
            evaluation = await self.judge.evaluate(query, response_text, results)
            self.agent_activity["judge"] = "idle"
            await self._broadcast_agent_status()
            
            # 7. REGENERATE if needed (one attempt)
            if not evaluation.passed:
                logger.warning(f"Judge rejected answer: {evaluation.feedback}")
                await self._broadcast_thought("Judge", f"❌ Failed: {evaluation.feedback}")
                regen_instructions = f"Refine answer based on feedback: {evaluation.feedback}\nQuery: {query}"
                
                self.agent_activity["generator"] = "active"
                await self._broadcast_agent_status()
                await self._broadcast_thought("Generator", "🔄 Regenerating response...")
                generation = await self.generator.generate(
                    regen_instructions, 
                    context=results, 
                    situational_awareness=situational_context, 
                    persona=user_persona, 
                    route=route
                )
                response_text = generation.get("answer", "")
                self.agent_activity["generator"] = "idle"
                await self._broadcast_agent_status()
                
                self.agent_activity["judge"] = "active"
                await self._broadcast_agent_status()
                await self._broadcast_thought("Judge", "⚖️ Re-evaluating response...")
                evaluation = await self.judge.evaluate(query, response_text, results)
                self.agent_activity["judge"] = "idle"
                await self._broadcast_agent_status()
            
            if evaluation.passed:
                await self._broadcast_thought("Judge", f"✅ PASSED! ({evaluation.confidence:.2f})")
            else:
                await self._broadcast_thought("Judge", f"❌ Final evaluation failed")

            # 8. LOG: Store in Layer 2 (Episodic Memory)
            self.agent_activity["episodic"] = "active"
            await self._broadcast_agent_status()
            await self._broadcast_thought("Episodic", "💾 Storing in Layer 2 (Liquid)...")
            entry = EpisodicEntry(
                query=query,
                plan=plan,
                results=results,
                answer=response_text,
                evaluation=evaluation,
                timestamp=datetime.now(timezone.utc)
            )
            await self.episodic_memory.store(entry)
            self.agent_activity["episodic"] = "idle"
            await self._broadcast_agent_status()

            # 9. GRADUATE: Analyze patterns for Layer 3 (Semantic Memory)
            self.agent_activity["semantic"] = "active"
            await self._broadcast_agent_status()
            await self._broadcast_thought("Semantic", "❄️ Checking for Layer 3 (Ice) patterns...")
            await self.check_and_graduate_patterns(query, evaluation)
            self.agent_activity["semantic"] = "idle"
            await self._broadcast_agent_status()

            await self._broadcast_thought("Orchestrator", "✅ Query processed successfully!")
            
            return {
                "answer": response_text,
                "evaluation": evaluation.dict(),
                "confidence": generation.get("confidence", 0.0),
                "reasoning": generation.get("reasoning_steps", []),
                "learned": evaluation.passed
            }
        
        finally:
            # Decrement active task count
            self.active_tasks -= 1
            if self.active_tasks < 0:
                self.active_tasks = 0
            await self._broadcast_agent_status()

    async def check_and_graduate_patterns(self, query: str, eval_res):
        """
        If the Judge fails the Generator repeatedly on a similar query pattern,
        create a permanent 'Constraint' in Semantic Memory.
        """
        if not eval_res.passed:
            logger.info(f"Analyzing error pattern for graduation: {query[:50]}...")
            
            # Look for similar failures in recent history
            recent_entries = await self.episodic_memory.get_recent(limit=10)
            recent_failures = [
                e for e in recent_entries
                if not e.evaluation.passed and query.lower()[:15] in e.query.lower()
            ]
            
            # If recurring failure (3+ times), graduate to Semantic Memory
            if len(recent_failures) >= 2:
                logger.info("Pattern graduated: Creating permanent constraint in Semantic Memory.")
                await self._broadcast_thought("Semantic", "🎓 Graduating pattern to Layer 3 (Ice)!")
                new_pattern = SemanticPattern(
                    pattern_type="hallucination_prevention" if eval_res.faithfulness < 0.6 else "query_refinement",
                    trigger=query,
                    correction=eval_res.feedback or "Ensure factual grounding.",
                    occurrence_count=len(recent_failures) + 1
                )
                await self.semantic_memory.add_pattern(new_pattern)
                await self._broadcast_thought("Semantic", f"✨ Pattern created: {new_pattern.trigger[:30]}...")
