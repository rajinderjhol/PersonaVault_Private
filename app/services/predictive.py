"""
Predictive Intelligence Service
Anticipates needs, identifies risks, and proposes actions.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import BehaviourEvent, EpisodicEntry
from app.services.self_improving import SelfImprovingIntelligence

logger = logging.getLogger(__name__)

class PredictiveIntelligence:
    """
    Predicts future needs and risks based on historical patterns.
    This is the core of Phase 3.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.self_improving = SelfImprovingIntelligence(db)
    
    async def calculate_drift_score(self, domain: str = None) -> Dict:
        """
        Calculate a "Drift Score" - how much current behavior deviates
        from established patterns.
        """
        # 1. Get recent events
        cutoff = datetime.utcnow() - timedelta(days=30)
        stmt = select(BehaviourEvent).where(
            BehaviourEvent.timestamp >= cutoff
        )
        if domain:
            stmt = stmt.where(BehaviourEvent.domain == domain)
        result = await self.db.execute(stmt)
        recent_events = result.scalars().all()
        
        if not recent_events:
            return {"score": 0, "status": "insufficient_data", "domain": domain}
        
        # 2. Get established patterns
        patterns = await self.self_improving.get_active_patterns()
        
        # 3. Calculate drift
        deviations = []
        for event in recent_events:
            matched = False
            for pattern in patterns:
                trigger = pattern.get("trigger", "").lower()
                # Ensure event.reason is not None
                reason = event.reason or ""
                if trigger and trigger in reason.lower():
                    matched = True
                    # Check if confidence is below pattern threshold
                    if event.confidence < pattern.get("weight", 0.7):
                        deviations.append({
                            "event_id": event.id,
                            "reason": reason,
                            "expected": pattern.get("weight", 0.7),
                            "actual": event.confidence,
                            "pattern_type": pattern.get("type", "unknown")
                        })
                    break
            if not matched:
                deviations.append({
                    "event_id": event.id,
                    "reason": reason,
                    "expected": 0.7,
                    "actual": event.confidence,
                    "pattern_type": "unseen"
                })
        
        total_events = len(recent_events)
        deviation_count = len(deviations)
        drift_score = (deviation_count / total_events) if total_events > 0 else 0
        
        if drift_score < 0.2:
            status = "low"
        elif drift_score < 0.5:
            status = "medium"
        else:
            status = "high"
        
        return {
            "score": drift_score,
            "status": status,
            "domain": domain or "all",
            "total_events": total_events,
            "deviations": deviation_count,
            "sample_deviations": deviations[:5],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def identify_emerging_risks(self) -> List[Dict]:
        """
        Identify emerging risks based on recent patterns.
        """
        risks = []
        domains = ["security", "compliance", "contract", "procurement"]
        for domain in domains:
            drift = await self.calculate_drift_score(domain)
            if drift["status"] == "high":
                risks.append({
                    "domain": domain,
                    "level": "high",
                    "message": f"High drift detected in {domain} domain",
                    "score": drift["score"],
                    "recommendation": f"Review recent {domain} decisions for alignment"
                })
            elif drift["status"] == "medium":
                risks.append({
                    "domain": domain,
                    "level": "medium",
                    "message": f"Moderate drift detected in {domain} domain",
                    "score": drift["score"],
                    "recommendation": f"Monitor {domain} decisions more closely"
                })
        
        patterns = await self.self_improving.get_active_patterns()
        for pattern in patterns:
            if pattern.get("weight", 1.0) < 0.5 and pattern.get("type") != "failure":
                risks.append({
                    "domain": "learning",
                    "level": "medium",
                    "message": f"Pattern '{pattern.get('trigger', '')[:50]}' is decaying",
                    "score": pattern.get("weight", 0),
                    "recommendation": "Reinforce this pattern or investigate why"
                })
        
        return risks
    
    # ============ USER BEHAVIOR ANALYSIS ============
    
    async def analyze_user_behavior(self, user_id: int) -> Dict:
        """
        Analyze a specific user's behavior patterns.
        """
        # 1. Get user's historical data
        user_data = await self._get_user_history(user_id)
        
        if not user_data:
            return {"user_id": user_id, "status": "no_data"}
        
        # 2. Analyze patterns
        patterns = await self._extract_user_patterns(user_data)
        
        # 3. Identify needs
        needs = await self._identify_user_needs(user_data, patterns)
        
        # 4. Build profile
        return {
            "user_id": user_id,
            "behavior": patterns,
            "predicted_needs": needs,
            "confidence": self._calculate_confidence(patterns),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_user_history(self, user_id: int, days: int = 90) -> Dict:
        """Get user's historical interactions."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get decisions
        stmt = select(BehaviourEvent).where(
            and_(
                BehaviourEvent.user_id == user_id,
                BehaviourEvent.timestamp >= cutoff
            )
        ).order_by(BehaviourEvent.timestamp)
        result = await self.db.execute(stmt)
        decisions = result.scalars().all()
        
        # Get chat history
        chat_stmt = select(EpisodicEntry).where(
            and_(
                EpisodicEntry.user_id == user_id,
                EpisodicEntry.timestamp >= cutoff
            )
        ).order_by(EpisodicEntry.timestamp)
        chat_result = await self.db.execute(chat_stmt)
        chats = chat_result.scalars().all()
        
        return {
            "decisions": [
                {
                    "domain": d.domain,
                    "event_type": d.event_type,
                    "decision": d.decision,
                    "confidence": d.confidence,
                    "timestamp": d.timestamp
                }
                for d in decisions
            ],
            "chats": [
                {
                    "query": c.query,
                    "response": c.answer,
                    "timestamp": c.timestamp
                }
                for c in chats
            ]
        }
    
    async def _extract_user_patterns(self, user_data: Dict) -> Dict:
        """Extract behavioral patterns from user data."""
        decisions = user_data.get("decisions", [])
        chats = user_data.get("chats", [])
        
        # Domain preferences
        domains = {}
        for d in decisions:
            domain = d.get("domain", "unknown")
            if domain not in domains:
                domains[domain] = {"count": 0, "confidences": []}
            domains[domain]["count"] += 1
            domains[domain]["confidences"].append(d.get("confidence", 0.5))
        
        # Time patterns
        time_patterns = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
        for d in decisions:
            hour = d.get("timestamp", datetime.utcnow()).hour
            if 6 <= hour < 12:
                time_patterns["morning"] += 1
            elif 12 <= hour < 17:
                time_patterns["afternoon"] += 1
            elif 17 <= hour < 21:
                time_patterns["evening"] += 1
            else:
                time_patterns["night"] += 1
        
        # Query patterns
        query_topics = {}
        for c in chats:
            query = c.get("query", "").lower()
            topics = ["security", "compliance", "contract", "procurement", "risk"]
            for topic in topics:
                if topic in query:
                    if topic not in query_topics:
                        query_topics[topic] = 0
                    query_topics[topic] += 1
        
        return {
            "domains": domains,
            "time_patterns": time_patterns,
            "query_topics": query_topics,
            "total_decisions": len(decisions),
            "total_chats": len(chats)
        }
    
    async def _identify_user_needs(self, user_data: Dict, patterns: Dict) -> List[Dict]:
        """Identify predicted needs based on behavior."""
        needs = []
        
        # Check if user needs more guidance in low-confidence domains
        for domain, data in patterns.get("domains", {}).items():
            avg_conf = sum(data["confidences"]) / len(data["confidences"]) if data["confidences"] else 0
            if avg_conf < 0.7 and data["count"] > 3:
                needs.append({
                    "type": "guidance",
                    "domain": domain,
                    "message": f"Consider more training in {domain} domain",
                    "priority": "high" if avg_conf < 0.5 else "medium"
                })
        
        # Check if user has emerging topics
        query_topics = patterns.get("query_topics", {})
        for topic, count in query_topics.items():
            if count > 5:
                needs.append({
                    "type": "topic",
                    "domain": topic,
                    "message": f"High interest in {topic} topics",
                    "priority": "medium"
                })
        
        # Time-based needs
        time_patterns = patterns.get("time_patterns", {})
        if time_patterns.get("morning", 0) > time_patterns.get("afternoon", 0) * 2:
            needs.append({
                "type": "schedule",
                "domain": "general",
                "message": "User prefers morning work hours",
                "priority": "low"
            })
        
        return needs
    
    def _calculate_confidence(self, patterns: Dict) -> float:
        """Calculate confidence in the analysis."""
        # Based on amount of data
        total = patterns.get("total_decisions", 0) + patterns.get("total_chats", 0)
        if total > 50:
            return 0.9
        elif total > 20:
            return 0.7
        elif total > 10:
            return 0.5
        else:
            return 0.3
    
    async def get_user_predictions(self, user_id: int) -> Dict:
        """
        Get comprehensive predictions for a user.
        """
        # Analyze behavior
        behavior = await self.analyze_user_behavior(user_id)
        
        # Get drift for this user
        drift = await self.calculate_drift_score()
        
        # Get general risks
        risks = await self.identify_emerging_risks()
        
        # Combine
        return {
            "user_id": user_id,
            "behavior_summary": behavior.get("behavior", {}),
            "predicted_needs": behavior.get("predicted_needs", []),
            "confidence": behavior.get("confidence", 0),
            "drift_context": drift,
            "relevant_risks": [r for r in risks if r.get("domain") in behavior.get("behavior", {}).get("domains", {})]
        }
    
    async def get_team_analysis(self, user_ids: List[int]) -> Dict:
        """
        Analyze a team's behavior patterns.
        """
        team_behavior = {
            "domains": {},
            "time_patterns": {"morning": 0, "afternoon": 0, "evening": 0, "night": 0},
            "total_members": len(user_ids),
            "member_profiles": []
        }
        
        for user_id in user_ids:
            profile = await self.analyze_user_behavior(user_id)
            team_behavior["member_profiles"].append(profile)
            
            # Aggregate domains
            for domain, data in profile.get("behavior", {}).get("domains", {}).items():
                if domain not in team_behavior["domains"]:
                    team_behavior["domains"][domain] = {"count": 0, "total_confidence": 0}
                team_behavior["domains"][domain]["count"] += data["count"]
                team_behavior["domains"][domain]["total_confidence"] += sum(data.get("confidences", [0]))
        
        return team_behavior
