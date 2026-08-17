"""
Multi-Agent Orchestrator with Parallel Execution
Transforms sequential agent pipeline into parallel processing
"""
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field

from app.swarm.core.planner import PlannerAgent
from app.swarm.core.retriever import RetrievalAgent
from app.swarm.core.generator import GeneratorAgent
from app.swarm.core.judge import JudgeAgent
from app.services.working_memory import WorkingMemory
from app.services.episodic_memory import EpisodicMemory
from app.services.semantic_memory import SemanticMemory
from app.schemas.memory_schemas import EpisodicEntry, MemoryResult, RetrievalPlan
from app.models import SemanticPattern
from app.swarm.core.router import AIRouter
from app.services.awareness_service import AwarenessService
from app.api.v1.endpoints.persona import PersonaProfiler
from app.utils.websocket import manager

logger = logging.getLogger(__name__)

@dataclass
class ExecutionStage:
    """Represents a stage in the execution pipeline."""
    name: str
    tasks: List[asyncio.Task]
    results: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    
    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0

class MultiAgentOrchestrator:
    """
    Parallel-optimized orchestration engine.
    Executes independent agent tasks in parallel while maintaining dependencies.
    """
    
    def __init__(self, db_session, blackboard, agents: Dict[str, Any] = None):
        self.db = db_session
        self.blackboard = blackboard
        self.working_memory = WorkingMemory()
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
        
        # Agent references
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
        self.episodic_memory = self.agents.get("episodic") or EpisodicMemory(db_session)
        
        self.awareness = AwarenessService()
        self.persona_profiler = PersonaProfiler(db_session)
        
        # Performance tracking
        self._stages: List[ExecutionStage] = []
        self._parallel_execution = True  # Enable parallel mode
    
    async def run(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the cognitive pipeline with parallel processing."""
        self._stages.clear()
        start_time = datetime.now(timezone.utc)
        
        self.active_tasks += 1
        await self._broadcast_agent_status()
        await self._broadcast_thought("Orchestrator", f"🚀 Parallel processing: '{query[:50]}...'")
        
        user_id = self._get_user_id(context)
        context["user_id"] = user_id
        
        try:
            # STAGE 1: Planning + Context Gathering (PARALLEL)
            stage1 = ExecutionStage(name="Planning + Context", tasks=[])
            logger.info("⏱️ Stage 1: Starting parallel planning and context gathering")
            await self._broadcast_thought("Orchestrator", "📝 Stage 1: Planning + Context (Parallel)")
            
            plan_task = asyncio.create_task(self.planning.create_plan(query, context=context))
            awareness_task = asyncio.create_task(self._gather_awareness(user_id))
            persona_task = asyncio.create_task(self._gather_persona(user_id))
            
            plan, situational_context, user_persona = await asyncio.gather(
                plan_task, awareness_task, persona_task, return_exceptions=True
            )
            
            if isinstance(plan, Exception):
                logger.error(f"Planning failed: {plan}")
                return await self._handle_error(query, context, "planning", plan)
            
            self.agent_activity["planner"] = "idle"
            self.agent_activity["empathy"] = "idle"
            stage1.end_time = datetime.now(timezone.utc)
            self._stages.append(stage1)
            logger.info(f"⏱️ Stage 1 complete: {stage1.duration_ms:.0f}ms")
            
            # STAGE 2: Retrieval + Routing + Reasoning (PARALLEL)
            stage2 = ExecutionStage(name="Retrieval + Routing", tasks=[])
            logger.info("⏱️ Stage 2: Starting parallel retrieval, routing, and reasoning")
            await self._broadcast_thought("Orchestrator", "🔍 Stage 2: Retrieval + Routing (Parallel)")
            
            retrieval_task = asyncio.create_task(self.retrieval.hybrid_search(plan, user_id))
            route_task = asyncio.create_task(self.ai_router.get_route(query))
            reasoning_task = asyncio.create_task(self._reason(query, situational_context))
            
            results, route, reasoning_insight = await asyncio.gather(
                retrieval_task, route_task, reasoning_task, return_exceptions=True
            )
            
            if isinstance(results, Exception):
                logger.error(f"Retrieval failed: {results}")
                results = []
            
            self.agent_activity["retriever"] = "idle"
            self.agent_activity["router"] = "idle"
            stage2.end_time = datetime.now(timezone.utc)
            self._stages.append(stage2)
            logger.info(f"⏱️ Stage 2 complete: {stage2.duration_ms:.0f}ms (found {len(results) if isinstance(results, list) else 0} results)")
            
            # STAGE 3: Generation (SEQUENTIAL)
            stage3 = ExecutionStage(name="Generation", tasks=[])
            logger.info("⏱️ Stage 3: Starting generation")
            await self._broadcast_thought("Orchestrator", "🤖 Stage 3: Generation")
            
            generation = await self.generator.generate(
                query,
                context=results if isinstance(results, list) else [],
                reasoning_insight=reasoning_insight if not isinstance(reasoning_insight, Exception) else None,
                situational_awareness=situational_context if not isinstance(situational_context, Exception) else {},
                persona=user_persona if not isinstance(user_persona, Exception) else None,
                route=route if isinstance(route, dict) else {}
            )
            
            response_text = generation.get("answer", "")
            confidence = generation.get("confidence", 0.5)
            
            self.agent_activity["generator"] = "idle"
            stage3.end_time = datetime.now(timezone.utc)
            self._stages.append(stage3)
            logger.info(f"⏱️ Stage 3 complete: {stage3.duration_ms:.0f}ms")
            
            # STAGE 4: Evaluation + Validation + Empathy (PARALLEL)
            stage4 = ExecutionStage(name="Evaluation + Validation", tasks=[])
            logger.info("⏱️ Stage 4: Starting parallel evaluation and validation")
            await self._broadcast_thought("Orchestrator", "⚖️ Stage 4: Evaluation + Validation (Parallel)")
            
            judge_task = asyncio.create_task(self.judge.evaluate(query, response_text, results if isinstance(results, list) else []))
            validate_task = asyncio.create_task(self._validate(query, response_text, results if isinstance(results, list) else []))
            empathy_task = asyncio.create_task(self._analyze_empathy(situational_context if not isinstance(situational_context, Exception) else {}))
            
            evaluation, validation, empathy_result = await asyncio.gather(
                judge_task, validate_task, empathy_task, return_exceptions=True
            )
            
            if isinstance(evaluation, Exception):
                logger.error(f"Judge failed: {evaluation}")
                evaluation = None
            
            if evaluation and not evaluation.passed:
                logger.warning(f"⚠️ Judge rejected answer: {evaluation.feedback}")
                await self._broadcast_thought("Judge", f"❌ Failed: {evaluation.feedback}")
                
                regen_instructions = f"Refine answer based on feedback: {evaluation.feedback}\nQuery: {query}"
                generation = await self.generator.generate(
                    regen_instructions,
                    context=results if isinstance(results, list) else [],
                    situational_awareness=situational_context if not isinstance(situational_context, Exception) else {},
                    persona=user_persona if not isinstance(user_persona, Exception) else None,
                    route=route if isinstance(route, dict) else {}
                )
                response_text = generation.get("answer", "")
                confidence = generation.get("confidence", 0.5)
                evaluation = await self.judge.evaluate(query, response_text, results if isinstance(results, list) else [])
            
            self.agent_activity["judge"] = "idle"
            self.agent_activity["validator"] = "idle"
            stage4.end_time = datetime.now(timezone.utc)
            self._stages.append(stage4)
            logger.info(f"⏱️ Stage 4 complete: {stage4.duration_ms:.0f}ms")
            
            if evaluation and evaluation.passed:
                await self._broadcast_thought("Judge", f"✅ PASSED! ({evaluation.confidence:.2f})")
            else:
                await self._broadcast_thought("Judge", f"❌ Final evaluation failed")
            
            # STAGE 5: Learning + Storage (PARALLEL)
            stage5 = ExecutionStage(name="Learning + Storage", tasks=[])
            logger.info("⏱️ Stage 5: Starting parallel learning and storage")
            await self._broadcast_thought("Orchestrator", "💾 Stage 5: Learning + Storage (Parallel)")
            
            store_task = asyncio.create_task(self._store_episodic(query, plan, results, response_text, evaluation))
            graduate_task = asyncio.create_task(self._graduate_patterns(query, evaluation))
            asyncio.create_task(self._safe_gather(store_task, graduate_task))
            
            self.agent_activity["episodic"] = "idle"
            self.agent_activity["semantic"] = "idle"
            stage5.end_time = datetime.now(timezone.utc)
            self._stages.append(stage5)
            logger.info(f"⏱️ Stage 5 started: {stage5.duration_ms:.0f}ms")
            
            total_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            logger.info(f"✅ Query processed in {total_time:.0f}ms")
            await self._broadcast_thought("Orchestrator", f"✅ Done! ({total_time:.0f}ms)")
            
            thought_process = self._build_thought_process()
            
            return {
                "answer": response_text,
                "evaluation": evaluation.dict() if evaluation else {},
                "confidence": confidence,
                "reasoning": generation.get("reasoning_steps", []),
                "learned": evaluation.passed if evaluation else False,
                "thought_process": thought_process,
                "total_time_ms": total_time,
                "stages": [{"name": s.name, "duration_ms": s.duration_ms} for s in self._stages]
            }
            
        finally:
            self.active_tasks -= 1
            if self.active_tasks < 0:
                self.active_tasks = 0
            await self._broadcast_agent_status()
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _get_user_id(self, context: Dict[str, Any]) -> int:
        user_id = context.get("user_id")
        if user_id is None:
            return 1
        if hasattr(user_id, 'id'):
            return user_id.id
        try:
            return int(user_id)
        except (ValueError, TypeError):
            return 1
    
    async def _gather_awareness(self, user_id: int):
        try:
            async with self.db() as session:
                return await self.awareness.get_contextual_awareness(user_id, session)
        except Exception as e:
            logger.error(f"Awareness gathering failed: {e}")
            return {}
    
    async def _gather_persona(self, user_id: int):
        try:
            async with self.db() as session:
                return await self.persona_profiler.get_or_create_profile(user_id, session=session)
        except Exception as e:
            logger.error(f"Persona gathering failed: {e}")
            return None
    
    async def _reason(self, query: str, situational_context: Dict):
        if not self.reasoner:
            return None
        try:
            return await self.reasoner.analyze(query, {"situational_awareness": situational_context})
        except Exception as e:
            logger.error(f"Reasoning failed: {e}")
            return None
    
    async def _validate(self, query: str, response: str, results: List):
        if not self.validator:
            return {"is_valid": True}
        try:
            return await self.validator.validate(query, results, response)
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"is_valid": True}
    
    async def _analyze_empathy(self, situational_context: Dict):
        if not self.empathy:
            return {"tone": "neutral"}
        try:
            return await self.empathy.determine_tone(situational_context)
        except Exception as e:
            logger.error(f"Empathy analysis failed: {e}")
            return {"tone": "neutral"}
    
    async def _store_episodic(self, query: str, plan, results, response_text, evaluation):
        try:
            entry = EpisodicEntry(
                query=query,
                plan=plan,
                results=results,
                answer=response_text,
                evaluation=evaluation,
                timestamp=datetime.now(timezone.utc)
            )
            await self.episodic_memory.store(entry)
        except Exception as e:
            logger.error(f"Episodic storage failed: {e}")
    
    async def _graduate_patterns(self, query: str, evaluation):
        if not evaluation or evaluation.passed:
            return
        try:
            await self.check_and_graduate_patterns(query, evaluation)
        except Exception as e:
            logger.error(f"Pattern graduation failed: {e}")
    
    async def _safe_gather(self, *tasks):
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Background task error: {e}")
    
    def _build_thought_process(self) -> List[Dict]:
        return [
            {
                "step": i + 1,
                "label": stage.name,
                "description": f"Completed in {stage.duration_ms:.0f}ms",
                "status": "complete",
                "duration": stage.duration_ms / 1000
            }
            for i, stage in enumerate(self._stages)
        ]
    
    async def _handle_error(self, query: str, context: Dict, stage: str, error: Exception) -> Dict:
        logger.error(f"Error in {stage}: {error}")
        return {
            "answer": f"I encountered an error during {stage}. Please try again.",
            "evaluation": {"passed": False, "feedback": f"Error in {stage}"},
            "confidence": 0.0,
            "reasoning": [],
            "learned": False,
            "error": str(error)
        }
    
    async def hybrid_search(self, plan: RetrievalPlan, user_id: int) -> List[MemoryResult]:
        """Execute hybrid search for memories using local retriever."""
        results = []
        try:
            from app.services.local_retriever import LocalRetriever
            retriever = LocalRetriever()
            
            if plan.semantic_queries:
                query = plan.semantic_queries[0]
                local_results = await retriever.search(query, user_id, limit=20)
                for r in local_results:
                    results.append(MemoryResult(
                        content=r.get("content", ""),
                        source="local",
                        score=r.get("score", 0.5),
                        metadata={"memory_id": r.get("id")}
                    ))
            
            if plan.keyword_queries:
                from app.services.keyword_search import KeywordSearch
                keyword_search = KeywordSearch()
                kw_results = keyword_search.search(plan.keyword_queries[0], user_id, limit=10)
                for r in kw_results:
                    if not any(res.content == r.get("content", "") for res in results):
                        results.append(MemoryResult(
                            content=r.get("content", ""),
                            source="keyword",
                            score=r.get("score", 0.3),
                            metadata={"memory_id": r.get("id")}
                        ))
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
        
        return self._normalize_and_deduplicate(results)
    
    def _normalize_and_deduplicate(self, results: List[MemoryResult]) -> List[MemoryResult]:
        seen = set()
        unique = []
        for r in results:
            if r.content not in seen:
                seen.add(r.content)
                unique.append(r)
        unique.sort(key=lambda x: x.score, reverse=True)
        return unique[:20]
    
    async def check_and_graduate_patterns(self, query: str, eval_res):
        """Existing pattern graduation logic."""
        if not eval_res.passed:
            logger.info(f"Analyzing error pattern for graduation: {query[:50]}...")
            recent_entries = await self.episodic_memory.get_recent(limit=10)
            recent_failures = [
                e for e in recent_entries
                if not e.evaluation.passed and query.lower()[:15] in e.query.lower()
            ]
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
    
    async def _broadcast_agent_status(self):
        """Broadcast agent status."""
        try:
            await manager.broadcast(json.dumps({
                "type": "agent_status",
                "active_tasks": self.active_tasks,
                "agent_activity": self.agent_activity
            }))
        except Exception:
            pass
    
    async def _broadcast_thought(self, agent: str, content: str):
        """Broadcast thought."""
        try:
            await manager.broadcast(json.dumps({
                "type": "thought_stream",
                "agent": agent,
                "content": content
            }))
        except Exception:
            pass
