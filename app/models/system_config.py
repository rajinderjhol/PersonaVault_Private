from sqlalchemy import Column, String, DateTime
from datetime import datetime
from app.db.session import Base

class SystemConfig(Base):
    __tablename__ = "system_configs"
    __table_args__ = {'extend_existing': True}
    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)  # Changed from JSON to String
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
