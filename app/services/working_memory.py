from typing import Any, Dict, Optional

class WorkingMemory: # No imports needed for this file
    """Short-lived memory for current session context."""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
    
    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key)
    
    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
    
    def update(self, key: str, value: Any) -> None:
        self._data[key] = value
    
    def clear(self) -> None:
        self._data.clear()
    
    def get_all(self) -> Dict[str, Any]:
        return self._data.copy()