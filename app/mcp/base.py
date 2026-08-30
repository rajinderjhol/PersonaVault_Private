from typing import Dict, Any

class BaseMCPConnector:
    """Base class for all MCP connectors."""
    def __init__(self, config: Dict[str, Any], *args, **kwargs):
        self.config = config
