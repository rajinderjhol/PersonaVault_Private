from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Float
from datetime import datetime, timezone
from app.db.session import Base

class SystemConfig(Base):
    __tablename__ = "system_configs"
    __table_args__ = {'extend_existing': True}
    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)  # Changed from JSON to String
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
