from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from datetime import datetime
from app.db.session import Base
from sqlalchemy.orm import relationship

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default={})
    users = relationship("User", back_populates="organization")
