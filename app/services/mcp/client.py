# app/services/mcp/client.py

import json
import sys
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# Add the free-search-mcp to path
SEARCH_MCP_PATH = "/home/rajinderj8888/personavault/backend/free-search-mcp/src"
if SEARCH_MCP_PATH not in sys.path:
    sys.path.insert(0, SEARCH_MCP_PATH)

class MCPClient:
    def __init__(self):
        self.servers = {}
        self.active_connections = {}
        
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Call a tool on an MCP server."""
        try:
            # ✅ Import from server.py where the actual tool is defined
            from search_mcp.server import search
            
            if tool_name == "search":
                result = await search(
                    query=params.get("query"),
                    max_results=params.get("num_results", 5),
                    freshness=params.get("freshness", "week"),
                    category=params.get("category"),
                    format="json"
                )
                return result
            else:
                logger.warning(f"Unknown tool: {tool_name}")
                return {"error": f"Tool {tool_name} not found"}
                
        except ImportError as e:
            logger.error(f"Failed to import search: {e}")
            return {"error": "search_mcp module not found", "details": str(e)}
        except Exception as e:
            logger.error(f"Failed to call MCP tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def connect(self, server_name: str) -> bool:
        """Connect to an MCP server."""
        return True
    
    async def disconnect(self, server_name: str) -> bool:
        """Disconnect from an MCP server."""
        return True

# Create a singleton instance
mcp_client = MCPClient()