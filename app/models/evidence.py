"""
Decision Evidence Models
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Float, Text, Boolean, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base
import hashlib

class EvidenceBlock(Base):
    """A single evidence block extracted from a document."""
    __tablename__ = "evidence_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(String(64), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    source = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # pdf, txt, clinical_note, contract
    block_metadata = Column(JSON, default={})
    confidence = Column(Float, default=0.8)
    provenance_score = Column(Float, default=0.8)
    quality_score = Column(Float, default=0.0)
    is_qualified = Column(Boolean, default=False)
    tags = Column(JSON, default=[])
    verifiable_attestation = Column(String(255), nullable=True)
    extracted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    decision_links = relationship("DecisionEvidenceLink", back_populates="evidence")

class DecisionEvidenceLink(Base):
    """Links evidence blocks to decisions."""
    __tablename__ = "decision_evidence_links"
    
    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(Integer, ForeignKey("behaviour_events.id"), nullable=False, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence_blocks.id"), nullable=False, index=True)
    confidence = Column(Float, default=0.8)
    reasoning = Column(Text)
    linked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    audit_hash = Column(String(64), nullable=False)
    
    # Relationships
    decision = relationship("BehaviourEvent")
    evidence = relationship("EvidenceBlock", back_populates="decision_links")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Generate audit hash on creation
        self.audit_hash = hashlib.sha256(
            f"{self.decision_id}{self.evidence_id}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

class DocumentIngestionJob(Base):
    """Tracks document ingestion jobs."""
    __tablename__ = "document_ingestion_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    total_blocks = Column(Integer, default=0)
    qualified_blocks = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    job_metadata = Column(JSON, default={})

class BulkIngestionJob(Base):
    """Tracks bulk ingestion jobs."""
    __tablename__ = "bulk_ingestion_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), unique=True, index=True, nullable=False)
    folder_path = Column(String(512), nullable=False)
    status = Column(String(20), default="pending")
    total_files = Column(Integer, default=0)
    successful_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    job_metadata = Column(JSON, default={})
