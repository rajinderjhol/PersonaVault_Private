"""
MCP Calendar Connector - Schedule decisions, reminders, and events
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import json
import httpx

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
