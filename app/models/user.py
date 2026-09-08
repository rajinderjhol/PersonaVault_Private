from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON
from datetime import datetime
from app.db.session import Base
from sqlalchemy.orm import relationship
from app.models.intelligence_source import IntelligenceSource

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="user")
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    sidebar_prefs = Column(JSON, default={
        "elements": [
            {"id": "dashboard", "type": "navigation", "label": "Dashboard", "icon": "📊", "visible": True},
            {"id": "chat", "type": "navigation", "label": "Chat", "icon": "💬", "visible": True},
            {"id": "swarm", "type": "navigation", "label": "Swarm", "icon": "🐝", "visible": True}
        ],
        "order": ["dashboard", "chat", "swarm"],
        "collapsed": False
    })
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # relationships
    organization = relationship("Organization", back_populates="users")
    sessions = relationship("UserSession", back_populates="user")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    intelligence_sources = relationship("IntelligenceSource", back_populates="user", cascade="all, delete-orphan")
