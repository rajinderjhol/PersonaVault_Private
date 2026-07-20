from fastapi import APIRouter
import logging
import json
import httpx
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import UserPersona, EpisodicEntry
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personalization", tags=["personalization"])

class PersonaProfiler:
    """
    Creates a unique cognitive profile for each user to drive True Personalization.
    """
    def __init__(self, db: AsyncSession, client: httpx.AsyncClient = None):
        self.db = db
        self.client = client or httpx.AsyncClient()

    async def get_or_create_profile(self, user_id: int) -> UserPersona:
        stmt = select(UserPersona).where(UserPersona.user_id == user_id)
        result = await self.db.execute(stmt)
        profile = result.scalars().first()
        if not profile:
            profile = UserPersona(
                user_id=user_id,
                writing_style="balanced",
                communication_style="casual"
            )
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
        return profile

    async def personalize_response(self, user_id: int, content: str) -> str:
        """
        Adjusts AI output based on the user's learned cognitive style.
        """
        profile = await self.get_or_create_profile(user_id)
        
        # Personalization logic: wrap response with persona instructions
        if profile.writing_style == "concise":
            content = f"[STRICT BREVITY] {content}"
        elif profile.writing_style == "technical":
            content = f"[DETAILED/TECHNICAL] {content}"
        
        if profile.communication_style == "formal":
            content = f"[FORMAL TONE] {content}"
            
        return content

    async def _analyze_writing_style(self, user_id: int):
        """Background task to update user persona based on new memories."""
        logger.info(f"Analyzing writing style for user {user_id}")
        
        # Fetch last 10 successful interactions
        stmt = select(EpisodicEntry).where(
            EpisodicEntry.user_feedback == 1
        ).order_by(EpisodicEntry.timestamp.desc()).limit(10)
        result = await self.db.execute(stmt)
        history = result.scalars().all()
        
        if not history:
            return

        samples = "\n---\n".join([h.query for h in history])
        prompt = f"""
Analyze the following user queries for writing style and cognitive patterns.
SAMPLES:
{samples}

Identify:
1. Writing style (concise, technical, balanced, verbose)
2. Communication style (formal, casual)
3. Core interests (JSON format)

Return JSON only: {{"writing_style": "...", "communication_style": "...", "interests": []}}
"""
        try:
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            res = await self.client.post(f"{ollama_url}/api/generate", json={
                "model": "llama3", "prompt": prompt, "stream": False
            }, timeout=30.0)
            if res.status_code == 200:
                analysis = json.loads(res.json().get("response", "{}"))
                profile = await self.get_or_create_profile(user_id)
                profile.writing_style = analysis.get("writing_style", profile.writing_style)
                profile.communication_style = analysis.get("communication_style", profile.communication_style)
                profile.cognitive_patterns = analysis
                await self.db.commit()
        except Exception as e:
            logger.error(f"Persona analysis failed: {e}")