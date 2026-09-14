from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Float, Float, JSON, Boolean, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base

class TraceStep(str, enum.Enum):
    PERCEPTION = "perception"
    POLICY_MATCH = "policy_match"
    AI_RECOMMENDATION = "ai_recommendation"
    ACTION = "action"
    OUTCOME = "outcome"
    SUMMARY = "summary" # New step for top-level summaries

class DecisionTrace(Base):
    __tablename__ = "decision_traces"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)
    
    # Existing fields for granular steps
    step = Column(Enum(TraceStep), nullable=False, default=TraceStep.SUMMARY)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Structured data for each step
    data = Column(JSON, nullable=False, default=dict)
    
    # Metadata
    confidence_score = Column(Float, nullable=True)
    agent_id = Column(String, nullable=True)
    is_crystallized = Column(Boolean, default=False)
    
    # --- New Fields for Top-Level Decision Record (Orchestrator Compatibility) ---
    decision_id = Column(String, nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query = Column(String, nullable=True)
    response = Column(String, nullable=True)
    trace = Column(JSON, nullable=True) # Stores the collection of traces
    explanation = Column(String, nullable=True)
    pack_name = Column(String, nullable=True)
    pack_version = Column(String, nullable=True)
    latency_ms = Column(Float, nullable=True)
    
    # Relationships
    provenance_links = relationship("ProvenanceRecord", back_populates="trace")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "step": self.step.value,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "data": self.data,
            "confidence_score": self.confidence_score,
            "is_crystallized": self.is_crystallized,
            "decision_id": self.decision_id,
            "user_id": self.user_id,
            "query": self.query,
            "response": self.response,
            "trace": self.trace,
            "explanation": self.explanation,
            "pack": {
                "name": self.pack_name,
                "version": self.pack_version
            } if self.pack_name else None,
            "latency_ms": self.latency_ms,
            "provenance_links": [p.to_dict() for p in self.provenance_links]
        }

class ProvenanceRecord(Base):
    __tablename__ = "provenance_records"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    trace_id = Column(PG_UUID(as_uuid=True), ForeignKey("decision_traces.id"), nullable=False)
    
    # Evidence anchoring
    source_type = Column(String, nullable=False)  # "document", "policy", "vector_memory", etc.
    source_id = Column(String, nullable=False)
    source_text = Column(String, nullable=True)
    relevance_score = Column(Float, nullable=True)
    
    # Cryptographic receipt placeholder
    receipt_hash = Column(String, nullable=True)
    
    trace = relationship("DecisionTrace", back_populates="provenance_links")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_text": self.source_text[:200] + "..." if self.source_text and len(self.source_text) > 200 else self.source_text,
            "relevance_score": self.relevance_score,
            "receipt_hash": self.receipt_hash
        }
