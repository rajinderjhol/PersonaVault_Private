from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from app.db.session import Base

class SystemConfig(Base):
    __tablename__ = "system_configs"
    __table_args__ = {'extend_existing': True}
    key = Column(String, primary_key=True, index=True)
    value = Column(JSON, nullable=False) # Changed from String to JSON
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
