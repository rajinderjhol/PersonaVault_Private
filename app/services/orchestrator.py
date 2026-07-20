import logging
from typing import Dict, Any, List
from datetime import datetime
from app.services.planning_agent import PlanningAgent
from app.services.retrieval_agent import RetrievalAgent
from app.services.generator_agent import GeneratorAgent
from app.services.judge_agent import JudgeAgent
from app.services.working_memory import WorkingMemory
from app.services.episodic_memory import EpisodicMemory
from app.services.semantic_memory import SemanticMemory
from app.schemas.memory_schemas import EpisodicEntry, SemanticPattern, MemoryResult
from app.services.ai_router import AIRouter
from app.services.awareness_service import AwarenessService
from app.api.v1.endpoints.persona import PersonaProfiler

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """
    Main closed-loop execution engine for PersonaVault.
    
    Orchestrates the cognitive pipeline by transitioning data through three distinct memory layers:
    Layer 1 (Working): Current query and situational context.
    Layer 2 (Episodic): Task history and short-term interactions.
    Layer 3 (Semantic): Long-term learned patterns and constraints.
    """
    def __init__(self, db_session):
        self.db = db_session
        self.working_memory = WorkingMemory()
        self.episodic_memory = EpisodicMemory(db_session)
        self.semantic_memory = SemanticMemory(db_session)
        self.planning = PlanningAgent(self.semantic_memory)
        self.retrieval = RetrievalAgent()
        self.generator = GeneratorAgent()
        self.judge = JudgeAgent()
        self.ai_router = AIRouter(engine_mode="Local-First (Ollama)")
        self.awareness = AwarenessService()
        self.persona_profiler = PersonaProfiler(db_session)

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
        
        user_id = context.get("user_id")

        # 1. PLAN: Create retrieval plan with learned patterns
        plan = await self.planning.create_plan(query, context=context)
        
        # 2. RETRIEVE: Execute hybrid search (FAISS + BM25 + Neo4j)
        results = await self.retrieval.hybrid_search(plan, user_id)
        
        # 3. CONTEXT: Gather real-time situational awareness and persona
        situational_context = await self.awareness.get_contextual_awareness(user_id, self.db)
        user_persona = await self.persona_profiler.get_or_create_profile(user_id)

        # 4. ROUTE: Determine the processing path
        route = await self.ai_router.get_route(query)
        
        # 5. GENERATE: Synthesize answer with grounding
        generation = await self.generator.generate(query, context=results, situational_awareness=situational_context, persona=user_persona, route=route)
        response_text = generation.get("answer", "")
        
        # 6. JUDGE: Evaluate the answer quality
        evaluation = await self.judge.evaluate(query, response_text, results)
        
        # 6. REGENERATE if needed (one attempt)
        if not evaluation.passed:
            logger.warning(f"Judge rejected answer: {evaluation.feedback}")
            regen_instructions = f"Refine answer based on feedback: {evaluation.feedback}\nQuery: {query}"
            generation = await self.generator.generate(regen_instructions, context=results, route=route)
            response_text = generation.get("answer", "")
            evaluation = await self.judge.evaluate(query, response_text, results)

        # 7. LOG: Store in Layer 2 (Episodic Memory)
        entry = EpisodicEntry(
            query=query,
            plan=plan,
            results=results,
            answer=response_text,
            evaluation=evaluation,
            timestamp=datetime.utcnow()
        )
        await self.episodic_memory.store(entry)

        # 8. GRADUATE: Analyze patterns for Layer 3 (Semantic Memory)
        await self.check_and_graduate_patterns(query, evaluation)

        return {
            "answer": response_text,
            "evaluation": evaluation.dict(),
            "confidence": generation.get("confidence", 0.0),
            "reasoning": generation.get("reasoning_steps", []),
            "learned": evaluation.passed
        }

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
                new_pattern = SemanticPattern(
                    pattern_type="hallucination_prevention" if eval_res.faithfulness < 0.6 else "query_refinement",
                    trigger=query,
                    correction=eval_res.feedback or "Ensure factual grounding.",
                    occurrence_count=len(recent_failures) + 1
                )
                await self.semantic_memory.add_pattern(new_pattern)
