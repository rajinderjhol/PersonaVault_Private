"""
Thermodynamic Memory Engine
Manages memory phase transitions (Gas, Liquid, Ice, Snowflakes).
"""
from typing import Dict, Any, Optional
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
