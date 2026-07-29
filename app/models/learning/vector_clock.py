"""
Vector Clock Model for causal ordering of events in multi-agent systems.
Enables conflict detection and resolution using CRDT semantics.
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from app.db.session import Base

class VectorClock(Base):
    __tablename__ = "vector_clocks"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, index=True, nullable=True)
    agent_id = Column(String, index=True, nullable=False)
    clock = Column(JSON, default={})  # {agent_id: counter}
    timestamp = Column(DateTime, default=lambda: datetime.utcnow())
    
    def increment(self, agent_id: str):
        """Increment clock for a specific agent."""
        self.clock[agent_id] = self.clock.get(agent_id, 0) + 1
    
    def is_causal(self, other: 'VectorClock') -> bool:
        """Check if this clock is causally related to another."""
        for agent, count in self.clock.items():
            if other.clock.get(agent, 0) > count:
                return False
        return True
    
    def is_concurrent(self, other: 'VectorClock') -> bool:
        """Check if two clocks are concurrent (conflicting)."""
        return not self.is_causal(other) and not other.is_causal(self)
    
    def __repr__(self):
        return f"<VectorClock agent={self.agent_id} clock={self.clock}>"
