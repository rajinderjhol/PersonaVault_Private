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

# Suppress the specific FutureWarning from the legacy google-generativeai package
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
        # Safely access model name with fallback to environment or default
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
        """Fetch the current primary provider from database with environment fallback."""
        try:
            from app.db.session import SessionLocal # Using the FastAPI-style session
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
        persona: Any = None, # User persona from Layer 3
        response_tone: str = "neutral", # From EmpathyAgent
        hitl_approved: bool = False
    ) -> Dict[str, Any]:
        """Generate content based on routing decision, reasoning, and context."""
        prompt = self._build_prompt(query, context, reasoning_insight, situational_awareness, persona)
        
        # 1. Attempt the provider suggested by the AIRouter
        result = None
        if route and "provider" in route:
            provider = route["provider"]
            logger.info(f"GeneratorAgent: Routing to {provider} as requested by AIRouter")
            
            if provider == "ollama":
                result = await self._try_ollama(prompt)
            elif provider == "gemini":
                result = await self._try_gemini(prompt)
            
            if result:
                if hitl_approved:
                    result["hitl_approved"] = True
                return result

        # 2. Dynamic Fallback: If route failed or wasn't provided, follow configured search order
        primary = await self._get_primary_provider()
        # Exclude the provider we already tried via route to avoid redundant calls
        providers = ["ollama", "gemini"] if primary == "ollama" else ["gemini", "ollama"]
        
        for provider in providers:
            if route and route.get("provider") == provider:
                continue

            if provider == "ollama":
                result = await self._try_ollama(prompt)
            elif provider == "gemini":
                result = await self._try_gemini(prompt)
            
            if result:
                if hitl_approved:
                    result["hitl_approved"] = True
                return result
        
        # 3. Final Synthesis Fallback
        logger.info("Falling back to template-based generation")
        result = self._fallback_generate(query, context)
        if hitl_approved:
            result["hitl_approved"] = True
        return result
    
    async def _try_ollama(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Internal helper to attempt generation via Ollama."""
        try:
            logger.info(f"Attempting generation with Ollama ({self.ollama_model})...")
            res = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
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
            logger.warning(f"Ollama generation failed or unreachable: {e}")
        return None
    
    async def _try_gemini(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Internal helper to attempt generation via Gemini."""
        if not self.gemini_key:
            return None
        
        try:
            logger.info("Attempting generation with Gemini...")
            if HAS_NEW_GEMINI:
                # New SDK is natively built with modern patterns
                # Wrapped in to_thread to ensure it remains non-blocking
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
        situational_awareness: Dict[str, Any] = None, # From Layer 1
        response_tone: str = "neutral", # From EmpathyAgent
        persona: Any = None
    ) -> str:
        """Constructs a structured prompt for the LLM."""
        reasoning_str = f"\nREASONING INSIGHTS:\n{reasoning_insight}\n" if reasoning_insight else ""
        
        # Extract template from context
        template = ""
        if context and len(context) > 0:
            item = context[0]
            if hasattr(item, 'content'):
                template = item.content
            elif isinstance(item, dict):
                template = item.get("content", "")
            else:
                template = str(item)
        
        # Format grounding data
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

{reasoning_str}

INSTRUCTIONS:
{query}
TEMPLATE:
{template}
Please generate a complete and professional document based on the instructions above.
Replace any placeholders in the template with appropriate content.
"""
        return prompt.strip()
    
    def _fallback_generate(self, query: str, context: List[Any]) -> Dict[str, Any]:
        """Generate a fallback response when AI is unavailable."""
        # Extract template from context
        template = ""
        if context and len(context) > 0:
            item = context[0]
            if hasattr(item, 'content'):
                template = item.content
            elif isinstance(item, dict):
                template = item.get("content", "")
            else:
                template = str(item)
        
        # Extract placeholders
        placeholders = re.findall(r'\{([^}]+)\}', template)
        
        # Generate sample values
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
        
        # Replace placeholders
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
