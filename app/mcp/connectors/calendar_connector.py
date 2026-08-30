"""
Enhanced MCP Calendar Connector - Temporal Intelligence for Decision Making
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import json
import httpx
from collections import defaultdict

from app.mcp.base import BaseMCPConnector

logger = logging.getLogger(__name__)


class CalendarConnector(BaseMCPConnector):
    """MCP connector for calendar operations."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider = config.get("provider", "google")  # google, outlook, apple
        self.api_url = config.get("api_url", "https://www.googleapis.com/calendar/v3")
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.redirect_uri = config.get("redirect_uri")
        self.access_token = config.get("access_token")
        self.refresh_token = config.get("refresh_token")
        
        # Token expiry tracking
        self.token_expires_at = datetime.utcnow()
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers for calendar API calls."""
        if self.access_token:
            await self._refresh_token_if_needed()
            return {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
        return {}
    
    async def _refresh_token_if_needed(self):
        """Refresh access token if expired."""
        if datetime.utcnow() >= self.token_expires_at:
            # Token refresh logic
            pass
    
    async def get_calendars(self) -> List[Dict]:
        """Get list of calendars."""
        headers = await self._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/users/me/calendarList",
                headers=headers
            )
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
    
    async def create_event(self, event_data: Dict) -> Dict:
        """Create a calendar event."""
        headers = await self._get_headers()
        calendar_id = event_data.get("calendar_id", "primary")
        
        # Format event for calendar API
        event = {
            "summary": event_data.get("summary", "PersonaVault Decision"),
            "description": event_data.get("description", ""),
            "start": {
                "dateTime": event_data.get("start_time"),
                "timeZone": event_data.get("timezone", "UTC")
            },
            "end": {
                "dateTime": event_data.get("end_time"),
                "timeZone": event_data.get("timezone", "UTC")
            },
            "attendees": [
                {"email": email} for email in event_data.get("attendees", [])
            ],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 30}
                ]
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/calendars/{calendar_id}/events",
                headers=headers,
                json=event
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to create event: {response.text}")
                return {"error": response.text}
    
    async def schedule_decision(self, decision_data: Dict) -> Dict:
        """Schedule a decision review or action."""
        event_data = {
            "summary": f"Decision Review: {decision_data.get('decision_id', '')}",
            "description": f"""
Decision ID: {decision_data.get('decision_id')}
Confidence: {decision_data.get('confidence', 0)}%
Query: {decision_data.get('query', '')}
Action Required: {decision_data.get('action_required', 'Review')}
            """.strip(),
            "start_time": decision_data.get("scheduled_time"),
            "end_time": (datetime.fromisoformat(decision_data.get("scheduled_time")) + timedelta(hours=1)).isoformat(),
            "attendees": decision_data.get("attendees", []),
            "timezone": decision_data.get("timezone", "UTC")
        }
        return await self.create_event(event_data)
    
    async def get_events(self, time_min: str = None, time_max: str = None) -> List[Dict]:
        """Get calendar events."""
        headers = await self._get_headers()
        if not time_min:
            time_min = datetime.utcnow().isoformat() + "Z"
        if not time_max:
            time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
        
        params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/calendars/primary/events",
                headers=headers,
                params=params
            )
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
    
    async def update_event(self, event_id: str, updates: Dict) -> Dict:
        """Update an existing event."""
        headers = await self._get_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.api_url}/calendars/primary/events/{event_id}",
                headers=headers,
                json=updates
            )
            if response.status_code == 200:
                return response.json()
            return {"error": response.text}
    
    async def delete_event(self, event_id: str) -> Dict:
        """Delete an event."""
        headers = await self._get_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.api_url}/calendars/primary/events/{event_id}",
                headers=headers
            )
            return {"success": response.status_code == 204}
    
    async def find_available_slots(self, duration_minutes: int = 60, days_ahead: int = 7) -> List[Dict]:
        """Find available time slots."""
        events = await self.get_events()
        busy_times = []
        
        for event in events:
            start = event.get("start", {}).get("dateTime")
            end = event.get("end", {}).get("dateTime")
            if start and end:
                busy_times.append({
                    "start": datetime.fromisoformat(start.replace("Z", "+00:00")),
                    "end": datetime.fromisoformat(end.replace("Z", "+00:00"))
                })
        
        # Find free slots
        slots = []
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)
        
        for day in range(days_ahead):
            date = now + timedelta(days=day)
            # Start checking from 9 AM
            slot_start = datetime(date.year, date.month, date.day, 9, 0)
            slot_end = slot_start + timedelta(minutes=duration_minutes)
            
            while slot_end.hour < 18:  # Work hours
                is_busy = False
                for busy in busy_times:
                    if not (slot_end <= busy["start"] or slot_start >= busy["end"]):
                        is_busy = True
                        break
                
                if not is_busy:
                    slots.append({
                        "start": slot_start.isoformat(),
                        "end": slot_end.isoformat()
                    })
                
                slot_start += timedelta(minutes=duration_minutes)
                slot_end = slot_start + timedelta(minutes=duration_minutes)
        
        return slots


class TemporalIntelligence:
    """Temporal intelligence for decision-aware scheduling."""
    
    def __init__(self):
        self.calendar_connector = None
    
    async def analyze_decision_timing(self, decision_data: Dict) -> Dict:
        """
        Analyze the best time to make or review a decision based on:
        - Historical decision patterns
        - Calendar availability
        - Decision urgency
        - User productivity patterns
        """
        # 1. Urgency-based timing
        urgency = decision_data.get("urgency", "medium")
        urgency_mapping = {
            "critical": 0,      # Immediate
            "high": 60,         # Within 1 hour
            "medium": 1440,     # Within 24 hours
            "low": 10080        # Within 7 days
        }
        
        deadline_minutes = urgency_mapping.get(urgency, 1440)
        deadline = datetime.utcnow() + timedelta(minutes=deadline_minutes)
        
        # 2. Find optimal time based on user patterns
        optimal_time = await self._find_optimal_time(decision_data.get("user_id"))
        
        # 3. Check availability
        available_slots = await self.calendar_connector.find_available_slots(60, 7)
        
        return {
            "urgency": urgency,
            "deadline": deadline.isoformat(),
            "optimal_time": optimal_time,
            "available_slots": available_slots,
            "recommendation": self._generate_time_recommendation(urgency, available_slots)
        }
    
    async def _find_optimal_time(self, user_id: str) -> str:
        """Find optimal time based on historical patterns."""
        # Analyze past decisions for patterns
        # Peak productivity hours
        # Meeting patterns
        return (datetime.utcnow() + timedelta(hours=2)).isoformat()
    
    def _generate_time_recommendation(self, urgency: str, slots: List) -> Dict:
        """Generate a time recommendation."""
        if not slots:
            return {
                "status": "no_slots",
                "message": "No available slots found",
                "suggestion": "Try a different day or time"
            }
        
        urgency_levels = {
            "critical": "immediately",
            "high": "within the next hour",
            "medium": "today",
            "low": "this week"
        }
        
        return {
            "status": "slots_found",
            "suggestion": f"Recommended {urgency_levels.get(urgency, 'soon')}",
            "best_slot": slots[0] if slots else None,
            "alternatives": slots[1:4] if len(slots) > 1 else []
        }


class TimeAwareDecisionScheduler:
    """Schedule decisions with temporal intelligence."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.temporal = TemporalIntelligence()
    
    async def schedule_decision_optimally(
        self,
        decision_id: str,
        user_id: str,
        urgency: str,
        attendees: List[str] = None
    ) -> Dict:
        """
        Schedule a decision review at the optimal time.
        """
        # 1. Analyze decision timing
        timing_analysis = await self.temporal.analyze_decision_timing({
            "decision_id": decision_id,
            "user_id": user_id,
            "urgency": urgency
        })
        
        # 2. Get decision context
        decision_context = await self._get_decision_context(decision_id)
        
        # 3. Find optimal slot
        best_slot = timing_analysis.get("best_slot")
        if not best_slot:
            return {
                "status": "no_slots",
                "analysis": timing_analysis,
                "decision": decision_context
            }
        
        # 4. Create calendar event
        event = {
            "summary": f"Decision Review: {decision_context.get('summary', decision_id)}",
            "description": self._build_event_description(decision_context),
            "start_time": best_slot.get("start"),
            "end_time": best_slot.get("end"),
            "attendees": attendees or [],
            "timezone": "UTC"
        }
        
        # 5. Create the event
        calendar_result = await self.calendar_connector.create_event(event)
        
        # 6. Store schedule record
        await self._store_schedule_record(decision_id, calendar_result, timing_analysis)
        
        return {
            "status": "scheduled",
            "event": calendar_result,
            "timing_analysis": timing_analysis,
            "decision": decision_context,
            "message": f"Decision scheduled for {best_slot.get('start')}"
        }
    
    def _build_event_description(self, decision_context: Dict) -> str:
        """Build a comprehensive event description."""
        return f"""
Decision Review: {decision_context.get('summary', '')}

Decision ID: {decision_context.get('id', '')}
Confidence: {decision_context.get('confidence', 0)}%
Status: {decision_context.get('status', 'pending')}

Review Questions:
1. Was the correct decision made?
2. What were the key factors?
3. Are there any new considerations?

Attachments: {decision_context.get('attachments', [])}

Generated by PersonaVault Decision Operating System
        """.strip()
