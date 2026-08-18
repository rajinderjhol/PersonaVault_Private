import logging
import os
import asyncio
import httpx
import json
from typing import List, Dict, Any, Optional, Union
import re
from sqlalchemy import select
from app.config import Config
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", message=".*google.generativeai.*")
warnings.filterwarnings("ignore", category=FutureWarning)

logger = logging.getLogger(__name__)

try:
    from google import genai
    HAS_NEW_GEMINI = True
    HAS_LEGACY_GEMINI = False
except ImportError:
    HAS_NEW_GEMINI = False
    try:
        import google.generativeai as genai
        HAS_LEGACY_GEMINI = True
    except ImportError:
        HAS_LEGACY_GEMINI = False

class GeneratorAgent:
    """
    Synthesizes answers using a tiered approach:
    1. Ollama (Local - Default Priority)
    2. Gemini (Cloud - Fallback/Secondary)
    3. Template-based Fallback (Deterministic)
    """
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.ollama_url = Config.OLLAMA_BASE_URL
        self.ollama_model = getattr(Config, "OLLAMA_LLM_MODEL", os.getenv("OLLAMA_LLM_MODEL", "tinydolphin"))
        self.client = client or httpx.AsyncClient()
        
        if self.gemini_key:
            if HAS_NEW_GEMINI:
                self.genai_client = genai.Client(api_key=self.gemini_key)
                logger.info("GeneratorAgent: New Gemini AI SDK initialized")
            elif HAS_LEGACY_GEMINI:
                genai.configure(api_key=self.gemini_key)
                logger.info("GeneratorAgent: Legacy Gemini AI SDK initialized")
  
        logger.info("GeneratorAgent initialized")
    
    async def _get_primary_provider(self) -> str:
        try:
            from app.db.session import SessionLocal
            from app.models import SystemConfig
            
            async with SessionLocal() as session:
                stmt = select(SystemConfig).where(SystemConfig.key == "primary_ai_provider")
                result = await session.execute(stmt)
                config = result.scalars().first()
                if config:
                    return config.value.lower()
        except Exception as e:
            logger.error(f"Error accessing database: {e}")
        
        return os.getenv("AI_PRIMARY_PROVIDER", "ollama").lower()
    
    async def generate(
        self, 
        query: str, 
        context: List[Any] = None, 
        reasoning_insight: Any = None,
        route: Dict[str, Any] = None,
        situational_awareness: Dict[str, Any] = None,
        persona: Any = None,
        response_tone: str = "neutral",
        hitl_approved: bool = False
    ) -> Dict[str, Any]:
        prompt = self._build_prompt(query, context, reasoning_insight, situational_awareness, persona)
        
        result = None
        if route and "provider" in route:
            provider = route["provider"]
            logger.info(f"GeneratorAgent: Routing to {provider} as requested")
            
            if provider == "ollama":
                result = await self._try_ollama(prompt)
            elif provider == "groq":
                result = await self._try_groq(prompt)
            elif provider == "gemini":
                result = await self._try_gemini(prompt)
            
            if result:
                if hitl_approved:
                    result["hitl_approved"] = True
                return result

        primary = await self._get_primary_provider()
        providers = ["ollama", "groq", "gemini"]
        if primary in providers:
            providers.remove(primary)
            providers.insert(0, primary)
        
        for provider in providers:
            if route and route.get("provider") == provider:
                continue

            if provider == "ollama":
                result = await self._try_ollama(prompt)
            elif provider == "groq":
                result = await self._try_groq(prompt)
            elif provider == "gemini":
                result = await self._try_gemini(prompt)
            
            if result:
                if hitl_approved:
                    result["hitl_approved"] = True
                return result
        
        logger.info("Falling back to template-based generation")
        result = self._fallback_generate(query, context)
        if hitl_approved:
            result["hitl_approved"] = True
        return result
    
    async def _try_ollama(self, prompt: str) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"Attempting generation with Ollama ({self.ollama_model})...")
            res = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=30.0
            )
            if res.status_code == 200:
                response_text = res.json().get("response", "").strip()
                if response_text:
                    return {
                        "answer": response_text,
                        "source": "ollama",
                        "confidence": 0.85
                    }
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
        return None
    
    async def _try_groq(self, prompt: str) -> Optional[Dict[str, Any]]:
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            logger.warning("GROQ_API_KEY not set")
            return None
        
        try:
            # Get the model from database or use default
            model = "qwen/qwen3.6-27b"
            try:
                from app.db.session import SessionLocal
                from app.models import SystemConfig
                import json
                
                async with SessionLocal() as session:
                    stmt = select(SystemConfig).where(SystemConfig.key == "ai_providers")
                    result = await session.execute(stmt)
                    config = result.scalars().first()
                    if config:
                        ai_config = json.loads(config.value)
                        if "groq" in ai_config and "model" in ai_config["groq"]:
                            model = ai_config["groq"]["model"]
            except Exception as e:
                logger.warning(f"Could not load Groq model from DB: {e}")
            
            logger.info(f"Attempting generation with Groq (model: {model})...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 500
                    }
                )
                
                if res.status_code == 200:
                    response_text = res.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if response_text:
                        return {
                            "answer": response_text,
                            "source": "groq",
                            "confidence": 0.92
                        }
                else:
                    logger.error(f"Groq API error: {res.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            return None
    
    async def _try_gemini(self, prompt: str) -> Optional[Dict[str, Any]]:
        if not self.gemini_key:
            return None
        
        try:
            logger.info("Attempting generation with Gemini...")
            if HAS_NEW_GEMINI:
                response = await asyncio.to_thread(
                    self.genai_client.models.generate_content,
                    model='gemini-2.0-flash-exp', 
                    contents=prompt
                )
                text = response.text
            elif HAS_LEGACY_GEMINI:
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                response = await asyncio.to_thread(model.generate_content, prompt)
                text = response.text
            else:
                return None

            if text:
                return {"answer": text.strip(), "source": "gemini", "confidence": 0.95}
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
        return None
    
    def _build_prompt(
        self, 
        query: str, 
        context: List[Any], 
        reasoning_insight: Any = None,
        situational_awareness: Dict[str, Any] = None,
        response_tone: str = "neutral",
        persona: Any = None
    ) -> str:
        """Constructs a structured prompt for the LLM with memory context."""
        reasoning_str = f"\nREASONING INSIGHTS:\n{reasoning_insight}\n" if reasoning_insight else ""
        
        # Format memory context
        memory_context = ""
        if context and len(context) > 0:
            memory_context = "RELEVANT MEMORIES:\n"
            for i, item in enumerate(context):
                if hasattr(item, 'content'):
                    content = item.content
                elif isinstance(item, dict):
                    content = item.get("content", "")
                else:
                    content = str(item)
                
                if content:
                    memory_context += f"{i+1}. {content}\n"
        
        # Template (for document generation)
        template = ""
        if context and len(context) > 0:
            item = context[0]
            if hasattr(item, 'content'):
                template = item.content
            elif isinstance(item, dict):
                template = item.get("content", "")
            else:
                template = str(item)
        
        awareness_str = json.dumps(situational_awareness) if situational_awareness else "No real-time context available."
        writing_style = persona.writing_style if persona else "balanced"
        comm_style = persona.communication_style if persona else "casual"
        
        prompt = f"""
USER PERSONA:
Writing Style: {writing_style}
Communication Style: {comm_style}
Response Tone: {response_tone}

CURRENT SITUATIONAL AWARENESS:
{awareness_str}

{memory_context}

{reasoning_str}

USER QUERY:
{query}

TEMPLATE:
{template}

Instructions:
- Use the RELEVANT MEMORIES as your primary source of truth.
- If memories provide specific information, use it directly in your response.
- If information is missing from memories, use your reasoning to provide general guidance.
- Be concise, direct, and human-like in your response.
- If the user asks about specific data and it's in the memories, reference it.
- Format your response clearly with bullet points or numbered lists when helpful.
"""
        return prompt.strip()
    
    def _fallback_generate(self, query: str, context: List[Any]) -> Dict[str, Any]:
        template = ""
        if context and len(context) > 0:
            item = context[0]
            if hasattr(item, 'content'):
                template = item.content
            elif isinstance(item, dict):
                template = item.get("content", "")
            else:
                template = str(item)
        
        placeholders = re.findall(r'\{([^}]+)\}', template)
        variables = {}
        for p in placeholders:
            if "name" in p.lower() or "client" in p.lower():
                variables[p] = "Acme Corporation"
            elif "company" in p.lower():
                variables[p] = "Security Tech Inc"
            elif "purpose" in p.lower():
                variables[p] = "biometric authentication services"
            elif "terms" in p.lower():
                variables[p] = "standard terms and conditions"
            else:
                variables[p] = f"[{p}]"
        
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        
        final_result = f"""
INSTRUCTIONS:
{query}

DRAFT DOCUMENT:
{result}
"""
        
        return {
            "answer": final_result.strip(),
            "source": "fallback",
            "warning": "Running in Cloud Shell mode - using template-based generation"
        }
