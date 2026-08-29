import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID
from app.services.episodic_memory import EpisodicMemory
from app.services.vector_service import vector_service
from app.schemas.memory_schemas import EpisodicEntry, RetrievalPlan, EvaluationMetrics, MemoryResult
from app.services.trace_service import TraceService
from app.models.decision_trace import TraceStep

logger = logging.getLogger(__name__)

class RoboticsPerceptionService:
    """
    Integrates PersonaVault memory with robotic perception systems.
    Handles Grounded Perception by structuring multimodal inputs.
    """
    
    def __init__(self, db_session, trace_service: Optional[TraceService] = None):
        from app.repositories.sqlalchemy.episodic import SQLEpisodicTaskRepository
        self.episodic_memory = EpisodicMemory(SQLEpisodicTaskRepository(db_session))
        self.vector_service = vector_service
        self.trace_service = trace_service

    async def process_robot_observation(self,
                                       observation_data: dict,
                                       robot_id: str,
                                       user_id: int,
                                       session_id: Optional[int] = None) -> dict:
        """
        Process a robot's observation and store it in grounded episodic memory.
        """
        timestamp = datetime.now(timezone.utc)
        
        # 1. Extract entities (agents, objects, actions) - Stub for actual CV/NLP integration
        entities = observation_data.get("entities", [])
        spatial = observation_data.get("spatial", "unknown_location")
        
        # 2. Format as a PersonaVault episodic entry
        summary = f"Robot {robot_id} observed {len(entities)} entities at {spatial}."
        
        # --- TRACE CAPTURE: PERCEPTION ---
        trace_id = None
        if self.trace_service and session_id:
            trace = await self.trace_service.capture_step(
                session_id=session_id,
                step=TraceStep.PERCEPTION,
                data={
                    "robot_id": robot_id,
                    "entities": entities,
                    "spatial_context": spatial,
                    "observation_summary": summary,
                    "raw_data": observation_data.get("raw_text", "")
                },
                agent_id="RoboticsPerceptionService",
                confidence_score=0.85
            )
            trace_id = str(trace.id) if trace else None
            
            # Add provenance for entities
            if trace:
                for entity in entities[:5]:
                    await self.trace_service.add_provenance(
                        trace_id=trace.id,
                        source_type="entity_extraction",
                        source_id=entity.get("id", f"entity_{hash(entity.get('text', ''))}"),
                        source_text=entity.get("text", ""),
                        relevance_score=entity.get("score", 0.7)
                    )
        # --- END TRACE CAPTURE ---
        
        # 3. Store in episodic memory
        entry = EpisodicEntry(
            query=f"Observation at {spatial}",
            plan=RetrievalPlan(needs_retrieval=False, reasoning="Sensory input processing"),
            results=[],
            answer=summary,
            evaluation=EvaluationMetrics(coverage=1.0, relevance=1.0, faithfulness=1.0, passed=True),
            timestamp=timestamp
        )
        await self.episodic_memory.store(entry)
        
        # 4. Index for semantic retrieval
        content_to_index = f"{summary} Context: {observation_data.get('raw_text', '')}"
        await self.vector_service.index_memory(0, content_to_index, user_id)
        
        logger.info(f"Processed grounded perception for robot {robot_id}")
        
        return {
            "type": "robot_observation",
            "robot_id": robot_id,
            "entities": entities,
            "spatial_context": spatial,
            "summary": summary,
            "timestamp": timestamp.isoformat(),
            "trace_id": trace_id
        }
