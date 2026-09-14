from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Float, Text, JSON, Float
from datetime import datetime, timezone
from app.db.session import Base

class SimulationJob(Base):
    """Tracks policy simulation jobs."""
    __tablename__ = "simulation_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), unique=True, index=True, nullable=False)
    domain = Column(String(50), nullable=False)
    params = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    result_metrics = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    attestation = Column(String(255), nullable=True)
