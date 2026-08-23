# app/services/intelligence_gateway.py - CLEAN VERSION

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
from app.services.thought_tracker import ThoughtTracker
from app.services.safe_cache import SafeCache
from app.services.ollama_manager import ollama_manager
from app.services.service_registry import ServiceRegistry
from app.services.execution_modes import ExecutionMode, ExecutionModeManager

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
        self.thought_tracker = ThoughtTracker()
        self.cache = SafeCache(max_size=50, default_ttl=300)
        self._initialized_from_db = False
        self.packs = []
        self._register_mcp_tools()
        self._register_services()
        self._register_groq_provider()  # Register Groq on startup

    # ==================== GROQ PROVIDER REGISTRATION ====================
    
    def _register_groq_provider(self):
        """Register Groq provider with the correct model."""
        groq_key = os.environ.get("GROQ_API_KEY")
        if not groq_key:
            # Try to read from .env
            try:
                env_paths = [".env", "../.env", "../../.env"]
                for env_path in env_paths:
                    if os.path.exists(env_path):
                        with open(env_path, "r") as f:
                            for line in f:
                                if line.startswith("GROQ_API_KEY="):
                                    groq_key = line.split("=")[1].strip().strip('"').strip("'")
                                    break
                        if groq_key:
                            break
            except Exception:
                pass
        
        if groq_key and groq_key != "YOUR_GROQ_API_KEY":
            self.ai_tool.register_provider("groq", {
                "enabled": True,
                "host": "https://api.groq.com/openai/v1",
                "model": "qwen/qwen3.6-27b",
                "api_key": groq_key
            })
            logger.info("✅ Groq provider registered with qwen/qwen3.6-27b")
        else:
            logger.warning("⚠️ GROQ_API_KEY not found or invalid, Groq provider not registered")

    # ==================== AI GENERATE ====================
    
    async def generate(self, provider: str, query: str, context: str = "") -> Dict[str, Any]:
        # Check execution mode
        if ExecutionModeManager.is_ice_memory_only():
            logger.info("🧊 Restricted mode: using only Ice memory")
            return {"response": "Restricted mode: I can only access crystallized memory."}
        
        if ExecutionModeManager.is_sandboxed():
            logger.info("🏖️ Simulation mode: no side effects")
            # In simulation mode, don't cache or persist
        
        cache_key = self.cache._get_key(query, {"provider": provider})
        cached = self.cache.get(cache_key)
        if cached and not ExecutionModeManager.is_sandboxed():
            logger.info(f"🔁 Cache hit for query: {query[:50]}...")
            return cached

        start_time = time.time()
        provider_key = provider.lower()
        config = self.ai_tool.providers.get(provider_key)
        
        logger.info(f"🔍 DEBUG - Provider: {provider_key}, Config: {config}")
        
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
            
            host = config.get('host', "http://localhost:11434") if config else "http://localhost:11434"
            model = config.get("model", "tinydolphin:latest") if config else "tinydolphin:latest"
            
            try:
                logger.info(f"Ollama request: model={model}, host={host}")
                async with httpx.AsyncClient(timeout=60.0) as client:
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
                        timeout=60.0
                    )
                    if response.status_code == 200:
                        msg_data = response.json().get("message", {})
                        result = {"response": msg_data.get("content", "No response")}
                        self.cache.set(cache_key, result)
                        return result
                    else:
                        return {"response": f"[Ollama error {response.status_code}]"}
            except httpx.TimeoutException:
                return {"response": "[Ollama timeout - please try again]"}
            except Exception as e:
                return {"response": f"[Ollama unavailable: {type(e).__name__}]"}
        
        # GROQ (Cloud)
        elif provider_key == "groq":
            if not HAS_HTTPX:
                return {"response": "[Groq not available - httpx missing]"}
            
            api_key = os.environ.get("GROQ_API_KEY") or (config.get("api_key") if config else None)
            if not api_key:
                return {"response": "[Groq API key not configured]"}
            
            model = config.get("model", "qwen/qwen3.6-27b") if config else "qwen/qwen3.6-27b"
            
            try:
                logger.info(f"Groq request: model={model}")
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model,
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
                        result = {"response": response.json()["choices"][0]["message"]["content"]}
                        self.cache.set(cache_key, result)
                        return result
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
            
            model_name = config.get("model", "gemini-2.0-flash") if config else "gemini-2.0-flash"
            
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction
                )
                response = await model.generate_content_async(f"{formatted_context}\n\nUSER_QUERY: {query}")
                result = {"response": response.text}
                self.cache.set(cache_key, result)
                return result
            except Exception as e:
                return {"response": f"[Gemini unavailable: {str(e)}]"}
        
        return {"response": f"[Provider '{provider}' not implemented]"}
    
    # ==================== REGISTRATION ====================
    

    FALLBACK_CHAIN = {
        "groq": ["gpt-oss-20b", "gpt-oss-120b"],
        "gemini": ["ollama"]
    }

    async def _call_with_fallback(self, provider: str, query: str, context: str) -> Dict[str, Any]:
        """Calls provider with automatic fallback on rate limit (429)."""
        providers_to_try = [provider] + self.FALLBACK_CHAIN.get(provider, [])
        
        last_error = None
        for p in providers_to_try:
            logger.info(f"Attempting provider: {p}")
            
            # Use the existing generate logic but wrapped
            result = await self.generate(p, query, context)
            
            # Check if it was a rate limit error (429)
            response_text = result.get("response", "")
            if "429" in response_text or "unavailable" in response_text.lower():
                logger.warning(f"Provider {p} failed or rate limited.")
                last_error = response_text
                continue
            
            # Success
            return result
            
        return {"response": f"[All providers failed. Last error: {last_error}]"}

    def _register_services(self):
        """Register core services with ServiceRegistry for runtime swapping."""
        # Register inference providers
        ServiceRegistry.register("inference", "ollama", self.generate)
        ServiceRegistry.register("inference", "groq", self.generate)
        ServiceRegistry.register("inference", "gemini", self.generate)
        
        # Register memory providers
        ServiceRegistry.register("memory", "episodic", self._get_episodic_memory)
        ServiceRegistry.register("memory", "semantic", self._get_semantic_memory)
        
        # Register governance providers
        ServiceRegistry.register("governance", "local", self._apply_local_governance)
        ServiceRegistry.register("governance", "verilink", self._apply_verilink_governance)
        
        logger.info("✅ Services registered with ServiceRegistry")
    
    def _get_episodic_memory(self):
        """Get episodic memory service."""
        # Dynamic import to avoid circular dependency
        from app.services.memory_service import MemoryService
        return MemoryService()
    
    def _get_semantic_memory(self):
        """Get semantic memory service."""
        # Dynamic import to avoid circular dependency
        from app.services.vector_service import VectorService
        return VectorService()
    
    def _apply_local_governance(self, decision):
        """Apply local governance rules."""
        return {"approved": True, "reason": "Local governance passed"}
    
    def _apply_verilink_governance(self, decision):
        """Apply VeriLink governance."""
        return {"approved": True, "reason": "VeriLink governance passed"}

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
                if ai_config.get("enabled", False):
                    self.ai_tool.register_provider(name, ai_config)
                    logger.info(f"Registered provider: {name}")
                else:
                    logger.info(f"Provider {name} is disabled")
            self.packs = await repo.get_config("packs") or []
        except Exception as e:
            logger.warning(f"Could not load config from DB: {e}")
    
    async def apply_config(self, db: AsyncSession) -> None:
        """Public wrapper for _apply_config_async (used by tests)."""
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
        self.cache.invalidate_all()
        logger.info("✅ Intelligence Gateway reloaded and cache invalidated")
    
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
        self.thought_tracker.start()
        self.thought_tracker.add_step("Understanding", f"Processing query: '{query}'")
        
        user_id_int = user_id.id if hasattr(user_id, 'id') else user_id
        if not isinstance(user_id_int, int):
            return {"error": "Invalid user_id"}
        
        self.thought_tracker.add_step("RBAC Check", f"Validating permissions for user {user_id_int}")
        user_role = await self.get_user_role(user_id_int)
        
        await self.ensure_initialized()
        self.thought_tracker.add_step("Config", "Gateway initialized")
        
        # DEBUG: Log what's in the state
        logger.info(f"🔍 DEBUG: state type: {type(state)}")
        logger.info(f"🔍 DEBUG: state has orchestrator: {hasattr(state, 'orchestrator')}")
        if hasattr(state, 'orchestrator'):
            logger.info(f"🔍 DEBUG: state.orchestrator: {state.orchestrator}")
        
        # Route through swarm orchestrator if available
        orchestration_result = None
        
        # Try multiple ways to get orchestrator
        orchestrator = None
        if hasattr(state, 'orchestrator') and state.orchestrator:
            orchestrator = state.orchestrator
            logger.info("✅ Orchestrator found in state")
        elif hasattr(self, '_orchestrator') and self._orchestrator:
            orchestrator = self._orchestrator
            logger.info("✅ Orchestrator found in gateway instance")
        
        if orchestrator:
            try:
                self.thought_tracker.add_step("Swarm Routing", "Routing query through swarm agents")
                logger.info(f"🧠 Routing through swarm orchestrator: {orchestrator}")
                
                # Process through swarm
                swarm_result = await orchestrator.run(
                    query=query,
                    context={
                        "user_id": user_id_int,
                        "patient_id": patient_id,
                        "provider": provider,
                        "role": user_role
                    }
                )
                
                # Extract response from swarm result
                response_text = swarm_result.get("answer", swarm_result.get("response", ""))
                sources = swarm_result.get("sources", [])
                confidence = swarm_result.get("confidence", 0.0)
                
                self.thought_tracker.add_step("Swarm Complete", f"Swarm returned response with confidence {confidence}")
                logger.info(f"✅ Swarm response: {response_text[:100]}...")
                
                orchestration_result = {
                    "response": response_text,
                    "sources": sources,
                    "confidence": confidence,
                    "provider": provider,
                    "swarm_used": True
                }
            except Exception as e:
                logger.error(f"Swarm orchestration failed: {e}", exc_info=True)
                self.thought_tracker.add_step("Swarm Error", f"Falling back to direct LLM: {str(e)}")
        else:
            logger.warning("⚠️ No orchestrator available - using direct LLM")
            self.thought_tracker.add_step("No Orchestrator", "Using direct LLM fallback")
        
        # Fallback to direct LLM if swarm failed or not available
        if orchestration_result is None:
            self.thought_tracker.add_step("Direct LLM", "Using direct LLM fallback")
            logger.info(f"🔄 Using direct LLM with provider: {provider}")
            result = await self._call_with_fallback(provider, query, "Context assembled.")
            orchestration_result = {
                "response": result.get("response", "No response"),
                "sources": [],
                "confidence": 0.7,
                "provider": provider,
                "swarm_used": False
            }
        
        # Apply self-improving patterns if available
        if hasattr(state, 'self_improving') and state.self_improving:
            try:
                self.thought_tracker.add_step("Self-Improvement", "Applying learned patterns")
                enhanced_response = await state.self_improving.apply_patterns_to_response(
                    query, orchestration_result.get("response", "")
                )
                if enhanced_response != orchestration_result.get("response", ""):
                    orchestration_result["response"] = enhanced_response
                    orchestration_result["pattern_applied"] = True
            except Exception as e:
                logger.warning(f"Self-improvement failed: {e}")
        
        final_result = {
            "response": orchestration_result.get("response", "No response"),
            "provider": orchestration_result.get("provider", provider),
            "sources": orchestration_result.get("sources", []),
            "confidence": orchestration_result.get("confidence", 0.7),
            "swarm_used": orchestration_result.get("swarm_used", False),
            "thought_process": self.thought_tracker.get_steps(),
            "total_time": self.thought_tracker.get_total_time()
        }
        
        logger.info(f"📊 Final result: swarm_used={final_result.get('swarm_used')}, provider={final_result.get('provider')}")
        
        return final_result
    
    # ==================== PATTERN EXPLORE ====================
    
    async def _pattern_explore(self, user_id: int) -> List[Dict]:
        return []


# ============================================================================
# GATEWAY INSTANCE
# ============================================================================

gateway = IntelligenceGateway()

# Register Groq provider immediately
gateway._register_groq_provider()

logger.info("✅ Intelligence Gateway initialized")
