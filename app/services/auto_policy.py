"""
Auto-Policy Updates Service
Automatically adjusts swarm agent behaviors based on learned patterns.
"""
import logging
import json
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import SemanticPattern, SystemConfig
from app.services.self_improving import SelfImprovingIntelligence
from app.services.trace_service import TraceService
from app.models.decision_trace import TraceStep
from datetime import datetime

logger = logging.getLogger(__name__)

class AutoPolicyUpdater:
    """
    Automatically updates policies based on validated patterns.
    The system evolves its own behavior.
    """
    
    def __init__(self, db: AsyncSession, trace_service: Optional[TraceService] = None):
        self.db = db
        self.self_improving = SelfImprovingIntelligence(db)
        self.trace_service = trace_service
    
    async def update_policies(self, session_id: Optional[int] = None):
        """
        Main entry point for auto-policy updates.
        """
        logger.info("🔄 Running auto-policy update...")
        
        # 1. Get all active patterns
        patterns = await self.self_improving.get_active_patterns()
        
        # 2. Group patterns by type
        grouped = self._group_patterns(patterns)
        
        # 3. Generate policy updates
        updates = await self._generate_policy_updates(grouped)
        
        # --- TRACE CAPTURE: POLICY MATCH ---
        trace_id = None
        if self.trace_service and session_id and updates:
            trace = await self.trace_service.capture_step(
                session_id=session_id,
                step=TraceStep.POLICY_MATCH,
                data={
                    "patterns_analyzed": len(patterns),
                    "updates_generated": len(updates),
                    "grouped_patterns": {
                        k: len(v) for k, v in grouped.items()
                    },
                    "updates": updates[:5]  # Top 5 updates
                },
                agent_id="AutoPolicyUpdater",
                confidence_score=0.8,
                query="Auto-policy update analysis",
                pack_name="policy"
            )
            trace_id = str(trace.id) if trace else None
            
            # Add provenance for each update
            if trace:
                for update in updates[:3]:  # Top 3 updates
                    await self.trace_service.add_provenance(
                        trace_id=trace.id,
                        source_type="policy_update",
                        source_id=f"policy_{update.get('domain', 'unknown')}",
                        source_text=update.get("recommendation", ""),
                        relevance_score=update.get("confidence", 0.5)
                    )
        # --- END TRACE CAPTURE ---
        
        # 4. Apply updates if they meet thresholds
        if updates:
            applied = await self._apply_updates(updates)
            logger.info(f"✅ Applied {len(applied)} policy updates")
            return {
                "applied": applied,
                "trace_id": trace_id
            }
        
        logger.info("ℹ️ No policy updates needed")
        return {"applied": [], "trace_id": trace_id}
    
    def _group_patterns(self, patterns: List[Dict]) -> Dict:
        """Group patterns by type for analysis."""
        grouped = {
            "security": [],
            "compliance": [],
            "contract": [],
            "procurement": [],
            "general": []
        }
        
        for p in patterns:
            trigger = p.get("trigger", "").lower()
            if any(word in trigger for word in ["security", "incident", "threat"]):
                grouped["security"].append(p)
            elif any(word in trigger for word in ["compliance", "gdpr", "hipaa"]):
                grouped["compliance"].append(p)
            elif any(word in trigger for word in ["contract", "legal", "agreement"]):
                grouped["contract"].append(p)
            elif any(word in trigger for word in ["procurement", "vendor", "supplier"]):
                grouped["procurement"].append(p)
            else:
                grouped["general"].append(p)
        
        return grouped
    
    async def _generate_policy_updates(self, grouped: Dict) -> List[Dict]:
        """Generate policy updates from grouped patterns."""
        updates = []
        
        for domain, patterns in grouped.items():
            if not patterns:
                continue
            
            # Calculate domain confidence
            avg_confidence = sum(p.get("confidence", 0.5) for p in patterns) / len(patterns)
            success_count = sum(1 for p in patterns if p.get("type") == "success")
            total_count = len(patterns)
            
            # Only update if there's enough evidence
            if total_count < 3:
                continue
            
            # Generate update if confidence is high enough
            if avg_confidence > 0.7:
                update = {
                    "domain": domain,
                    "action": "enhance",
                    "confidence": avg_confidence,
                    "patterns": patterns[:5],  # Top 5 patterns
                    "recommendation": self._generate_recommendation(domain, patterns)
                }
                updates.append(update)
            elif avg_confidence < 0.4 and success_count / total_count < 0.5:
                update = {
                    "domain": domain,
                    "action": "review",
                    "confidence": avg_confidence,
                    "patterns": patterns[:5],
                    "recommendation": f"Review {domain} patterns - low success rate detected"
                }
                updates.append(update)
        
        return updates
    
    def _generate_recommendation(self, domain: str, patterns: List[Dict]) -> str:
        """Generate a human-readable recommendation."""
        success_count = sum(1 for p in patterns if p.get("type") == "success")
        total = len(patterns)
        
        if success_count / total > 0.8:
            return f"✅ {domain} is performing well. Consider expanding {domain} policies."
        elif success_count / total > 0.5:
            return f"🔄 {domain} has mixed results. Focus on improvement patterns."
        else:
            return f"⚠️ {domain} needs review. Consider revising {domain} policies."
    
    async def _apply_updates(self, updates: List[Dict]) -> List[Dict]:
        """Apply policy updates to the system."""
        applied = []
        
        for update in updates:
            # Get current policy from system_config
            policy_key = f"policy_{update['domain']}"
            stmt = select(SystemConfig).where(SystemConfig.key == policy_key)
            result = await self.db.execute(stmt)
            policy = result.scalars().first()
            
            if policy:
                # Update existing policy
                try:
                    current = json.loads(policy.value)
                except:
                    current = {}
                
                # Apply update
                current["auto_updated"] = True
                current["last_update"] = update["confidence"]
                current["patterns_applied"] = len(update["patterns"])
                current["recommendation"] = update["recommendation"]
                current["timestamp"] = datetime.utcnow().isoformat()
                
                policy.value = json.dumps(current)
                logger.info(f"📝 Updated policy for {update['domain']}")
            else:
                # Create new policy
                new_policy = SystemConfig(
                    key=policy_key,
                    value=json.dumps({
                        "auto_created": True,
                        "domain": update["domain"],
                        "confidence": update["confidence"],
                        "patterns_applied": len(update["patterns"]),
                        "recommendation": update["recommendation"],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )
                self.db.add(new_policy)
                logger.info(f"📝 Created policy for {update['domain']}")
            
            await self.db.commit()
            applied.append(update)
        
        return applied
    
    async def get_policy_status(self) -> Dict:
        """Get the current status of all policies."""
        stmt = select(SystemConfig).where(SystemConfig.key.like("policy_%"))
        result = await self.db.execute(stmt)
        policies = result.scalars().all()
        
        status = {}
        for p in policies:
            try:
                status[p.key.replace("policy_", "")] = json.loads(p.value)
            except:
                status[p.key.replace("policy_", "")] = {"error": "Invalid policy data"}
        
        return status
    
    async def get_policy_recommendations(self) -> List[Dict]:
        """Get actionable recommendations based on current policies."""
        recommendations = []
        status = await self.get_policy_status()
        
        for domain, data in status.items():
            if data.get("auto_updated", False):
                if "recommendation" in data:
                    recommendations.append({
                        "domain": domain,
                        "recommendation": data["recommendation"],
                        "confidence": data.get("last_update", 0.5),
                        "patterns_applied": data.get("patterns_applied", 0)
                    })
        
        return sorted(recommendations, key=lambda x: x["confidence"], reverse=True)
