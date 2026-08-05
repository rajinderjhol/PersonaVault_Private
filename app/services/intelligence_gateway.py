# app/services/intelligence_gateway.py - COMPLETE 

"""
Unified Intelligence Gateway for PersonaVault. Handles ALL intelligence routing through MCP protocol.
This single file is designed to be clean, maintainable, and extensible.
"""

import json
import os
import re
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from pathlib import Path
from app.services.custom import PLASMA_ACTIVE, AGENT_STATUS

# ============================================================================
# SAFE IMPORTS - With fallbacks for Cloud Shell
# ============================================================================

# Try to import optional dependencies
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
    import asyncpg
    HAS_ASYNC_PG = True
except ImportError:
    HAS_ASYNC_PG = False
    asyncpg = None

try:
    import aiomysql
    HAS_ASYNC_MYSQL = True
except ImportError:
    HAS_ASYNC_MYSQL = False
    aiomysql = None

# SQLite is built-in
import sqlite3

logger = logging.getLogger(__name__)

# ============================================================================
# PART 1: MCP PROTOCOL IMPLEMENTATION
# ============================================================================

class MCPTool:
    """Model Context Protocol Tool - Pluggable intelligence source."""
    
    def __init__(self, name: str, description: str, handler: Callable, 
                 parameters: Dict[str, Any] = None):
        self.name = name
        self.description = description
        self.handler = handler
        self.parameters = parameters or {}

class MCPRegistry:
    """Registry for all MCP tools. ONE registry for everything."""
    
    _tools: Dict[str, MCPTool] = {}
    
    @classmethod
    def register(cls, tool: MCPTool):
        """Register a tool."""
        cls._tools[tool.name] = tool
        return tool
    
    @classmethod
    def get_tool(cls, name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        return cls._tools.get(name)
    
    @classmethod
    def list_tools(cls) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in cls._tools.values()
        ]
    
    @classmethod
    async def call(cls, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call a tool by name."""
        tool = cls.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        try:
            # Check if tool is async
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

# -------- 2.1: DATABASE TOOL (SQLite-only for Cloud Shell, extensible) --------
class DatabaseTool:
    """Connect to databases. SQLite by default, PostgreSQL/MySQL optional."""
    
    def __init__(self):
        self.connections = {}
        # Default SQLite connection
        self.connections["default"] = {
            "type": "sqlite",
            "path": "instance/personavault.db"
        }
    
    def register_connection(self, name: str, config: Dict[str, Any]):
        """Register a database connection."""
        self.connections[name] = config
    
    async def query(self, db_name: str, sql: str) -> List[Dict[str, Any]]:
        """Execute a query on a database."""
        config = self.connections.get(db_name)
        if not config:
            return [{"error": f"Database '{db_name}' not found"}]
        
        # SQLite (always works)
        if config["type"] == "sqlite":
            try:
                db_path = config.get("path", "storage/databases/pv.db")
                # Ensure directory exists
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(sql)
                results = cursor.fetchall()
                conn.close()
                return [dict(row) for row in results]
            except Exception as e:
                return [{"error": f"SQLite error: {str(e)}"}]
        
        # PostgreSQL (optional)
        elif config["type"] == "postgresql" and HAS_ASYNC_PG:
            try:
                conn = await asyncpg.connect(
                    host=config.get("host", "localhost"),
                    port=config.get("port", 5432),
                    user=config.get("user", "postgres"),
                    password=config.get("password", ""),
                    database=config.get("database", "postgres")
                )
                results = await conn.fetch(sql)
                await conn.close()
                return [dict(row) for row in results]
            except Exception as e:
                return [{"error": f"PostgreSQL error: {str(e)}"}]
        
        # MySQL (optional)
        elif config["type"] == "mysql" and HAS_ASYNC_MYSQL:
            try:
                pool = await aiomysql.create_pool(
                    host=config.get("host", "localhost"),
                    port=config.get("port", 3306),
                    user=config.get("user", "root"),
                    password=config.get("password", ""),
                    db=config.get("database", "mysql"),
                    minsize=1,
                    maxsize=5
                )
                async with pool.acquire() as conn:
                    async with conn.cursor(aiomysql.DictCursor) as cursor:
                        await cursor.execute(sql)
                        results = await cursor.fetchall()
                pool.close()
                await pool.wait_closed()
                return results
            except Exception as e:
                return [{"error": f"MySQL error: {str(e)}"}]
        
        return [{"error": f"Unsupported DB type: {config.get('type')}"}]

# -------- 2.2: EMAIL TOOL (IMAP) --------
class EmailTool:
    """Connect to customer's email (IMAP)."""
    
    def __init__(self):
        self.connections = {}
    
    def register_connection(self, name: str, config: Dict[str, Any]):
        self.connections[name] = config
    
    async def search(self, email_name: str, query: str) -> List[Dict[str, Any]]:
        """Search emails."""
        config = self.connections.get(email_name)
        if not config:
            return [{"error": f"Email '{email_name}' not found"}]
        
        try:
            import imaplib
            import email
            from email.header import decode_header
            
            imap = imaplib.IMAP4_SSL(
                config.get("host", "imap.gmail.com"),
                config.get("port", 993)
            )
            imap.login(config.get("user", ""), config.get("password", ""))
            imap.select("INBOX")
            
            _, message_ids = imap.search(None, f'BODY "{query}"')
            
            results = []
            for msg_id in message_ids[0].split()[:10]:
                _, msg_data = imap.fetch(msg_id, "(RFC822)")
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                subject, encoding = decode_header(email_message["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8", errors="ignore")
                
                results.append({
                    "id": msg_id.decode(),
                    "subject": subject,
                    "from": email_message["From"],
                    "date": email_message["Date"],
                    "body": self._get_email_body(email_message)[:500]
                })
            
            imap.close()
            imap.logout()
            return results
        except Exception as e:
            return [{"error": str(e)}]
    
    def _get_email_body(self, email_message):
        """Extract email body."""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode("utf-8", errors="ignore")
        else:
            return email_message.get_payload(decode=True).decode("utf-8", errors="ignore")
        return ""

# -------- 2.3: FILE TOOL --------
class FileTool:
    """Access customer's local files."""
    
    def __init__(self):
        self.index = {}
    
    def index_path(self, path: str, extensions: List[str] = None):
        """Index files in a path."""
        extensions = extensions or [".txt", ".md", ".pdf", ".docx"]
        path = os.path.expanduser(path)
        
        if not os.path.exists(path):
            return
        
        for root, dirs, files in os.walk(path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', errors='ignore') as f:
                            content = f.read(10000)
                            self.index[file_path] = {
                                "path": file_path,
                                "content": content,
                                "size": os.path.getsize(file_path),
                                "modified": os.path.getmtime(file_path)
                            }
                    except:
                        pass
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search indexed files."""
        results = []
        for path, data in self.index.items():
            if query.lower() in data["content"].lower():
                results.append({
                    "path": path,
                    "content": data["content"][:500] + "...",
                    "name": os.path.basename(path),
                    "score": self._calculate_score(query, data["content"]),
                    "modified": datetime.fromtimestamp(data["modified"]).isoformat()
                })
        return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]
    
    def _calculate_score(self, query: str, content: str) -> float:
        """Calculate relevance score."""
        query_words = query.lower().split()
        content_lower = content.lower()
        matches = sum(1 for word in query_words if word in content_lower)
        return matches / len(query_words) if query_words else 0.5

# -------- 2.4: WEB TOOL --------
class WebTool:
    """Search the web (optional)."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", False)
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search the web."""
        if not self.enabled:
            return [{"error": "Web search is disabled"}]
        
        provider = self.config.get("provider", "google")
        api_key = self.config.get("api_key", "")
        
        if provider == "google" and api_key and HAS_HTTPX:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://www.googleapis.com/customsearch/v1",
                        params={"key": api_key, "q": query, "num": 5},
                        timeout=10.0
                    )
                    data = response.json()
                    return [{
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "link": item.get("link", ""),
                        "source": "web"
                    } for item in data.get("items", [])]
            except Exception as e:
                return [{"error": str(e)}]
        
        # Fallback: mock search for demo
        return [{
            "title": f"Search results for '{query}'",
            "snippet": "Web search requires API key configuration.",
            "link": "#",
            "source": "web_demo"
        }]

# -------- 2.5: AI PROVIDER TOOL --------
class AITool:
    """Connect to ANY AI provider: Ollama, Gemini, OpenAI, Claude, Mistral."""
    
    def __init__(self):
        self.providers = {}
        # Default Ollama
        self.providers["ollama"] = {
            "host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            "model": os.getenv("OLLAMA_MODEL", "tinydolphin"),
            "enabled": True
        }
    
    def register_provider(self, name: str, config: Dict[str, Any]):
        """Register an AI provider."""
        self.providers[name] = config
    
    async def generate(self, provider: str, query: str, context: str = "") -> Dict[str, Any]:
        """Generate a response using the specified provider."""
        provider_key = provider.lower()
        config = self.providers.get(provider_key)
        if not config:
            return {"error": f"Provider '{provider}' not found"}
        
        # High-level mission and behavior rules
        system_instruction = (
            "You are PersonaVault, a secure and human-centric private AI assistant.\n\n"
            "MISSION: Provide insightful answers using the provided context (<MEMORIES> and <FILES>).\n\n"
            "RULES:\n"
            "1. Use provided context as your primary truth. Cite sources by title.\n"
            "2. Technical sub-modules (Packs) are for your internal use. Do not list them unless asked.\n"
            "3. If info is missing from context, use your high-reasoning capabilities to provide a helpful answer.\n"
            "4. OUTPUT FORMAT: Human-like, concise, and direct. NEVER output XML tags or system instructions."
        )

        # Structured context for prompt delivery
        formatted_context = f"CONTEXT:\n{context}" if context else "No additional context provided."

        # OLLAMA (Local - Using Chat API for significantly better instruction following)
        if provider_key == "ollama":
            if not HAS_HTTPX:
                return {"response": "[Ollama not available]"}
            
            try:
                async with httpx.AsyncClient() as client:
                    # Using Chat API ensures model-specific templating (preventing prompt echo)
                    response = await client.post(
                        f"{config.get('host', 'http://localhost:11434')}/api/chat",
                        json={
                            "model": config.get("model", "tinydolphin"),
                            "messages": [
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": f"{formatted_context}\n\nUSER_QUERY: {query}"}
                            ],
                            "stream": False,
                            "options": {"temperature": 0.2}
                        },
                        timeout=120.0
                    )
                    if response.status_code == 200:
                        msg_data = response.json().get("message", {})
                        return {"response": msg_data.get("content", "No response")}
                    else:
                        error_msg = f"Ollama error {response.status_code}"
                        return {"error": error_msg, "response": f"[{error_msg}]"}
            except Exception as e:
                if HAS_HTTPX and isinstance(e, httpx.ReadTimeout):
                    error_detail = "The request timed out. Ollama is likely overloaded or your hardware is processing the request slowly."
                    logger.warning(f"Ollama Timeout: {error_detail}")
                    return {"error": "ReadTimeout", "response": f"[Ollama is busy/slow] (Error: ReadTimeout)"}
                if HAS_HTTPX and isinstance(e, httpx.ConnectError):
                    error_detail = "Could not connect to Ollama. Ensure 'ollama serve' is running."
                    return {"error": "ConnectionError", "response": f"[Ollama unavailable] (Error: ConnectionError)"}
                error_detail = str(e) or e.__class__.__name__
                return {"error": f"Ollama connection failed: {error_detail}", "response": f"[Ollama unavailable] (Error: {error_detail})"}
        
        # GEMINI (Cloud - Requires API key)
        elif provider_key == "gemini" and not config.get("host"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=config.get("api_key"))
                model = genai.GenerativeModel(
                    model_name=config.get("model", "gemini-2.0-flash"),
                    system_instruction=system_instruction
                )
                response = await model.generate_content_async(f"{formatted_context}\n\nUSER_QUERY: {query}")
                return {"response": response.text}
            except ImportError:
                return {"error": "ImportError", "response": "[Gemini] Install google-generativeai: pip install google-generativeai"}
            except Exception as e:
                return {"error": f"Gemini error: {str(e)}", "response": f"[Gemini error] {str(e)}"}
        
        # OPENAI (Cloud - Requires API key)
        elif provider_key == "openai":
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(
                    api_key=config.get("api_key"),
                    base_url=config.get("host") if config.get("host") else None
                )
                response = await client.chat.completions.create(
                    model=config.get("model", "gpt-4o"),
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": f"{formatted_context}\n\nUSER_QUERY: {query}"}
                    ]
                )
                return {"response": response.choices[0].message.content}
            except ImportError:
                return {"error": "ImportError", "response": "[OpenAI] Install openai: pip install openai"}
            except Exception as e:
                return {"error": f"OpenAI error: {str(e)}", "response": f"[OpenAI error] {str(e)}"}
        
        # GROQ (Cloud - High speed inference)
        elif provider_key == "groq":
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(
                    api_key=config.get("api_key"),
                    base_url=config.get("host") or "https://api.groq.com/openai/v1"
                )
                response = await client.chat.completions.create(
                    model=config.get("model") or "llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": f"{formatted_context}\n\nUSER_QUERY: {query}"}
                    ]
                )
                return {"response": response.choices[0].message.content}
            except Exception as e:
                return {"error": f"Groq error: {str(e)}", "response": f"[Groq error] {str(e)}"}

        # GROK (Cloud - xAI)
        elif provider_key == "grok":
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(
                    api_key=config.get("api_key"),
                    base_url=config.get("host") or "https://api.x.ai/v1"
                )
                response = await client.chat.completions.create(
                    model=config.get("model") or "grok-beta",
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": f"{formatted_context}\n\nUSER_QUERY: {query}"}
                    ]
                )
                return {"response": response.choices[0].message.content}
            except Exception as e:
                return {"error": f"Grok error: {str(e)}", "response": f"[Grok error] {str(e)}"}

        # CLAUDE (Cloud - Requires API key)
        elif provider_key == "claude":
            try:
                from anthropic import AsyncAnthropic
                client = AsyncAnthropic(api_key=config.get("api_key"))
                response = await client.messages.create(
                    model=config.get("model", "claude-3-5-sonnet-20241022"),
                    max_tokens=1024,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": f"{formatted_context}\n\nUSER_QUERY: {query}"}
                    ]
                )
                return {"response": response.content[0].text}
            except ImportError:
                return {"error": "ImportError", "response": "[Claude] Install anthropic: pip install anthropic"}
            except Exception as e:
                return {"error": f"Claude error: {str(e)}", "response": f"[Claude error] {str(e)}"}
        
        # MISTRAL (Cloud - Requires API key)
        elif provider_key == "mistral":
            try:
                from mistralai import Mistral
                client = Mistral(api_key=config.get("api_key"))
                response = await client.chat.complete_async(
                    model=config.get("model", "mistral-large-latest"),
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": f"{formatted_context}\n\nUSER_QUERY: {query}"}
                    ]
                )
                return {"response": response.choices[0].message.content}
            except ImportError:
                return {"error": "ImportError", "response": "[Mistral] Install mistralai: pip install mistralai"}
            except Exception as e:
                return {"error": f"Mistral error: {str(e)}", "response": f"[Mistral error] {str(e)}"}
        
        # Generic OpenAI-compatible fallback for custom cloud providers
        if config.get("api_key") and config.get("host"):
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=config.get("api_key"), base_url=config.get("host"))
                response = await client.chat.completions.create(
                    model=config.get("model") or "gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": f"{formatted_context}\n\nUSER_QUERY: {query}"}
                    ]
                )
                return {"response": response.choices[0].message.content}
            except ImportError:
                return {"error": "ImportError", "response": f"[{provider_key}] OpenAI library missing. Install it with: pip install openai"}
            except Exception as e:
                return {"error": f"[{provider_key}] fallback error: {str(e)}", "response": f"[{provider_key} error] {str(e)}"}

        return {"response": f"[Unsupported provider: {provider}] (Query: {query[:100]}...)"}


# ============================================================================
# PART 3: THE UNIFIED GATEWAY
# ============================================================================

class IntelligenceGateway:
    """
    Unified Intelligence Gateway.
    ONE class that handles EVERYTHING.
    """
    
    def __init__(self):
        self.config = {}
        
        # Initialize all tools
        self.db_tool = DatabaseTool()
        self.email_tool = EmailTool()
        self.file_tool = FileTool()
        self.web_tool = WebTool()
        self.ai_tool = AITool()
        self.agent_tool = None
        self._initialized_from_db = False
        self.packs = []
        
        # Register tools with MCP
        self._register_mcp_tools()
        
        # Load configuration
        self._load_config()
    
    def _register_mcp_tools(self):
        """Register ALL tools with MCP protocol."""
        
        MCPRegistry.register(MCPTool(
            name="database_query",
            description="Query a connected database",
            parameters={"db_name": "string", "sql": "string"},
            handler=self.db_tool.query
        ))
        
        MCPRegistry.register(MCPTool(
            name="email_search",
            description="Search emails",
            parameters={"email_name": "string", "query": "string"},
            handler=self.email_tool.search
        ))
        
        MCPRegistry.register(MCPTool(
            name="file_search",
            description="Search local files",
            parameters={"query": "string", "limit": "integer"},
            handler=self.file_tool.search
        ))
        
        MCPRegistry.register(MCPTool(
            name="web_search",
            description="Search the web",
            parameters={"query": "string"},
            handler=self.web_tool.search
        ))
        
        MCPRegistry.register(MCPTool(
            name="ai_generate",
            description="Generate using any AI provider",
            parameters={"provider": "string", "query": "string", "context": "string"},
            handler=self.ai_tool.generate
        ))
        
        MCPRegistry.register(MCPTool(
            name="memory_search",
            description="Search PersonaVault memories",
            parameters={"user_id": "integer", "query": "string", "limit": "integer"},
            handler=self._memory_search
        ))
        
        MCPRegistry.register(MCPTool(
            name="pattern_explore",
            description="Explore learned patterns",
            parameters={"user_id": "integer"},
            handler=self._pattern_explore
        ))
    
    def _load_config(self):
        """Load configuration from file."""
        config_path = os.path.expanduser("storage/config/personavault.yaml")
        if os.path.exists(config_path) and HAS_YAML:
            try:
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
            except:
                self.config = {}
        
        # Apply configuration
        self._apply_config()
    
    def _apply_config(self):
        """Apply configuration to tools."""
        # Databases
        for name, db_config in self.config.get("databases", {}).items():
            if db_config.get("enabled", False):
                self.db_tool.register_connection(name, db_config)
        
        # Emails
        for name, email_config in self.config.get("emails", {}).items():
            if email_config.get("enabled", False):
                self.email_tool.register_connection(name, email_config)
        
        # Files
        for path_config in self.config.get("files", {}).get("paths", []):
            if path_config.get("enabled", False):
                self.file_tool.index_path(
                    path_config.get("path", "~"),
                    path_config.get("extensions", [".txt", ".md"])
                )
        
        # Web
        web_config = self.config.get("web", {})
        if web_config.get("enabled", False):
            self.web_tool.enabled = True
            self.web_tool.config = web_config
        
        # AI Providers
        for name, ai_config in self.config.get("ai_providers", {}).items():
            if ai_config.get("enabled", False):
                self.ai_tool.register_provider(name, ai_config)

        # Packs from config
        self.packs = self.config.get("packs") or []
        self._discover_local_packs()

    def _discover_local_packs(self):
        """Scan 'packs/' directory for additional packs."""
        packs_dir = Path("packs")
        if not packs_dir.exists():
            return
            
        for d in packs_dir.iterdir():
            if d.is_dir() and not d.name.startswith((".", "__")):
                # Aggressive semantic deduplication
                # Normalizes "contracts" -> "contract", "security" -> "security"
                stem = d.name.lower().rstrip('s')
                
                exists = False
                for p in self.packs:
                    name = p.get("name", "").lower()
                    domain = p.get("domain", "").lower()
                    if stem in name or stem in domain or name.startswith(stem):
                        exists = True
                        break
                
                if exists:
                    continue

                pack_data = {
                    "name": d.name.capitalize(),
                    "domain": d.name.capitalize(),
                    "version": "1.0.0",
                    "is_active": True,
                    "description": f"Intelligence pack discovered in packs/{d.name}"
                }

                # Try to load metadata if behaviour_pack.yaml exists in the folder
                meta_file = d / "behaviour_pack.yaml"
                if meta_file.exists() and HAS_YAML:
                    try:
                        with open(meta_file, 'r') as f:
                            meta = yaml.safe_load(f)
                            if meta: pack_data.update(meta)
                    except: pass
                
                self.packs.append(pack_data)
    
    async def test_provider_connection(self, provider: str, host: str = None, api_key: str = None, model: str = None) -> Dict[str, Any]:
        """Test connection to a specific AI provider without permanent registration."""
        provider_key = provider.lower()
        # Build temporary config for testing
        existing = self.ai_tool.providers.get(provider_key, {})
        test_config = {
            "host": host if host else existing.get("host"),
            "api_key": api_key if api_key else existing.get("api_key"),
            "enabled": True,
            "model": model if model else existing.get("model")
        }
        
        # Swap config temporarily
        original_config = self.ai_tool.providers.get(provider_key)
        self.ai_tool.providers[provider_key] = test_config
        
        try:
            # Use a minimal prompt to verify API key and connectivity
            result = await self.ai_tool.generate(provider_key, "Respond with 'Success'", "Connection Test")
            if "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, "response": result.get("response")}
        finally:
            # Restore original state
            if original_config: self.ai_tool.providers[provider] = original_config
            else: self.ai_tool.providers.pop(provider, None)

    async def reload_config(self):
        """Reload configuration from file and apply Database overrides."""
        logger.info("IntelligenceGateway: Reloading configuration...")
        self._load_config()
        
        # 0. Load from Environment Variables (Prioritize .env for persistence)
        for provider in ["gemini", "openai", "claude", "mistral", "grok", "groq"]:
            env_key = os.getenv(f"AI_PROVIDER_{provider.upper()}_API_KEY")
            if env_key:
                if provider not in self.ai_tool.providers:
                    self.ai_tool.providers[provider] = {}
                self.ai_tool.providers[provider]["api_key"] = env_key
                self.ai_tool.providers[provider]["enabled"] = True
                # Load optional Host and Model overrides from environment
                for setting in ["host", "model"]:
                    val = os.getenv(f"AI_PROVIDER_{provider.upper()}_{setting.upper()}")
                    if val: self.ai_tool.providers[provider][setting] = val

        # Apply Database Overrides
        try:
            from app.db.session import SessionLocal
            from app.models import SystemConfig
            from sqlalchemy import select
            
            async with SessionLocal() as db:
                # 1. Load Primary Provider Override
                stmt_primary = select(SystemConfig).where(SystemConfig.key == "primary_ai_provider")
                res_primary = await db.execute(stmt_primary)
                primary_cfg = res_primary.scalars().first()
                if primary_cfg:
                    if "router" not in self.config: self.config["router"] = {}
                    self.config["router"]["primary_override"] = primary_cfg.value
                
                # 2. Load Specific Provider Settings (Host/API Key)
                stmt = select(SystemConfig).where(SystemConfig.key.like("ai_provider_%"))
                result = await db.execute(stmt)
                configs = result.scalars().all()
                
                for cfg in configs:
                    parts = cfg.key.split('_')
                    if len(parts) >= 4:
                        p_name = parts[2].lower()
                        setting = "_".join(parts[3:]) # host, api_key, enabled
                        
                        if p_name not in self.ai_tool.providers:
                            self.ai_tool.providers[p_name] = {}
                        
                        if setting == "enabled":
                            self.ai_tool.providers[p_name]["enabled"] = cfg.value.lower() == "true"
                        else:
                            self.ai_tool.providers[p_name][setting] = cfg.value
                            self.ai_tool.providers[p_name]["enabled"] = True
                
                self._initialized_from_db = True
                logger.info("IntelligenceGateway: DB overrides applied")
        except Exception as e:
            logger.error(f"IntelligenceGateway: DB override failed: {e}")
    
    async def chat(self, user_id: int, query: str, state: Any = None) -> Dict[str, Any]:
        """
        Main chat endpoint.
        Routes to appropriate intelligence based on configuration.
        """
        # Lazy-load DB config on first chat if not already done (avoids startup circular imports)
        if not self._initialized_from_db:
            await self.reload_config()

        # Ensure user_id is an integer PK even if an object was passed
        user_id_int = user_id.id if hasattr(user_id, 'id') else user_id
        
        PLASMA_ACTIVE.set(1)
        if state and hasattr(state, "blackboard"):
            await state.blackboard.post_insight("Gateway", {"event": "query_received", "query": query}, importance=0.9)
            
        # Simple Empathy Simulation (Priority 3)
        if state and hasattr(state, "empathy_agent"):
            mood, tone = ("Concerned", "Serious") if any(x in query.lower() for x in ["urgent", "help", "error"]) else ("Calm", "Supportive")
            setattr(state.empathy_agent, "last_mood", mood)
            setattr(state.empathy_agent, "last_tone", tone)

        # Track individual agent activation (Priority 2)
        self._set_agent_active("planner", True)

        # 1. Mask PII
        masked_query, mapping = self._mask_pii(query)
        
        # 2. Gather context from ALL sources
        context = await self._gather_context(user_id_int, masked_query)
        self._set_agent_active("planner", False)
        self._set_agent_active("retriever", True)
        if state and hasattr(state, "blackboard") and context.get("sources"):
            await state.blackboard.post_insight("Retriever", {"event": "context_retrieved", "source_count": len(context["sources"])}, importance=0.6)
        self._set_agent_active("retriever", False)
        
        # 3. Choose provider
        self._set_agent_active("router", True)
        provider = self._choose_provider(masked_query, context).lower()
        self._set_agent_active("router", False)
        
        # 4. Generate response
        # Optimization: If using a local model, keep the combined context to a reasonable length
        combined_context = context.get("combined", "")
        if provider == "ollama" and len(combined_context) > 4000:
            # Trim context to prevent ReadTimeout on small models
            logger.info("Gateway: Trimming context for local Ollama request to improve performance.")
            combined_context = combined_context[:4000] + "... [Context trimmed for performance]"

        self._set_agent_active("generator", True)
        result = await MCPRegistry.call(
            "ai_generate",
            provider=provider,
            query=masked_query,
            context=combined_context
        )
        
        if not result.get("success"):
            response = f"Error calling AI: {result.get('error')}"
        else:
            res_data = result.get("result", {})
            response = res_data.get("response") or (f"Error: {res_data.get('error')}" if "error" in res_data else "No response")
            
            # UX FIX: Final sanitation to strip common prompt-leaks or hallucinated tags
            # Especially important for very small models that echo headers.
            leak_patterns = [
                r'<(?:CONTEXT|USER_QUERY|ASSISTANT_RESPONSE|SYSTEM_INSTRUCTION|MEMORIES|FILES|CAPABILITIES|LEARNED_PATTERNS)>',
                r'(?:USER_QUERY|ASSISTANT_RESPONSE|CONTEXT):',
                r'^\s*ASSISTANT_RESPONSE\s*$'
            ]
            for pattern in leak_patterns:
                response = re.sub(pattern, '', response, flags=re.IGNORECASE | re.MULTILINE)
            response = response.strip()
            
        self._set_agent_active("generator", False)
        
        self._set_agent_active("judge", True)
        if state and hasattr(state, "blackboard"):
             await state.blackboard.post_insight("Judge", {"event": "evaluation_complete", "confidence": self._calculate_confidence(provider, context)}, importance=0.8)
        self._set_agent_active("judge", False)

        # 5. Unmask response
        unmasked_response = self._unmask_pii(response, mapping)
        
        # 6. Learn from interaction (simple version)
        self._set_agent_active("episodic", True)
        await self._learn_from_interaction(user_id_int, query, unmasked_response, context)
        self._set_agent_active("episodic", False)
        
        PLASMA_ACTIVE.set(0)
        # 7. Return response
        return {
            "response": unmasked_response,
            "provider": provider,
            "sources": context.get("sources", []),
            "thought_chain": [],
            "confidence": self._calculate_confidence(provider, context),
            "patterns": []
        }
    
    def _set_agent_active(self, agent_name: str, active: bool):
        """Track individual agent activation state for the telemetry layer."""
        try:
            AGENT_STATUS.labels(agent_name=agent_name).set(1 if active else 0)
        except Exception:
            pass

    # ============ DOCUMENT SEARCH ============
    async def _search_documents(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """Search uploaded documents."""
        try:
            from app.db.session import SessionLocal
            from app.models import Memory
            from sqlalchemy import select
            
            async with SessionLocal() as db:
                stmt = select(Memory).where(
                    Memory.user_id == user_id,
                    Memory.modality == "document",
                    Memory.content.ilike(f"%{query}%")
                ).limit(limit)
                result = await db.execute(stmt)
                documents = result.scalars().all()
                
                return [{
                    "id": d.id,
                    "content": d.content,
                    "title": d.title,
                    "tags": d.tags,
                    "score": 0.7,
                    "modality": "document"
                } for d in documents]
        except Exception as e:
            logger.error(f"Document search error: {e}")
            return []

    async def _gather_context(self, user_id: int, query: str) -> Dict[str, Any]:
        """Gather context from ALL sources using MCP tools."""
        context = {
            "memories": [],
            "files": [],
            "emails": [],
            "database": [],
            "web": [],
            "sources": [],
            "combined": ""
        }
        
        # 1. Local memories
        memory_result = await MCPRegistry.call("memory_search", user_id=user_id, query=query, limit=5)
        if memory_result.get("success"):
            context["memories"] = memory_result["result"]
            context["sources"].extend([{"type": "memory", "id": m.get("id"), "title": m.get("title")} for m in memory_result["result"]])
        
        # 2. Local files
        file_result = await MCPRegistry.call("file_search", query=query, limit=3)
        if file_result.get("success"):
            context["files"] = file_result["result"]
            context["sources"].extend([{"type": "file", "path": f.get("path"), "title": f.get("name")} for f in file_result["result"]])
        
        # 3. Documents
        doc_result = await self._search_documents(user_id, query, limit=3)
        if doc_result:
            context["documents"] = doc_result
            context["sources"].extend([{"type": "document", "id": d.get("id"), "title": d.get("title")} for d in doc_result])
        
        # 4. Intelligent Context Assembly
        context_parts = []
        if context["memories"]:
            logs = [m for m in context["memories"] if m.get("tags") and "interaction_log" in m.get("tags")]
            facts = [m for m in context["memories"] if not m.get("tags") or "interaction_log" not in m.get("tags")]
            
            if facts:
                context_parts.append("<MEMORIES>\n" + "\n".join([f"- [{m.get('title')}]: {m.get('content')}" for m in facts]) + "\n</MEMORIES>")
            if logs and any(k in query.lower() for k in ["history", "learned", "learnt", "interaction", "previous"]):
                context_parts.append("<CHAT_HISTORY>\n" + "\n".join([f"- {m.get('content')}" for m in logs]) + "\n</CHAT_HISTORY>")

        if context["files"]:
            context_parts.append("<FILES>\n" + "\n".join([f"- [{f.get('name')}]: {f.get('content', '')[:500]}" for f in context["files"]]) + "\n</FILES>")

        if context.get("documents"):
            context_parts.append("<DOCUMENTS>\n" + "\n".join([f"- [{d.get('title')}]: {d.get('content', '')[:500]}" for d in context["documents"]]) + "\n</DOCUMENTS>")

        # 5. Only inject capabilities if the query is about the system
        active_packs = [p for p in self.packs if p.get("is_active")]
        system_keywords = ["help", "capabilities", "you do", "tools", "packs", "features", "can you", "what can you", "what do you", "how do you", "your abilities"]
        
        if active_packs and any(kw in query.lower() for kw in system_keywords):
            pack_context = "<CAPABILITIES>\n"
            for p in active_packs:
                pack_context += f"- {p.get('name')} ({p.get('domain')}): {p.get('description')}\n"
            pack_context += "</CAPABILITIES>"
            context_parts.append(pack_context)
            logger.info(f"✅ Injected capabilities because query contained system keywords: {query[:50]}...")
        else:
            logger.info(f"⏭️ Skipped capabilities injection for query: {query[:50]}...")

        # 6. Learned Patterns
        pattern_result = await MCPRegistry.call("pattern_explore", user_id=user_id)
        if pattern_result.get("success") and pattern_result.get("result"):
            context["patterns"] = pattern_result["result"]
            p_text = "<LEARNED_PATTERNS>\n"
            for p in context["patterns"]:
                p_text += f"- If '{p.get('trigger')}', use correction: '{p.get('correction')}'\n"
            p_text += "</LEARNED_PATTERNS>"
            context_parts.append(p_text)

        context["combined"] = "\n\n".join(context_parts)
        return context
    
    def _choose_provider(self, query: str, context: Dict) -> str:
        """Choose the best intelligence provider."""
        db_primary = self.config.get("router", {}).get("primary_override", "ollama").lower().strip()
        
        if db_primary != "ollama":
            if self.ai_tool.providers.get(db_primary, {}).get("enabled"):
                return db_primary

        strategy = self.config.get("router", {}).get("strategy", "hybrid")
        
        if strategy == "local":
            return "ollama"
        
        word_count = len(query.split())
        if context["memories"] and word_count < 10:
            return "ollama"
        
        if strategy == "hybrid" and (word_count > 12 or any(word in query.lower() for word in ["analyze", "compare", "evaluate", "explain", "how to", "what is"])):
            for p_name in ["groq", "grok", "gemini", "openai", "claude", "mistral"]:
                if self.ai_tool.providers.get(p_name, {}).get("enabled"):
                    return p_name
            
            for p_name, p_cfg in self.ai_tool.providers.items():
                if p_name != "ollama" and p_cfg.get("enabled"):
                    return p_name
        
        return "ollama"
    
    def _mask_pii(self, text: str) -> tuple[str, dict]:
        """Mask PII in text and return the mapping for restoration."""
        patterns = {
            "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "phone": r'\+?1?\d{9,15}',
            "ssn": r'\d{3}-\d{2}-\d{4}',
            "ip": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        }
        
        masked = text
        mapping = {}
        for pii_type, pattern in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                pii_value = match.group()
                mask_id = f"[PII_{pii_type}_{len(mapping)}]"
                mapping[mask_id] = pii_value
                masked = masked.replace(pii_value, mask_id)
        
        return masked, mapping
    
    def _unmask_pii(self, text: str, mapping: dict) -> str:
        """Unmask PII in text."""
        unmasked = text
        for mask_id, pii_value in mapping.items():
            unmasked = unmasked.replace(mask_id, pii_value)
        return unmasked
    
    async def _learn_from_interaction(self, user_id: int, query: str, response: str, context: Dict):
        """Learn from every interaction and persist to episodic memory logs."""
        if response.startswith("[Ollama") or response.startswith("Error:") or "unavailable" in response.lower():
            return
            
        try:
            from app.db.session import SessionLocal
            from app.models import Memory
            async with SessionLocal() as db:
                log_entry = Memory(
                    user_id=user_id,
                    title=f"Chat Episode: {query[:30]}...",
                    content=f"User: {query}\nAI: {response}",
                    tags="interaction_log",
                    modality="text"
                )
                db.add(log_entry)
                await db.commit()
        except Exception as e:
            logger.error(f"Gateway learning failure: {e}")
    
    async def _memory_search(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """Search memories."""
        try:
            from app.db.session import SessionLocal
            from app.models import Memory
            from sqlalchemy import select
            
            async with SessionLocal() as db:
                if any(word in query.lower() for word in ["learnt", "learned", "interaction", "about me", "history", "recent"]):
                    stmt = select(Memory).where(
                        Memory.user_id == user_id,
                        Memory.tags == "interaction_log"
                    ).order_by(Memory.id.desc()).limit(limit)
                else:
                    stmt = select(Memory).where(
                        Memory.user_id == user_id,
                        Memory.content.ilike(f"%{query}%")
                    ).limit(limit)
                    
                result = await db.execute(stmt)
                memories = result.scalars().all()
                return [{"id": m.id, "content": m.content, "title": m.title, "tags": m.tags, "score": 0.5} for m in memories]
        except Exception:
            return []
    
    async def _pattern_explore(self, user_id: int) -> List[Dict]:
        """Explore learned patterns."""
        try:
            from app.models import SemanticPattern
            from app.db.session import SessionLocal
            from sqlalchemy import select
            
            async with SessionLocal() as db:
                stmt = select(SemanticPattern).where(
                    SemanticPattern.is_active == True
                ).order_by(SemanticPattern.weight.desc()).limit(20)
                result = await db.execute(stmt)
                patterns = result.scalars().all()
                
                return [{
                    "trigger": p.trigger,
                    "correction": p.correction,
                    "weight": p.weight,
                    "success_count": p.success_count,
                    "is_active": p.is_active
                } for p in patterns]
        except Exception:
            return []
    
    def _calculate_confidence(self, provider: str, context: Dict) -> float:
        """Calculate confidence score."""
        base_confidence = {
            "ollama": 0.7,
            "gemini": 0.9,
            "openai": 0.85,
            "claude": 0.88,
            "mistral": 0.83
        }
        
        confidence = base_confidence.get(provider, 0.7)
        
        if len(context.get("memories", [])) > 2:
            confidence += 0.05
        if context.get("combined"):
            confidence += 0.05
        
        return min(confidence, 1.0)


# ============================================================================
# PART 4: FASTAPI INTEGRATION - Add to main.py
# ============================================================================

# To integrate with FastAPI, add these routes in main.py:
#
# from app.services.intelligence_gateway import gateway, MCPRegistry
#
# @app.post("/api/v1/chat")
# async def chat(request: ChatRequest, user_id: int = Depends(get_current_user)):
#     result = await gateway.chat(user_id, request.query)
#     return result
#
# @app.get("/api/v1/mcp/tools")
# async def list_tools():
#     return {"tools": MCPRegistry.list_tools()}

# Initialize gateway instance
gateway = IntelligenceGateway()

# Print status on import
print(f"✅ Intelligence Gateway initialized")
print(f"   - Providers: {list(gateway.ai_tool.providers.keys())}")
print(f"   - Files indexed: {len(gateway.file_tool.index)}")
print(f"   - MCP Tools: {len(MCPRegistry.list_tools())}")
