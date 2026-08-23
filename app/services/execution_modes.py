"""
Sovereign Execution Modes - Inspired by DeepSeek Harness.
"""
import logging
from enum import Enum
from typing import Dict, Any, Optional
from app.services.service_registry import ServiceRegistry

logger = logging.getLogger(__name__)

class ExecutionMode(Enum):
    STANDARD = "standard"        # Full tool access with HITL
    RESTRICTED = "restricted"    # No external tools, only Ice memory
    SIMULATION = "simulation"    # Sandboxed decision replay
    AUDIT = "audit"              # Read-only with full logging

class ExecutionModeManager:
    """Manages the current execution mode."""
    
    _current_mode = ExecutionMode.STANDARD
    _mode_configs = {
        ExecutionMode.STANDARD: {
            "tools_enabled": True,
            "hitl_required": True,
            "ice_memory_only": False,
            "sandboxed": False,
            "logging_level": "info"
        },
        ExecutionMode.RESTRICTED: {
            "tools_enabled": False,
            "hitl_required": False,
            "ice_memory_only": True,
            "sandboxed": False,
            "logging_level": "warn"
        },
        ExecutionMode.SIMULATION: {
            "tools_enabled": True,
            "hitl_required": False,
            "ice_memory_only": False,
            "sandboxed": True,
            "logging_level": "debug"
        },
        ExecutionMode.AUDIT: {
            "tools_enabled": True,
            "hitl_required": False,
            "ice_memory_only": False,
            "sandboxed": False,
            "logging_level": "info"
        }
    }
    
    @classmethod
    def set_mode(cls, mode: ExecutionMode):
        """Set the current execution mode."""
        cls._current_mode = mode
        logger.info(f"🔄 Execution mode changed to: {mode.value}")
    
    @classmethod
    def get_mode(cls) -> ExecutionMode:
        return cls._current_mode
    
    @classmethod
    def get_config(cls) -> Dict:
        return cls._mode_configs.get(cls._current_mode, {})
    
    @classmethod
    def is_tools_enabled(cls) -> bool:
        return cls.get_config().get("tools_enabled", True)
    
    @classmethod
    def is_hitl_required(cls) -> bool:
        return cls.get_config().get("hitl_required", True)
    
    @classmethod
    def is_ice_memory_only(cls) -> bool:
        return cls.get_config().get("ice_memory_only", False)
    
    @classmethod
    def is_sandboxed(cls) -> bool:
        return cls.get_config().get("sandboxed", False)
