"""
Service Registry - Cordis-inspired plugin system.
"""
import logging
from typing import Dict, Any, Optional, Type, Callable

logger = logging.getLogger(__name__)

class ServiceRegistry:
    """
    A service registry that allows runtime swapping of components.
    Inspired by DeepSeek Harness's Cordis meta-framework.
    """
    
    _services: Dict[str, Dict[str, Any]] = {}
    _hooks: Dict[str, list] = {}
    
    @classmethod
    def register(cls, service_type: str, name: str, implementation: Any, 
                 hooks: Optional[Dict[str, Callable]] = None):
        """Register a service with optional lifecycle hooks."""
        if service_type not in cls._services:
            cls._services[service_type] = {}
        cls._services[service_type][name] = implementation
        
        if hooks:
            cls._hooks.setdefault(service_type, []).append({
                "name": name,
                "hooks": hooks
            })
        
        logger.info(f"✅ Registered {service_type}: {name}")
    
    @classmethod
    def get(cls, service_type: str, name: str = None) -> Optional[Any]:
        """Get a service by type and name."""
        if name:
            return cls._services.get(service_type, {}).get(name)
        # Return first available if no name specified
        first = list(cls._services.get(service_type, {}).values())
        return first[0] if first else None
    
    @classmethod
    def list_services(cls, service_type: str = None) -> Dict:
        """List all registered services."""
        if service_type:
            return cls._services.get(service_type, {})
        return cls._services
    
    @classmethod
    def swap(cls, service_type: str, old_name: str, new_name: str) -> bool:
        """
        Swap a service at runtime without restart.
        This is the key "leapfrog" feature.
        """
        if service_type not in cls._services:
            logger.warning(f"Service type {service_type} not found")
            return False
        
        if old_name not in cls._services[service_type]:
            logger.warning(f"Service {old_name} not found")
            return False
        
        if new_name not in cls._services[service_type]:
            logger.warning(f"Service {new_name} not found")
            return False
        
        # Store the old service for rollback
        old_service = cls._services[service_type][old_name]
        cls._services[service_type][old_name] = cls._services[service_type][new_name]
        
        # Trigger any hooks
        if service_type in cls._hooks:
            for hook in cls._hooks[service_type]:
                if hook["name"] == new_name:
                    on_swap = hook["hooks"].get("on_swap")
                    if on_swap:
                        on_swap(old_service)
        
        logger.info(f"🔄 Swapped {service_type}: {old_name} → {new_name}")
        return True
    
    @classmethod
    def register_hook(cls, service_type: str, name: str, 
                     on_swap: Optional[Callable] = None,
                     on_init: Optional[Callable] = None):
        """Register lifecycle hooks for a service."""
        cls._hooks.setdefault(service_type, []).append({
            "name": name,
            "hooks": {
                "on_init": on_init,
                "on_swap": on_swap
            }
        })
