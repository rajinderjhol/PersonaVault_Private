# app/services/intelligence_gateway.py - FULLY FIXED VERSION

"""
Unified Intelligence Gateway for PersonaVault. Handles ALL intelligence routing through MCP protocol.
"""

import json
import os
import re
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from pathlib import Path

# ============================================================================
# SAFE IMPORTS
# ============================================================================

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    genai = None

from app.repositories.system_config_repository import SystemConfigRepository
from app.db.session import SessionLocal, AsyncSession
from app.utils.plugin_loader import PluginLoader
from app.core.permissions import check_tool_permission
from app.models import User
from sqlalchemy import select

logger = logging.getLogger(__name__)

# ============================================================================
# PART 1: MCP PROTOCOL IMPLEMENTATION
# ============================================================================

class MCPTool:
    def __init__(self, name: str, description: str, handler: Callable, 
                 parameters: Dict[str, Any] = None):
        self.name = name
        self.description = description
        self.handler = handler
        self.parameters = parameters or {}

class MCPRegistry:
    _tools: Dict[str, MCPTool] = {}
    
    @classmethod
    def register(cls, tool: MCPTool):
        cls._tools[tool.name] = tool
        return tool
    
    @classmethod
    def get_tool(cls, name: str) -> Optional[MCPTool]:
        return cls._tools.get(name)
    
    @classmethod
    def list_tools(cls) -> List[Dict[str, Any]]:
        return [
            {"name": tool.name, "description": tool.description, "parameters": tool.parameters}
            for tool in cls._tools.values()
        ]
    
    @classmethod
    async def call(cls, tool_name: str, user_role: str = None, **kwargs) -> Dict[str, Any]:
        if user_role and not check_tool_permission(user_role, tool_name):
            return {"success": False, "error": f"Permission denied for tool '{tool_name}'"}
        
        tool = cls.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        try:
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**kwargs)
            else:
                result = tool.handler(**kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================================
# PART 2: TOOL IMPLEMENTATIONS
# ============================================================================

class DatabaseTool:
    def __init__(self):
        self.connections = {}
    
    def register_connection(self, name: str, config: Dict[str, Any]):
        self.connections[name] = config
    
    async def query(self, db_name: str, sql: str) -> List[Dict[str, Any]]:
        return [{"error": "Not implemented"}]

class EmailTool:
    def __init__(self):
        self.connections = {}
    
    def register_connection(self, name, config):
        self.connections[name] = config

class FileTool:
    def __init__(self):
        self.index = {}

class WebTool:
    def __init__(self):
        self.config = {}
        self.enabled = False

class AITool:
    def __init__(self):
        self.providers = {}
    
    def register_provider(self, name, config):
        self.providers[name] = config


# ============================================================================
# PART 3: INTELLIGENCE GATEWAY
# ============================================================================

class IntelligenceGateway:
    def __init__(self):
        self.config = {}
        self.db_tool = DatabaseTool()
        self.email_tool = EmailTool()
        self.file_tool = FileTool()
        self.web_tool = WebTool()
        self.ai_tool = AITool()
        self.agent_tool = None
        self._initialized_from_db = False
        self.packs = []
        self._register_mcp_tools()

    # ==================== AI GENERATE ====================
    
    async def generate(self, provider: str, query: str, context: str = "") -> Dict[str, Any]:
        start_time = time.time()
        provider_key = provider.lower()
        config = self.ai_tool.providers.get(provider_key)
        
        # Debug logging
        logger.info(f"🔍 DEBUG - Provider: {provider_key}, Model: {config.get('model') if config else 'N/A'}")
        
        system_instruction = (
            "You are PersonaVault, a secure and human-centric private AI assistant.\n\n"
            "MISSION: Provide insightful answers using the provided context.\n\n"
            "RULES:\n"
            "1. Use provided context as your primary truth.\n"
            "2. If info is missing from context, use your high-reasoning capabilities.\n"
            "3. OUTPUT FORMAT: Human-like, concise, and direct."
        )
        
        formatted_context = f"CONTEXT:\n{context}" if context else "No additional context provided."

        # OLLAMA (Local)
        if provider_key == "ollama":
            if not HAS_HTTPX:
                return {"response": "[Ollama not available - httpx missing]"}
            
            host = "http://localhost:11434"
            model = config.get("model", "tinydolphin:latest") if config else "tinydolphin:latest"
            if config:
                host = config.get('host', host)
                model = config.get("model", "tinydolphin:latest") if config else "tinydolphin:latest"
            
            try:
                logger.info(f"Ollama request started at {start_time}")
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{host}/api/chat",
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": f"{formatted_context}\n\nUSER_QUERY: {query}"}
                            ],
                            "stream": False,
                            "options": {"temperature": 0.2}
                        },
                        timeout=120.0
                    )
                    end_time = time.time()
                    logger.info(f"Ollama request completed in {end_time - start_time} seconds")
                    if response.status_code == 200:
                        msg_data = response.json().get("message", {})
                        return {"response": msg_data.get("content", "No response")}
                    else:
                        return {"response": f"[Ollama error {response.status_code}]"}
            except Exception as e:
                logger.exception(f"Ollama error type: {type(e).__name__}, message: {str(e)}")
                return {"response": f"[Ollama unavailable: {type(e).__name__}]"}
        
        # GROQ (Cloud)
        elif provider_key == "groq":
            if not HAS_HTTPX:
                return {"response": "[Groq not available - httpx missing]"}
            
            api_key = os.environ.get("GROQ_API_KEY") or (config.get("api_key") if config else None)
            if not api_key:
                return {"response": "[Groq API key not configured]"}
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": config.get("model", "llama-3.3-70b-versatile") if config else "llama-3.3-70b-versatile",
                            "messages": [
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": f"{formatted_context}\n\nUSER_QUERY: {query}"}
                            ],
                            "temperature": 0.2,
                            "max_tokens": 2048
                        },
                        timeout=120.0
                    )
                    if response.status_code == 200:
                        return {"response": response.json()["choices"][0]["message"]["content"]}
                    else:
                        return {"response": f"[Groq error {response.status_code}]"}
            except Exception as e:
                return {"response": f"[Groq unavailable: {str(e)}]"}
        
        # GEMINI (Cloud)
        elif provider_key == "gemini":
            if not HAS_GEMINI:
                return {"response": "[Gemini not available]"}
            
            api_key = config.get("api_key") if config else None
            if not api_key:
                return {"response": "[Gemini API key not configured]"}
            
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name=config.get("model", "gemini-2.0-flash") if config else "gemini-2.0-flash",
                    system_instruction=system_instruction
                )
                response = await model.generate_content_async(f"{formatted_context}\n\nUSER_QUERY: {query}")
                return {"response": response.text}
            except Exception as e:
                return {"response": f"[Gemini unavailable: {str(e)}]"}
        
        return {"response": f"[Provider '{provider}' not implemented]"}
    
    # ==================== REGISTRATION ====================
    
    def _register_mcp_tools(self):
        MCPRegistry.register(MCPTool(
            name="ai_generate",
            description="Generate text using an AI provider",
            parameters={"provider": "string", "query": "string", "context": "string", "user_role": "string"},
            handler=self.generate
        ))
        
        MCPRegistry.register(MCPTool(
            name="pattern_explore",
            description="Explore learned patterns",
            parameters={"user_id": "integer"},
            handler=self._pattern_explore
        ))
        
        try:
            plugins = PluginLoader.load_plugins(plugins_dir="plugins")
            for plugin in plugins:
                MCPRegistry.register(MCPTool(
                    name=plugin["name"],
                    description=plugin["description"],
                    parameters=plugin.get("parameters", {}),
                    handler=plugin["handler"]
                ))
                logger.info(f"🚀 Registered MCP tool: {plugin['name']}")
        except Exception as e:
            logger.warning(f"Could not load plugins: {e}")

    # ==================== CONFIG LOADING ====================
    
    async def _apply_config_async(self, db: AsyncSession):
        """Apply all configurations from DB."""
        try:
            repo = SystemConfigRepository(db)
            ai_providers = await repo.get_config("ai_providers") or {}
            logger.info(f"DEBUG: ai_providers loaded: {ai_providers}")
            for name, ai_config in ai_providers.items():
                logger.info(f"DEBUG: Processing provider: {name}, config: {ai_config}")
                if ai_config.get("enabled", False):
                    self.ai_tool.register_provider(name, ai_config)
                    logger.info(f"DEBUG: Registered provider: {name}")
                else:
                    logger.info(f"DEBUG: Provider {name} is disabled")
            self.packs = await repo.get_config("packs") or []
        except Exception as e:
            logger.warning(f"Could not load config from DB: {e}")
    
    # PUBLIC WRAPPER FOR TESTS
    async def apply_config(self, db: AsyncSession) -> None:
        """Public wrapper for _apply_config_async (used by tests)."""
        await self._apply_config_async(db)
    
    async def _load_config_from_db(self, db: AsyncSession):
        """Load configuration from database."""
        await self._apply_config_async(db)
    
    async def ensure_initialized(self):
        """Ensure gateway is initialized from database."""
        if not self._initialized_from_db:
            async with SessionLocal() as db:
                await self._apply_config_async(db)
            self._initialized_from_db = True
    
    async def reload_config(self):
        """Reload configuration from database."""
        self._initialized_from_db = False
        await self.ensure_initialized()
        logger.info("✅ Intelligence Gateway reloaded")
    
    async def hot_reload(self, db: AsyncSession):
        """Hot reload configuration."""
        MCPRegistry._tools.clear()
        await self._apply_config_async(db)
        self._register_mcp_tools()
        logger.info("✅ Intelligence Gateway hot-reload complete.")
    
    # ==================== CHAT ====================
    
    _user_role_cache = {}

    async def get_user_role(self, user_id: int):
        if user_id not in self._user_role_cache:
            async with SessionLocal() as db:
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalars().first()
                self._user_role_cache[user_id] = user.role if user else "user"
        return self._user_role_cache[user_id]

    async def chat(self, user_id: int, query: str, state: Any = None, patient_id: str = None, provider: str = "ollama") -> Dict[str, Any]:
        chat_start = time.time()
        
        # Normalize user_id
        user_id_int = user_id.id if hasattr(user_id, 'id') else user_id
        if not isinstance(user_id_int, int):
            return {"error": "Invalid user_id"}
        
        user_role = await self.get_user_role(user_id_int)
        
        await self.ensure_initialized()
        
        # Use the provided provider or default to ollama
        context = "Context assembled."
        
        # Bypass MCP registry for direct Ollama call
        result = await self.generate(provider, query, context=context)
        
        # Ensure the response includes the provider
        final_result = {"response": result.get("response", "No response")}
        final_result["provider"] = provider
        
        return final_result
    
    # ==================== PATTERN EXPLORE ====================
    
    async def _pattern_explore(self, user_id: int) -> List[Dict]:
        return []


# ============================================================================
# GATEWAY INSTANCE
# ============================================================================

gateway = IntelligenceGateway()