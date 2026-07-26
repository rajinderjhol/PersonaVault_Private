import logging
from typing import Dict, Any, Optional
import httpx
import json
from app.config import Config

logger = logging.getLogger(__name__)

class EmpathyAgent:
    """
    Interprets Layer 1 situational awareness data (e.g., mood sensors, environment)
    to determine an appropriate response tone for the GeneratorAgent.
    """
    def __init__(self, ollama_url: Optional[str] = None, client: Optional[httpx.AsyncClient] = None, session_factory: Optional[Any] = None):
        self.ollama_url = ollama_url or Config.OLLAMA_BASE_URL
        self.ollama_model = Config.OLLAMA_REASONER_MODEL  # Using reasoner model for interpretation
        self._client = client or httpx.AsyncClient(timeout=30.0)
        self.last_mood = "unknown"
        self.last_tone = "neutral"
        self.session_factory = session_factory

    async def _persist_state(self):
        """Helper to save last mood/tone to system_configs database lattice."""
        if not self.session_factory:
            return
        try:
            async with self.session_factory() as db:
                from sqlalchemy import select
                from app.models import SystemConfig
                
                for key, value in [("last_empathy_mood", self.last_mood), ("last_empathy_tone", self.last_tone)]:
                    stmt = select(SystemConfig).where(SystemConfig.key == key)
                    res = await db.execute(stmt)
                    cfg = res.scalars().first()
                    if cfg:
                        cfg.value = str(value)
                    else:
                        db.add(SystemConfig(key=key, value=str(value)))
                await db.commit()
        except Exception as e:
            logger.warning(f"EmpathyAgent: Failed to persist state: {e}")

    async def determine_tone(self, situational_awareness: Dict[str, Any]) -> str:
        """
        Analyzes situational awareness data and returns a suggested response tone.
        Uses an LLM for interpretation, with a rule-based fallback.
        """
        if not situational_awareness:
            self.last_mood = "none"
            self.last_tone = "neutral"
            await self._persist_state()
            return "neutral"

        self.last_mood = situational_awareness.get("mood", "unknown")

        # Construct a prompt for the LLM to interpret the situational awareness
        prompt = f"""
        Analyze the following real-time situational awareness data and suggest an appropriate response tone for an AI.
        The tone should be one of the following: "calming and reassuring", "patient and understanding", "enthusiastic and supportive", "empathetic and comforting", or "neutral and informative".
        
        Situational Awareness Data:
        {json.dumps(situational_awareness, indent=2)}
        
        Based on this data, what is the most suitable response tone?
        Provide only the tone, no additional text.
        """
        
        try:
            res = await self._client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2} # Lower temperature for more consistent tone
                },
                timeout=10.0
            )
            if res.status_code == 200:
                llm_response = res.json().get("response", "").strip().lower()
                # Simple keyword matching for now, can be improved with more robust parsing
                tone = "neutral and informative"
                if "calming" in llm_response or "reassuring" in llm_response: tone = "calming and reassuring"
                elif "patient" in llm_response or "understanding" in llm_response: tone = "patient and understanding"
                elif "enthusiastic" in llm_response or "supportive" in llm_response: tone = "enthusiastic and supportive"
                elif "empathetic" in llm_response or "comforting" in llm_response: tone = "empathetic and comforting"
                
                self.last_tone = tone
                await self._persist_state()
                return tone
        except Exception as e:
            logger.warning(f"EmpathyAgent: LLM tone determination failed: {e}. Falling back to rule-based.")
            # Fallback to simple rule-based if LLM fails
            mood = situational_awareness.get("mood", "neutral").lower()
            tone = "neutral and informative"
            if "stressed" in mood or "anxious" in mood: tone = "calming and reassuring"
            elif "frustrated" in mood or "angry" in mood: tone = "patient and understanding"
            elif "happy" in mood or "excited" in mood: tone = "enthusiastic and supportive"
            elif "sad" in mood or "lonely" in mood: tone = "empathetic and comforting"
            
            self.last_tone = tone
            await self._persist_state()
            return tone

        self.last_tone = "neutral and informative"
        await self._persist_state()
        return "neutral and informative" # Final default