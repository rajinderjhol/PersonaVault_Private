from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.db.session import Base
from datetime import datetime, timezone

class PendingAction(Base):
    __tablename__ = "pending_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_type = Column(String)
    query = Column(Text)
    options = Column(JSON)
    status = Column(String, default="pending")  # pending, approved, rejected, timed_out
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)
    user_response = Column(Text, nullable=True)

    # VeriLinkOS Integration Placeholders
    vap_hash = Column(String, nullable=True, index=True)  # Cryptographic receipt hash
    action_chain_id = Column(String, nullable=True)      # Link to the VeriLink Action Chain