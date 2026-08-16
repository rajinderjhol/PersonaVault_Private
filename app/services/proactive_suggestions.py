"""
Proactive Suggestion Engine
Translates insights into actionable suggestions in the UI.
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.predictive import PredictiveIntelligence
from app.services.self_improving import SelfImprovingIntelligence

logger = logging.getLogger(__name__)

class ProactiveSuggestionEngine:
    """
    Generates proactive suggestions based on predictive intelligence.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.predictive = PredictiveIntelligence(db)
        self.self_improving = SelfImprovingIntelligence(db)
    
    async def get_suggestions(self, user_id: int, context: Dict = None) -> List[Dict]:
        """
        Get proactive suggestions for a user.
        """
        suggestions = []
        
        # 1. Get user predictions
        predictions = await self.predictive.get_user_predictions(user_id)
        
        # 2. Get risks
        risks = await self.predictive.identify_emerging_risks()
        
        # 3. Generate suggestions based on predictions
        for need in predictions.get("predicted_needs", []):
            suggestion = await self._generate_suggestion(need, user_id)
            if suggestion:
                suggestions.append(suggestion)
        
        # 4. Generate suggestions based on risks
        for risk in risks:
            if risk.get("level") in ["high", "medium"]:
                suggestion = await self._generate_risk_suggestion(risk, user_id)
                if suggestion:
                    suggestions.append(suggestion)
        
        # 5. Add quick actions based on context
        if context:
            quick_actions = await self._get_quick_actions(user_id, context)
            suggestions.extend(quick_actions)
        
        # Sort by priority
        suggestions.sort(key=lambda x: 0 if x.get("priority") == "high" else 1 if x.get("priority") == "medium" else 2)
        
        return suggestions
    
    async def _generate_suggestion(self, need: Dict, user_id: int) -> Optional[Dict]:
        """Generate a suggestion from a predicted need."""
        need_type = need.get("type")
        domain = need.get("domain")
        message = need.get("message")
        priority = need.get("priority", "medium")
        
        suggestions = {
            "guidance": {
                "title": f"📚 Need more guidance in {domain}?",
                "description": message,
                "action": f"Review {domain} intelligence pack",
                "action_url": f"/admin/dashboard/packs/{domain}",
                "icon": "fa-book",
                "priority": priority
            },
            "topic": {
                "title": f"📊 You're showing high interest in {domain}",
                "description": message,
                "action": f"Generate {domain} report",
                "action_url": f"/admin/dashboard/trends/{domain}",
                "icon": "fa-chart-line",
                "priority": priority
            },
            "schedule": {
                "title": "⏰ You prefer morning work",
                "description": "Consider scheduling complex tasks in the morning",
                "action": "View productivity tips",
                "action_url": "/admin/dashboard/settings",
                "icon": "fa-clock",
                "priority": "low"
            }
        }
        
        return suggestions.get(need_type)
    
    async def _generate_risk_suggestion(self, risk: Dict, user_id: int) -> Optional[Dict]:
        """Generate a suggestion from a risk."""
        level = risk.get("level")
        domain = risk.get("domain")
        message = risk.get("message")
        recommendation = risk.get("recommendation")
        
        if level == "high":
            return {
                "title": f"🚨 High risk detected in {domain}",
                "description": f"{message}. {recommendation}",
                "action": f"Investigate {domain} risks",
                "action_url": f"/admin/dashboard/risks/{domain}",
                "icon": "fa-exclamation-triangle",
                "priority": "high"
            }
        elif level == "medium":
            return {
                "title": f"⚠️ Moderate risk in {domain}",
                "description": f"{message}. {recommendation}",
                "action": f"Review {domain} patterns",
                "action_url": f"/admin/dashboard/trends/{domain}",
                "icon": "fa-info-circle",
                "priority": "medium"
            }
        return None
    
    async def _get_quick_actions(self, user_id: int, context: Dict) -> List[Dict]:
        """Get quick actions based on context."""
        actions = []
        
        # If user is in chat, suggest related topics
        if context.get("current_tab") == "chat":
            # Get recent topics
            patterns = await self.self_improving.get_active_patterns()
            topics = [p.get("trigger", "")[:30] for p in patterns[:3]]
            for topic in topics:
                if topic:
                    actions.append({
                        "title": f"💬 Ask about {topic}",
                        "description": f"Quick question about {topic}",
                        "action": f"Ask: Tell me more about {topic}",
                        "action_url": "/chat",
                        "icon": "fa-comment",
                        "priority": "low"
                    })
        
        # If user is in trends, suggest analysis
        if context.get("current_tab") == "trends":
            actions.append({
                "title": "📈 Generate trend analysis",
                "description": "Get AI-powered trend insights",
                "action": "generate_trend_report",
                "action_url": "/admin/dashboard/trends",
                "icon": "fa-chart-line",
                "priority": "low"
            })
        
        return actions
    
    async def get_dashboard_suggestions(self, user_id: int) -> Dict:
        """
        Get suggestions specifically for the dashboard.
        This is the main entry point for the UI.
        """
        suggestions = await self.get_suggestions(user_id, {"current_tab": "dashboard"})
        
        # Categorize suggestions
        high_priority = [s for s in suggestions if s.get("priority") == "high"]
        medium_priority = [s for s in suggestions if s.get("priority") == "medium"]
        low_priority = [s for s in suggestions if s.get("priority") == "low"]
        
        return {
            "suggestions": {
                "high": high_priority[:3],
                "medium": medium_priority[:5],
                "low": low_priority[:5]
            },
            "total": len(suggestions),
            "has_suggestions": len(suggestions) > 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def dismiss_suggestion(self, suggestion_id: str, user_id: int) -> Dict:
        """Dismiss a suggestion for a user."""
        logger.info(f"User {user_id} dismissed suggestion: {suggestion_id}")
        return {"status": "dismissed", "suggestion_id": suggestion_id}
