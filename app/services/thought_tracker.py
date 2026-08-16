"""
Thought Tracker - Real-time Chain-of-Thought streaming
"""
import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

class ThoughtTracker:
    """Tracks and streams thought steps in real-time."""
    
    def __init__(self):
        self.steps = []
        self.start_time = None
        self.current_step = None
        self.is_complete = False
    
    def start(self):
        """Start tracking."""
        self.start_time = time.time()
        self.steps = []
        self.is_complete = False
    
    def add_step(self, label: str, description: str, data: dict = None):
        """Add a thought step."""
        step = {
            "step": len(self.steps) + 1,
            "label": label,
            "description": description,
            "data": data or {},
            "timestamp": time.time() - self.start_time,
            "duration": 0,
            "status": "in_progress"
        }
        self.steps.append(step)
        self.current_step = step
        return step
    
    def complete_step(self, step_index: int = None):
        """Mark a step as complete."""
        if step_index is None:
            step_index = len(self.steps) - 1
        if 0 <= step_index < len(self.steps):
            self.steps[step_index]["status"] = "complete"
            if step_index > 0:
                self.steps[step_index - 1]["duration"] = self.steps[step_index]["timestamp"] - self.steps[step_index - 1]["timestamp"]
    
    def fail_step(self, step_index: int = None, error: str = ""):
        """Mark a step as failed."""
        if step_index is None:
            step_index = len(self.steps) - 1
        if 0 <= step_index < len(self.steps):
            self.steps[step_index]["status"] = "failed"
            self.steps[step_index]["error"] = error
    
    def get_steps(self) -> List[Dict]:
        """Get all steps."""
        return self.steps
    
    def get_current_step(self) -> Optional[Dict]:
        """Get the current step."""
        return self.current_step
    
    def get_total_time(self) -> float:
        """Get total time."""
        return time.time() - self.start_time if self.start_time else 0
    
    def is_running(self) -> bool:
        """Check if tracking is still running."""
        return not self.is_complete and self.start_time is not None
    
    def complete(self):
        """Mark tracking as complete."""
        self.is_complete = True
        if self.steps:
            self.steps[-1]["duration"] = time.time() - self.start_time - self.steps[-1]["timestamp"]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "steps": self.steps,
            "total_time": self.get_total_time(),
            "is_complete": self.is_complete
        }
