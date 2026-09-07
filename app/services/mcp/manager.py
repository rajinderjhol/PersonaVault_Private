import json
import subprocess
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import psutil

logger = logging.getLogger(__name__)

class MCPServerManager:
    """Manages MCP server lifecycle and connections."""
    
    def __init__(self):
        self.servers: Dict[str, Dict] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.config_path = Path("config/mcp/servers.json")
        self.load_config()
    
    def load_config(self):
        """Load MCP server configurations."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.servers = config.get("mcpServers", {})
        else:
            # Default configuration with Free Search MCP
            self.servers = {
                "free-search": {
                    "name": "Free Web Search",
                    "description": "Multi-engine web search with no API key required",
                    "command": "python",
                    "args": ["-m", "search_mcp"],
                    "cwd": str(Path.home() / "personavault/backend/free-search-mcp"),
                    "env": {
                        "PATH": "/usr/local/bin:/usr/bin:/bin",
                        "PYTHONPATH": str(Path.home() / "personavault/backend/free-search-mcp/src")
                    },
                    "enabled": True,
                    "tools": ["search", "fetch", "fetch_batch", "research", "read_doc", "compare", "download"],
                    "status": "disconnected"
                }
            }
            self.save_config()
    
    def save_config(self):
        """Save MCP server configurations."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump({"mcpServers": self.servers}, f, indent=2)
    
    async def connect_server(self, server_id: str) -> Dict[str, Any]:
        """Connect to an MCP server."""
        if server_id not in self.servers:
            return {"success": False, "error": f"Server {server_id} not found"}
        
        server = self.servers[server_id]
        
        try:
            # Start the server process
            process = subprocess.Popen(
                [server["command"]] + server.get("args", []),
                cwd=server.get("cwd"),
                env=server.get("env", {}),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes[server_id] = process
            server["status"] = "connected"
            self.save_config()
            
            return {"success": True, "message": f"Connected to {server['name']}"}
            
        except Exception as e:
            logger.error(f"Failed to connect to {server_id}: {e}")
            server["status"] = "error"
            self.save_config()
            return {"success": False, "error": str(e)}
    
    async def disconnect_server(self, server_id: str) -> Dict[str, Any]:
        """Disconnect from an MCP server."""
        if server_id in self.processes:
            process = self.processes[server_id]
            process.terminate()
            await asyncio.sleep(1)
            if process.poll() is None:
                process.kill()
            del self.processes[server_id]
            
            if server_id in self.servers:
                self.servers[server_id]["status"] = "disconnected"
                self.save_config()
            
            return {"success": True, "message": f"Disconnected from {server_id}"}
        
        return {"success": False, "error": f"Server {server_id} not running"}
    
    # Add this method to MCPServerManager

    async def call_tool(self, server_id: str, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on an MCP server."""
        if server_id not in self.servers:
            return {"success": False, "error": f"Server {server_id} not found"}
        
        if server_id == "free-search":
            try:
                # Import free-search-mcp directly
                import sys
                import asyncio
                sys.path.insert(0, '/home/rajinderj8888/personavault/backend/free-search-mcp/src')
                
                from search_mcp.server import search, fetch, research
                
                if tool_name == "search":
                    result = await search(
                        query=params.get("query"),
                        max_results=params.get("max_results", 5),
                        freshness=params.get("freshness", "week"),
                        format="json"
                    )
                    return {"success": True, "result": result}
                elif tool_name == "fetch":
                    result = await fetch(
                        url=params.get("url"),
                        format="json"
                    )
                    return {"success": True, "result": result}
                elif tool_name == "research":
                    result = await research(
                        question=params.get("query"),
                        depth=params.get("depth", 3),
                        format="json"
                    )
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": f"Tool {tool_name} not implemented"}
                    
            except Exception as e:
                logger.error(f"Free search error: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": f"Server {server_id} not supported"}

    def get_status(self, server_id: str) -> Dict[str, Any]:
        """Get the status of an MCP server."""
        if server_id not in self.servers:
            return {"error": f"Server {server_id} not found"}
        
        server = self.servers[server_id]
        return {
            "id": server_id,
            "name": server.get("name", server_id),
            "status": server.get("status", "unknown"),
            "tools": server.get("tools", []),
            "description": server.get("description", "")
        }
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """List all configured MCP servers."""
        return [
            {
                "id": server_id,
                "name": server.get("name", server_id),
                "status": server.get("status", "unknown"),
                "tools": server.get("tools", []),
                "description": server.get("description", ""),
                "enabled": server.get("enabled", True)
            }
            for server_id, server in self.servers.items()
        ]
    
    async def install_server(self, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """Install a new MCP server from configuration."""
        server_id = server_config.get("id")
        if not server_id:
            return {"success": False, "error": "Server ID required"}
        
        if server_id in self.servers:
            return {"success": False, "error": f"Server {server_id} already exists"}
        
        self.servers[server_id] = {
            "name": server_config.get("name", server_id),
            "description": server_config.get("description", ""),
            "command": server_config.get("command", "python"),
            "args": server_config.get("args", []),
            "cwd": server_config.get("cwd"),
            "env": server_config.get("env", {}),
            "enabled": server_config.get("enabled", True),
            "tools": server_config.get("tools", []),
            "status": "disconnected"
        }
        
        self.save_config()
        return {"success": True, "message": f"Server {server_id} installed"}
    
    async def uninstall_server(self, server_id: str) -> Dict[str, Any]:
        """Uninstall an MCP server."""
        if server_id in self.processes:
            await self.disconnect_server(server_id)
        
        if server_id in self.servers:
            del self.servers[server_id]
            self.save_config()
            return {"success": True, "message": f"Server {server_id} uninstalled"}
        
        return {"success": False, "error": f"Server {server_id} not found"}
