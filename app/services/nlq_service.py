"""
Natural Language Query Service - Query decisions and intelligence in plain English
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from datetime import datetime, timedelta
import logging

from app.models.decision_trace import DecisionTrace
from app.models.user import User

logger = logging.getLogger(__name__)


class NLQService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def query(self, query: str, user: User, context: Dict = None) -> Dict[str, Any]:
        """Execute a natural language query over intelligence data."""
        # Parse the natural language query
        parsed = await self._parse_query(query, context)
        
        # Execute search
        results = await self._search(parsed, user)
        
        # Generate response
        response = await self._generate_response(query, results, parsed)
        
        return {
            "query": query,
            "parsed": parsed,
            "results": results,
            "response": response,
            "confidence": parsed.get("confidence", 0.85),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _parse_query(self, query: str, context: Dict = None) -> Dict[str, Any]:
        """Parse natural language query into structured filters."""
        parsed = {
            "intent": self._detect_intent(query),
            "filters": {},
            "sort": "relevance",
            "limit": 10
        }
        
        # Detect time range
        if "last week" in query.lower():
            parsed["filters"]["time_range"] = "week"
        elif "last month" in query.lower():
            parsed["filters"]["time_range"] = "month"
        elif "today" in query.lower():
            parsed["filters"]["time_range"] = "day"
        
        # Detect domain filters
        domains = ["security", "compliance", "contract", "procurement", "robotics", "clinical"]
        for domain in domains:
            if domain in query.lower():
                parsed["filters"]["domain"] = domain
        
        # Detect step filters
        steps = ["perception", "policy_match", "ai_recommendation", "action", "outcome"]
        for step in steps:
            if step in query.lower():
                parsed["filters"]["step"] = step
        
        # Detect confidence threshold
        if "high confidence" in query.lower():
            parsed["filters"]["min_confidence"] = 0.8
        elif "low confidence" in query.lower():
            parsed["filters"]["max_confidence"] = 0.5
        
        return parsed

    def _detect_intent(self, query: str) -> str:
        """Detect the intent of the query."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["show", "find", "list", "get"]):
            return "list"
        elif any(word in query_lower for word in ["why", "explain", "reason"]):
            return "explain"
        elif any(word in query_lower for word in ["summary", "overview", "report"]):
            return "summary"
        elif any(word in query_lower for word in ["pattern", "trend", "emerging"]):
            return "analyze"
        else:
            return "search"

    async def _search(self, parsed: Dict, user: User) -> List[Dict]:
        """Execute search based on parsed query."""
        # Build base query
        stmt = select(DecisionTrace).where(DecisionTrace.user_id == user.id)
        
        # Apply filters
        if "time_range" in parsed.get("filters", {}):
            time_range = parsed["filters"]["time_range"]
            if time_range == "day":
                stmt = stmt.where(DecisionTrace.timestamp >= datetime.utcnow() - timedelta(days=1))
            elif time_range == "week":
                stmt = stmt.where(DecisionTrace.timestamp >= datetime.utcnow() - timedelta(days=7))
            elif time_range == "month":
                stmt = stmt.where(DecisionTrace.timestamp >= datetime.utcnow() - timedelta(days=30))
        
        # Apply domain filter (search in multiple fields)
        if "domain" in parsed.get("filters", {}):
            domain = parsed["filters"]["domain"]
            # Logging to debug filter
            logger.debug(f"Applying domain filter: {domain}")
            stmt = stmt.where(
                or_(
                    DecisionTrace.pack_name.ilike(f"%{domain}%"),
                    DecisionTrace.data.contains({"domain": domain}),
                    DecisionTrace.query.ilike(f"%{domain}%"),
                    DecisionTrace.response.ilike(f"%{domain}%")
                )
            )
        
        # Apply step filter
        if "step" in parsed.get("filters", {}):
            step = parsed["filters"]["step"]
            stmt = stmt.where(DecisionTrace.step == step)
        
        # Apply confidence filters
        if "min_confidence" in parsed.get("filters", {}):
            stmt = stmt.where(DecisionTrace.confidence_score >= parsed["filters"]["min_confidence"])
        if "max_confidence" in parsed.get("filters", {}):
            stmt = stmt.where(DecisionTrace.confidence_score <= parsed["filters"]["max_confidence"])
        
        # Order by timestamp
        stmt = stmt.order_by(desc(DecisionTrace.timestamp))
        stmt = stmt.limit(parsed.get("limit", 10))
        
        # Execute
        result = await self.db.execute(stmt)
        traces = result.scalars().all()
        
        # Debugging
        logger.debug(f"Search executed. Found {len(traces)} traces.")
        
        return [self._format_trace(t) for t in traces]

    def _format_trace(self, trace: DecisionTrace) -> Dict:
        """Format a trace for display."""
        return {
            "id": str(trace.id),
            "step": trace.step.value if hasattr(trace.step, 'value') else str(trace.step),
            "timestamp": trace.timestamp.isoformat(),
            "confidence": trace.confidence_score,
            "data": trace.data,
            "query": trace.query,
            "response": trace.response,
            "is_crystallized": trace.is_crystallized,
            "pack_name": trace.pack_name
        }

    async def _generate_response(self, query: str, results: List[Dict], parsed: Dict) -> Dict:
        """Generate a natural language response."""
        if not results:
            return {
                "text": "No decisions found matching your query.",
                "suggestion": "Try adjusting your filters or using different keywords."
            }
        
        # Detect intent and generate appropriate response
        intent = parsed.get("intent", "search")
        
        if intent == "list":
            return {
                "text": f"Found {len(results)} matching decisions.",
                "items": results[:5],
                "total": len(results)
            }
        elif intent == "summary":
            avg_conf = sum(r.get("confidence", 0) for r in results) / len(results) if results else 0
            return {
                "text": f"Here's a summary of {len(results)} decisions.",
                "summary": {
                    "count": len(results),
                    "average_confidence": round(avg_conf * 100, 1),
                    "steps": list(set(r.get("step") for r in results)),
                    "crystallized": sum(1 for r in results if r.get("is_crystallized"))
                }
            }
        elif intent == "analyze":
            return {
                "text": f"Analyzing patterns in {len(results)} decisions...",
                "patterns": [
                    {"name": "High confidence decisions", "count": sum(1 for r in results if r.get("confidence", 0) > 0.8)},
                    {"name": "Crystallized patterns", "count": sum(1 for r in results if r.get("is_crystallized"))}
                ]
            }
        else:
            return {
                "text": f"Here are the results for your query.",
                "items": results[:3]
            }
