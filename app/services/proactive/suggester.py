"""
Proactive Suggestion Service - Generates proactive suggestions based on user context
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from app.services.memory.ice_repository import IceMemoryRepository
from app.services.episodic_memory import EpisodicMemory
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


@dataclass
class Suggestion:
    """A proactive suggestion."""
    id: str
    type: str  # memory, time, action, context
    confidence: float
    title: str
    description: str
    action: Dict[str, Any]  # What action to take
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProactiveSuggester:
    """
    Proactive suggestion engine - suggests actions based on context.
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory or SessionLocal
        self.ice_repo = IceMemoryRepository(session_factory)
        self.episodic_repo = EpisodicMemory(session_factory)
        self.suggestion_threshold = 0.5
        self.max_suggestions = 5
    
    async def get_suggestions(
        self,
        user_id: int,
        context: Optional[Dict[str, Any]] = None,
        query: Optional[str] = None
    ) -> List[Suggestion]:
        """
        Generate proactive suggestions based on user context.
        """
        context = context or {}
        suggestions = []
        
        # 1. Memory-based suggestions
        memory_suggestions = await self._suggest_from_memory(user_id, query)
        suggestions.extend(memory_suggestions)
        
        # 2. Time-based suggestions
        time_suggestions = await self._suggest_from_time(user_id)
        suggestions.extend(time_suggestions)
        
        # 3. Context-based suggestions
        context_suggestions = await self._suggest_from_context(user_id, context, query)
        suggestions.extend(context_suggestions)
        
        # 4. Pattern-based suggestions
        pattern_suggestions = await self._suggest_from_patterns(user_id, query)
        suggestions.extend(pattern_suggestions)
        
        # Filter and sort by confidence
        suggestions = [s for s in suggestions if s.confidence > self.suggestion_threshold]
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        return suggestions[:self.max_suggestions]
    
    async def _suggest_from_memory(
        self,
        user_id: int,
        query: Optional[str] = None
    ) -> List[Suggestion]:
        """Generate suggestions from memory patterns."""
        suggestions = []
        
        try:
            # Get recent patterns
            patterns = await self.ice_repo.get_recent_patterns(user_id, limit=10)
            
            if not patterns:
                # New user - suggest onboarding
                suggestions.append(Suggestion(
                    id=f"sug_onboard_{user_id}",
                    type="memory",
                    confidence=0.9,
                    title="Welcome to PersonaVault",
                    description="I'm your personal intelligence assistant. Let me help you get started.",
                    action={
                        "type": "onboarding",
                        "steps": [
                            "Tell me about yourself",
                            "Upload some documents",
                            "Connect your calendar"
                        ]
                    },
                    metadata={"user_id": user_id}
                ))
                return suggestions
            
            # Check for patterns that need following up
            for pattern in patterns[:5]:
                pattern_meta = pattern.get("metadata", {})
                last_used = pattern_meta.get("last_used")
                
                if last_used:
                    days_since = (datetime.now() - datetime.fromisoformat(last_used)).days
                    if days_since > 7 and pattern.get("confidence", 0) > 0.7:
                        suggestions.append(Suggestion(
                            id=f"sug_revisit_{pattern.get('id')}",
                            type="memory",
                            confidence=0.7,
                            title=f"Revisit: {pattern.get('trigger', '')[:50]}...",
                            description=f"You haven't revisited this pattern in {days_since} days.",
                            action={
                                "type": "revisit_pattern",
                                "pattern_id": pattern.get("id")
                            },
                            metadata={"pattern": pattern}
                        ))
            
            # Check for follow-up opportunities
            if query:
                related = await self.ice_repo.search_similar(query, user_id=user_id, limit=3)
                if related:
                    suggestions.append(Suggestion(
                        id=f"sug_related_{user_id}",
                        type="memory",
                        confidence=0.65,
                        title=f"I found related patterns: {len(related)}",
                        description=f"These patterns might help with: {query[:50]}...",
                        action={
                            "type": "show_related",
                            "patterns": [p.get("id") for p in related]
                        },
                        metadata={"related": related}
                    ))
                    
        except Exception as e:
            logger.error(f"Memory-based suggestions failed: {e}")
        
        return suggestions
    
    async def _suggest_from_time(self, user_id: int) -> List[Suggestion]:
        """Generate suggestions based on time."""
        suggestions = []
        now = datetime.now()
        
        try:
            # Get upcoming events from context
            events = await self._get_upcoming_events(user_id, days=3)
            if events:
                suggestions.append(Suggestion(
                    id=f"sug_events_{user_id}",
                    type="time",
                    confidence=0.8,
                    title=f"{len(events)} Upcoming Events",
                    description=f"Your next event: {events[0].get('summary', 'Unknown')}",
                    action={
                        "type": "show_events",
                        "events": events
                    },
                    metadata={"events": events}
                ))
            
            # Check for overdue tasks
            tasks = await self._get_overdue_tasks(user_id)
            if tasks:
                suggestions.append(Suggestion(
                    id=f"sug_tasks_{user_id}",
                    type="time",
                    confidence=0.85,
                    title=f"{len(tasks)} Overdue Tasks",
                    description="You have tasks that need attention.",
                    action={
                        "type": "show_tasks",
                        "tasks": tasks
                    },
                    metadata={"tasks": tasks}
                ))
                    
        except Exception as e:
            logger.error(f"Time-based suggestions failed: {e}")
        
        return suggestions
    
    async def _suggest_from_context(
        self,
        user_id: int,
        context: Dict[str, Any],
        query: Optional[str] = None
    ) -> List[Suggestion]:
        """Generate suggestions from current context."""
        suggestions = []
        
        try:
            # Check if we need to save something to memory
            if query and len(query) > 100:
                suggestions.append(Suggestion(
                    id=f"sug_save_{user_id}",
                    type="context",
                    confidence=0.6,
                    title="Save to Memory",
                    description="Would you like to save this conversation to memory?",
                    action={
                        "type": "save_to_memory",
                        "content": query
                    },
                    metadata={"query": query}
                ))
            
            # Check for action opportunities
            action_intents = await self._detect_action_intent(query or "", context)
            for intent in action_intents:
                suggestions.append(Suggestion(
                    id=f"sug_action_{intent.get('id')}",
                    type="context",
                    confidence=intent.get("confidence", 0.5),
                    title=intent.get("title", "I can help with that"),
                    description=intent.get("description", ""),
                    action=intent.get("action", {}),
                    metadata={"intent": intent}
                ))
                
        except Exception as e:
            logger.error(f"Context-based suggestions failed: {e}")
        
        return suggestions
    
    async def _suggest_from_patterns(
        self,
        user_id: int,
        query: Optional[str] = None
    ) -> List[Suggestion]:
        """Generate suggestions from detected patterns."""
        suggestions = []
        
        try:
            workflows = await self._detect_workflows(user_id)
            
            for workflow in workflows[:3]:
                if workflow.get("ready_to_execute"):
                    suggestions.append(Suggestion(
                        id=f"sug_workflow_{workflow.get('id')}",
                        type="memory",
                        confidence=0.75,
                        title=f"Ready to execute: {workflow.get('name')}",
                        description=workflow.get("description", ""),
                        action={
                            "type": "execute_workflow",
                            "workflow_id": workflow.get("id")
                        },
                        metadata={"workflow": workflow}
                    ))
                    
        except Exception as e:
            logger.error(f"Pattern-based suggestions failed: {e}")
        
        return suggestions
    
    # Helper methods
    async def _get_upcoming_events(self, user_id: int, days: int = 3) -> List[Dict]:
        """Get upcoming events from integrations."""
        return []
    
    async def _get_overdue_tasks(self, user_id: int) -> List[Dict]:
        """Get overdue tasks."""
        return []
    
    async def _detect_recurring_patterns(self, user_id: int) -> List[Dict]:
        """Detect recurring patterns."""
        return []
    
    async def _detect_action_intent(self, query: str, context: Dict) -> List[Dict]:
        """Detect action intents in query."""
        intents = []
        
        # Simple keyword-based detection
        if "schedule" in query.lower() or "calendar" in query.lower():
            intents.append({
                "id": "schedule",
                "confidence": 0.8,
                "title": "I can schedule that for you",
                "description": "Would you like me to add this to your calendar?",
                "action": {
                    "type": "schedule",
                    "details": query
                }
            })
        
        if "remind" in query.lower():
            intents.append({
                "id": "reminder",
                "confidence": 0.85,
                "title": "I'll remember that",
                "description": "I'll remind you about this later.",
                "action": {
                    "type": "set_reminder",
                    "details": query
                }
            })
        
        return intents
    
    async def _detect_workflows(self, user_id: int) -> List[Dict]:
        """Detect user workflows."""
        return []
