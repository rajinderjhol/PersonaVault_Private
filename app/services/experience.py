import logging
from typing import Dict, Any, List
from datetime import datetime
from orchestrator import MultiAgentOrchestrator
from app.schemas.memory_schemas import MemoryResult, EpisodicEntry, RetrievalPlan

logger = logging.getLogger(__name__)

class ExperienceLearningService:
    """
    Enables robots to learn from experience using PersonaVault's self-improving pipeline.
    """
    
    def __init__(self, db_session, orchestrator: MultiAgentOrchestrator):
        self.db = db_session
        self.orchestrator = orchestrator

    async def learn_from_task(self,
                             task_id: str,
                             task_description: str,
                             task_result: dict,
                             robot_id: str,
                             user_id: int):
        """
        Analyze task performance and graduate successful patterns.
        """
        logger.info(f"Robot {robot_id} analyzing experience for task {task_id}")

        # 1. Evaluate task success using the Judge Agent
        # We wrap the task result as context for the judge
        context = [MemoryResult(
            content=str(task_result),
            source="robot_execution",
            score=1.0
        )]
        
        # 1. Evaluate task success using the Judge Agent from the global MultiAgentOrchestrator
        judge = self.orchestrator.agents.get("judge")
        if not judge:
            logger.error("Judge agent not found in orchestrator. Cannot evaluate experience.")
            return {"task_id": task_id, "learned": False, "error": "No judge available"}
            
        evaluation = await judge.evaluate(
            query=task_description,
            answer=task_result.get("outcome", ""),
            context=context
        )
        
        # 2. Log the experience to Layer 2 (Episodic Memory)
        # The background ConsolidationTask will automatically analyze these entries 
        # for recurring patterns to graduate them into Layer 3 (Semantic Memory).
        episodic = self.orchestrator.agents.get("episodic")
        if episodic:
            entry = EpisodicEntry(
                query=task_description,
                plan=RetrievalPlan(needs_retrieval=False, semantic_queries=[], keyword_queries=[], graph_traversals=[]),
                results=context,
                answer=task_result.get("outcome", ""),
                evaluation=evaluation,
                timestamp=datetime.utcnow()
            )
            await episodic.store(entry)
            logger.info(f"Robot experience logged to episodic memory for task {task_id}")
        else:
            logger.warning("Episodic Memory agent missing in orchestrator. Experience will not be persisted for learning.")
            
        return {
            "task_id": task_id,
            "learned": evaluation.passed,
            "feedback": evaluation.feedback
        }