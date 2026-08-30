"""
AI Concierge Service - Intelligent user onboarding and discovery
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging

from app.models.user import User
from app.models.decision_trace import DecisionTrace

logger = logging.getLogger(__name__)


class OnboardingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_onboarding_plan(self, user: User) -> Dict[str, Any]:
        """Generate personalized onboarding plan based on user role and activity."""
        # Analyze user's role and potential needs
        role_insights = await self._analyze_role(user)
        
        # Check existing activity
        activity = await self._check_activity(user)
        
        # Generate personalized recommendations
        recommendations = await self._generate_recommendations(user, role_insights, activity)
        
        return {
            "user": {
                "id": str(user.id),
                "name": user.username,
                "role": user.role,
                "joined": user.created_at.isoformat() if user.created_at else None
            },
            "role_insights": role_insights,
            "activity": activity,
            "recommendations": recommendations,
            "next_steps": [
                "Configure your dashboard",
                "Explore your domain packs",
                "Try the Cognitive Lab",
                "Set up automation rules"
            ]
        }

    async def _analyze_role(self, user: User) -> Dict[str, Any]:
        """Analyze user role and provide role-specific insights."""
        role_configs = {
            "admin": {
                "title": "System Administrator",
                "description": "You have full access to all features and settings.",
                "focus": ["System health", "User management", "Security", "Compliance"],
                "recommended_packs": ["Security Intelligence", "Compliance Intelligence", "Sovereign Control"],
                "quick_actions": ["View system metrics", "Manage users", "Configure providers", "Review audit logs"]
            },
            "analyst": {
                "title": "Intelligence Analyst",
                "description": "You can analyze decisions, patterns, and generate insights.",
                "focus": ["Decision analysis", "Pattern discovery", "Reporting", "Collaboration"],
                "recommended_packs": ["Security Intelligence", "Contract Intelligence", "Procurement Intelligence"],
                "quick_actions": ["Start a new analysis", "Review recent decisions", "Explore patterns", "Generate report"]
            },
            "viewer": {
                "title": "Intelligence Viewer",
                "description": "You can view decisions, patterns, and reports.",
                "focus": ["Decision review", "Pattern exploration", "Report viewing"],
                "recommended_packs": ["Compliance Intelligence", "Contract Intelligence"],
                "quick_actions": ["Browse decisions", "View patterns", "Check reports"]
            }
        }
        
        return role_configs.get(user.role, {
            "title": "User",
            "description": "Customize your experience.",
            "focus": ["Getting started", "Exploring features"],
            "recommended_packs": [],
            "quick_actions": ["Explore dashboard", "Try chat"]
        })

    async def _check_activity(self, user: User) -> Dict[str, Any]:
        """Check user's activity level and history."""
        # Count decisions
        result = await self.db.execute(
            select(DecisionTrace).where(DecisionTrace.user_id == user.id)
        )
        decisions = result.scalars().all()
        
        # Analyze recency
        has_recent = False
        last_activity = None
        if decisions:
            last_decision = max(decisions, key=lambda x: x.timestamp)
            days_since = (datetime.utcnow() - last_decision.timestamp).days
            has_recent = days_since < 7
            last_activity = last_decision.timestamp.isoformat()
        
        return {
            "total_decisions": len(decisions),
            "has_recent_activity": has_recent,
            "last_activity": last_activity,
            "engagement_level": "high" if len(decisions) > 50 else "medium" if len(decisions) > 10 else "low"
        }

    async def _generate_recommendations(self, user: User, role_insights: Dict, activity: Dict) -> List[Dict]:
        """Generate personalized recommendations."""
        recommendations = []
        
        # If low activity, focus on getting started
        if activity["engagement_level"] == "low":
            recommendations.append({
                "type": "getting_started",
                "title": "🚀 Start Your First Analysis",
                "description": "Try asking a question in the Cognitive Lab to see the decision-making process in action.",
                "action": "Go to Cognitive Lab",
                "priority": 1
            })
        
        # If medium activity, suggest deeper exploration
        if activity["engagement_level"] == "medium":
            recommendations.append({
                "type": "exploration",
                "title": "🔍 Discover Patterns",
                "description": "Explore the Intelligence Vault to see patterns emerging from your decisions.",
                "action": "Open Intelligence Vault",
                "priority": 2
            })
        
        # Always suggest role-specific actions
        for action in role_insights.get("quick_actions", [])[:2]:
            recommendations.append({
                "type": "role_based",
                "title": f"💡 {action}",
                "description": f"As a {role_insights.get('title', 'user')}, this is recommended for you.",
                "action": action,
                "priority": 3
            })
        
        return recommendations


class ConciergeAgent:
    """AI Agent for intelligent user onboarding and guidance."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.service = OnboardingService(db)
    
    async def greet_user(self, user: User) -> str:
        """Generate a personalized greeting message."""
        plan = await self.service.get_onboarding_plan(user)
        
        greetings = {
            "admin": f"👋 Welcome back, {user.username}! Your system is healthy and ready. You have {plan['activity']['total_decisions']} decisions processed. What would you like to manage today?",
            "analyst": f"👋 Hello, {user.username}! You've analyzed {plan['activity']['total_decisions']} decisions. I see patterns waiting to be discovered. Shall we explore them?",
            "viewer": f"👋 Welcome, {user.username}! There are {plan['activity']['total_decisions']} decisions available for review. Let me know what you'd like to see."
        }
        
        # If first time or low activity
        if plan["activity"]["engagement_level"] == "low":
            return f"👋 Welcome to PersonaVault, {user.username}! I'm your AI Concierge. Let me show you how to get started. 🚀"
        
        return greetings.get(user.role, f"👋 Welcome back, {user.username}!")
    
    async def suggest_next_action(self, user: User) -> Dict[str, Any]:
        """Suggest the next best action for the user."""
        plan = await self.service.get_onboarding_plan(user)
        
        if plan["activity"]["engagement_level"] == "low":
            return {
                "action": "Start a conversation",
                "description": "Ask a question in the Cognitive Lab to see how decisions are made.",
                "priority": "high"
            }
        elif plan["activity"]["engagement_level"] == "medium":
            return {
                "action": "Explore patterns",
                "description": "Your decisions are forming patterns. See what intelligence has been crystallized.",
                "priority": "high"
            }
        else:
            return {
                "action": "Review decisions",
                "description": f"You have {plan['activity']['total_decisions']} decisions. Review the latest ones for insights.",
                "priority": "medium"
            }
