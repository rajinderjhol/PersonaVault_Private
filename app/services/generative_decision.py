"""
Generative Decision Making Service
Generates and evaluates multiple decision paths.
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.self_improving import SelfImprovingIntelligence
from app.services.predictive import PredictiveIntelligence
from app.services.trace_service import TraceService
from app.models.decision_trace import TraceStep

logger = logging.getLogger(__name__)

class GenerativeDecisionMaker:
    """
    Generates multiple decision options, simulates outcomes,
    analyzes tradeoffs, and ranks recommendations.
    """
    
    def __init__(self, db: AsyncSession, trace_service: Optional[TraceService] = None):
        self.db = db
        self.self_improving = SelfImprovingIntelligence(db)
        self.predictive = PredictiveIntelligence(db)
        self.trace_service = trace_service
    
    async def generate_options(self, problem: str, context: Dict) -> List[Dict]:
        """
        Generate multiple decision options.
        """
        options = []
        
        # 1. Get relevant patterns
        patterns = await self.self_improving.get_active_patterns()
        
        # 2. Generate options based on patterns
        for pattern in patterns[:5]:  # Top 5 patterns
            if pattern.get("type") == "success" and pattern.get("weight", 0) > 0.7:
                options.append({
                    "id": f"opt_{len(options)+1}",
                    "name": f"Apply pattern: {pattern.get('trigger', 'Unknown')[:50]}",
                    "description": pattern.get("correction", ""),
                    "source": "pattern",
                    "pattern_id": pattern.get("id"),
                    "confidence": pattern.get("confidence", 0.5)
                })
        
        # 3. Add default options
        if "security" in problem.lower():
            options.append({
                "id": "opt_default",
                "name": "Escalate to security team",
                "description": "Send to human review for security incident",
                "source": "default",
                "confidence": 0.85
            })
            options.append({
                "id": "opt_auto",
                "name": "Auto-block and log",
                "description": "Automatically block and log for review",
                "source": "default",
                "confidence": 0.75
            })
        elif "compliance" in problem.lower():
            options.append({
                "id": "opt_default",
                "name": "Review against regulations",
                "description": "Check against compliance requirements",
                "source": "default",
                "confidence": 0.80
            })
        
        return options
    
    async def simulate_outcomes(self, options: List[Dict], context: Dict) -> List[Dict]:
        """
        Simulate outcomes for each option.
        """
        simulated = []
        
        for option in options:
            # Simulate based on context and patterns
            base_confidence = option.get("confidence", 0.5)
            drift = await self.predictive.calculate_drift_score()
            
            # Adjust confidence based on drift
            if drift.get("status") == "high":
                adjusted_confidence = base_confidence * 0.8
                risk_level = "high"
            elif drift.get("status") == "medium":
                adjusted_confidence = base_confidence * 0.9
                risk_level = "medium"
            else:
                adjusted_confidence = base_confidence
                risk_level = "low"
            
            # Predict success probability
            patterns = await self.self_improving.get_active_patterns()
            similar_patterns = [p for p in patterns if option.get("description", "") and p.get("trigger") in option.get("description", "")]
            
            if similar_patterns:
                avg_success = sum(p.get("confidence", 0.5) for p in similar_patterns) / len(similar_patterns)
                success_prob = (adjusted_confidence + avg_success) / 2
            else:
                success_prob = adjusted_confidence
            
            simulated.append({
                **option,
                "simulation": {
                    "success_probability": min(success_prob, 1.0),
                    "risk_level": risk_level,
                    "confidence": adjusted_confidence,
                    "expected_impact": self._calculate_impact(option, context),
                    "similar_patterns": len(similar_patterns)
                }
            })
        
        return simulated
    
    def _calculate_impact(self, option: Dict, context: Dict) -> Dict:
        """Calculate expected impact of an option."""
        return {
            "risk_reduction": min(option.get("confidence", 0.5) * 0.3, 0.9),
            "efficiency_gain": min(option.get("confidence", 0.5) * 0.2, 0.8),
            "cost_saving": min(option.get("confidence", 0.5) * 0.1, 0.7)
        }
    
    async def analyze_tradeoffs(self, options: List[Dict]) -> Dict:
        """
        Analyze tradeoffs between options.
        """
        tradeoffs = {
            "recommended": None,
            "alternatives": [],
            "comparison": {}
        }
        
        best_score = 0
        for option in options:
            sim = option.get("simulation", {})
            score = (
                sim.get("success_probability", 0) * 0.5 +
                (1 - self._risk_score(sim.get("risk_level", "low"))) * 0.3 +
                sim.get("confidence", 0) * 0.2
            )
            
            if score > best_score:
                best_score = score
                tradeoffs["recommended"] = option
        
        tradeoffs["alternatives"] = [o for o in options if o != tradeoffs["recommended"]]
        
        return tradeoffs
    
    def _risk_score(self, risk_level: str) -> float:
        """Convert risk level to numeric score."""
        return {"low": 0.2, "medium": 0.5, "high": 0.8}.get(risk_level, 0.5)
    
    async def get_recommendation(self, problem: str, context: Dict, session_id: Optional[int] = None) -> Dict:
        """
        Main entry point for generative decision making.
        """
        # 1. Generate options
        options = await self.generate_options(problem, context)
        
        # 2. Simulate outcomes
        simulated = await self.simulate_outcomes(options, context)
        
        # 3. Analyze tradeoffs
        tradeoffs = await self.analyze_tradeoffs(simulated)
        
        recommendation = tradeoffs["recommended"]
        confidence = recommendation.get("confidence", 0.5)
        
        # --- TRACE CAPTURE: AI RECOMMENDATION ---
        trace_id = None
        if self.trace_service and session_id:
            trace = await self.trace_service.capture_step(
                session_id=session_id,
                step=TraceStep.AI_RECOMMENDATION,
                data={
                    "problem": problem,
                    "options_count": len(options),
                    "recommendation": {
                        "id": recommendation.get("id"),
                        "name": recommendation.get("name"),
                        "confidence": confidence
                    },
                    "alternatives": [
                        {
                            "id": alt.get("id"),
                            "name": alt.get("name"),
                            "confidence": alt.get("confidence", 0.5)
                        }
                        for alt in tradeoffs.get("alternatives", [])[:3]
                    ],
                    "tradeoffs": {
                        "risk_level": recommendation.get("simulation", {}).get("risk_level"),
                        "success_probability": recommendation.get("simulation", {}).get("success_probability")
                    }
                },
                agent_id="GenerativeDecisionMaker",
                confidence_score=confidence
            )
            trace_id = str(trace.id) if trace else None
            
            # Add provenance for the recommendation
            if trace and recommendation:
                await self.trace_service.add_provenance(
                    trace_id=trace.id,
                    source_type="generative_decision",
                    source_id=recommendation.get("id", "recommendation"),
                    source_text=recommendation.get("description", ""),
                    relevance_score=confidence
                )
        # --- END TRACE CAPTURE ---
        
        return {
            "problem": problem,
            "options": simulated,
            "recommendation": recommendation,
            "alternatives": tradeoffs["alternatives"],
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": trace_id
        }
