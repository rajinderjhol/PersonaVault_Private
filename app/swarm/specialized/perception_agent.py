from typing import Dict, Any, List
import uuid
from datetime import datetime
from app.swarm.base import BaseAgent
from app.swarm.context import AgentEnvironmentContext
from app.api.v2.models.observation import Observation, ObservationStatus
from app.api.v2.models.provenance import ProvenanceRef

class PerceptionAgent(BaseAgent):
    """
    Universal Perception Agent: Turns raw signals into structured observations.
    """
    
    def __init__(self, name: str = "PerceptionAgent"):
        super().__init__(name)
    
    async def perceive(
        self,
        context: AgentEnvironmentContext,
        raw_signals: List[Dict[str, Any]]
    ) -> List[Observation]:
        """
        Process raw signals and produce structured observations.
        """
        observations = []
        
        for signal in raw_signals:
            observation = await self._process_signal(context, signal)
            if observation:
                observations.append(observation)
        
        return observations
    
    async def _process_signal(
        self,
        context: AgentEnvironmentContext,
        signal: Dict[str, Any]
    ) -> Observation:
        """
        Process a single raw signal into a structured observation.
        """
        # 1. Validate source
        source_type = signal.get("source_type", "unknown")
        source_id = signal.get("source_id", "unknown")
        
        # 2. Extract content
        content = signal.get("content", {})
        
        # 3. Create observation
        observation = Observation(
            id=str(uuid.uuid4()),
            environment_id=context.environment.id,
            observed_at=datetime.utcnow(),
            observer_id=self.name,
            content=content,
            confidence=signal.get("confidence", 0.5),
            provenance=[ProvenanceRef(source_type=source_type, source_id=source_id)],
            status=ObservationStatus.CANDIDATE
        )
        
        return observation
