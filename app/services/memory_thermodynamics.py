"""
Thermodynamic Memory Engine
Manages memory phase transitions (Gas, Liquid, Ice, Snowflakes).
"""
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

class MemoryPhase(Enum):
    GAS = "gas"
    LIQUID = "liquid"
    ICE = "ice"
    SNOWFLAKE = "snowflake"

class PatternPhaseManager:
    """
    Manages transitions between memory phases for intelligence patterns.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def transition_to_phase(self, pattern: Dict[str, Any], new_phase: MemoryPhase) -> Dict[str, Any]:
        """
        Transition a pattern to a new thermodynamic phase.
        """
        old_phase = pattern.get("phase", MemoryPhase.GAS.value)
        pattern["phase"] = new_phase.value
        
        self.logger.info(f"Pattern {pattern.get('id')} transitioned: {old_phase} -> {new_phase.value}")
        
        # Add transition metadata
        pattern["last_transition"] = new_phase.value
        
        return pattern

    def check_transition_triggers(self, pattern: Dict[str, Any]) -> Optional[MemoryPhase]:
        """
        Evaluates pattern metrics to determine if a phase transition is triggered.
        """
        # Logic to trigger transitions based on confidence, age, failure rates
        confidence = pattern.get("confidence", 0.0)
        failure_rate = pattern.get("failure_rate", 0.0)
        age_days = pattern.get("age_days", 0)
        
        current_phase = pattern.get("phase", MemoryPhase.GAS.value)
        
        # Freezing (Liquid -> Ice)
        if current_phase == MemoryPhase.LIQUID.value and confidence > 0.85:
            return MemoryPhase.ICE
            
        # Melting (Ice -> Liquid)
        if current_phase == MemoryPhase.ICE.value and failure_rate > 0.20:
            return MemoryPhase.LIQUID
            
        # Evaporation (Liquid -> Gas)
        if current_phase == MemoryPhase.LIQUID.value and age_days > 30:
            return MemoryPhase.GAS
            
        # Sublimation (Ice -> Gas)
        if current_phase == MemoryPhase.ICE.value and pattern.get("conflicts", 0) > 3:
            return MemoryPhase.GAS
            
        return None

    def calculate_thermal_pressure(self, patterns: List[Dict[str, Any]], threshold: float = 20.0, redundancy_score: float = 0.0) -> float:
        """
        V3 Refined: Calculates 'Thermal Pressure' based on pattern density 
        AND redundancy (compressibility). 
        EXCLUDES Meta-patterns to prevent recursive synthesis.
        """
        # Exclude meta-patterns from the count
        base_patterns = [p for p in patterns if p.get("metadata", {}).get("type") != "meta_pattern"]
        pattern_count = len(base_patterns)
        
        count_density = min(pattern_count / threshold, 1.0)
        
        # Redundancy score (0.0 to 1.0) indicates overlap
        pressure = (count_density * 0.4) + (redundancy_score * 0.6)
        return round(pressure, 2)

    async def evaporate_patterns(self, db_session, domain: str, decay_threshold_days: int = 90):
        """
        V3 Refined: Implements 'Evaporation' with real guards.
        Formula: Retention Score = (Occurrence Count * 2) - (Days Since Update / 5.0) [Days]
        Purges if Retention Score < 0 and NOT critical/dependent.
        """
        from app.models.semantic import SemanticPattern
        from sqlalchemy import select, func, delete
        from datetime import datetime, timezone
        
        # 1. Fetch candidates for evaporation
        stmt = select(SemanticPattern).where(SemanticPattern.pattern_type == domain)
        result = await db_session.execute(stmt)
        patterns = result.scalars().all()
        
        deleted_count = 0
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        for p in patterns:
            # REAL GUARD: Check for dependents
            # In V3, SemanticPattern has 'occurrence_count' to check usage
            # Check if this pattern is a parent of others
            dep_stmt = select(func.count(SemanticPattern.id)).where(
                SemanticPattern.pattern_type == domain, # simple scope
                # Assuming 'derived_from' field exists in model
                SemanticPattern.trigger.contains(str(p.id)) 
            )
            dep_count = await db_session.execute(dep_stmt)
            has_dependents = dep_count.scalar() > 0
            
            is_critical = p.weight > 0.9 or "critical" in (p.trigger or "").lower()
            
            if is_critical or has_dependents:
                continue
                
            # Retention Calculation (Unit: days)
            days_stale = (now - p.updated_at).days
            retention_score = (p.occurrence_count * 2) - (days_stale / 5.0)
            
            if retention_score < 0:
                await db_session.delete(p)
                deleted_count += 1
                
        return deleted_count

    async def handle_synthesis_rejection(self, env_id: str, domain: str, reason: str):
        """
        V3: Handles human rejection of synthesis.
        - Raises local threshold by 50%.
        - Persists the change to the environment.
        """
        from app.api.v2.services.environment_service import environment_service
        self.logger.info(f"🚫 Synthesis rejected for {env_id}:{domain}. Reason: {reason}")
        
        env = await environment_service.get_environment(env_id)
        if env:
            await environment_service.update_environment(env_id, {
                "thermal_threshold": env.thermal_threshold * 1.5,
                "is_armed": False # Disarm until pressure drops
            })
        return True

    async def evaluate_synthesis_need(self, env_id: str, patterns: List[Dict[str, Any]], domain: str, redundancy_score: float = 0.0):
        """
        V3 Refined: Determines if environment needs synthesis with:
        - Hysteresis: Trigger at 1.0, re-arm at 0.5. Persisted in Environment.
        - Recursive Guard: Excludes Meta-patterns.
        - Idempotency: Don't double-notify.
        """
        from app.api.v2.services.environment_service import environment_service
        env = await environment_service.get_environment(env_id)
        if not env:
            return False

        pressure = self.calculate_thermal_pressure(patterns, threshold=env.thermal_threshold, redundancy_score=redundancy_score)
        
        # Hysteresis re-arm logic
        if pressure < 0.5 and not env.is_armed:
            await environment_service.update_environment(env_id, {"is_armed": True})
            env.is_armed = True
            
        if pressure >= 1.0 and env.is_armed:
            from app.models.pending_action import PendingAction
            from app.db.session import SessionLocal
            from sqlalchemy import select, and_
            
            async with SessionLocal() as db:
                # 1. Idempotency Check
                result = await db.execute(
                    select(PendingAction).where(
                        and_(
                            PendingAction.agent_type == "synthesis_engine",
                            PendingAction.status == "pending",
                            PendingAction.query.contains(domain)
                        )
                    )
                )
                if result.scalars().first():
                    return False

                self.logger.info(f"🔥 HIGH THERMAL PRESSURE ({pressure}) in {env_id}:{domain}. Proposing synthesis.")
                
                # 2. Inform the Human
                action = PendingAction(
                    agent_type="synthesis_engine",
                    query=f"High Thermal Pressure ({pressure}) in {domain}. Redundancy is {redundancy_score}. Should I synthesize Meta-Patterns?",
                    options=["synthesize", "ignore", "raise_threshold"],
                    status="pending"
                )
                db.add(action)
                await db.commit()
                
                # 3. Disarm until re-armed or completed
                await environment_service.update_environment(env_id, {"is_armed": False})
            
            return True
        return False
