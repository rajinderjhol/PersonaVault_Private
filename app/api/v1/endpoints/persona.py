from fastapi import APIRouter
import logging
import json
import httpx
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import UserPersona, EpisodicEntry
from app.config import Config
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personalization", tags=["personalization"])

class PersonaProfiler:
    """
    Creates a unique cognitive profile for each user to drive True Personalization.
    """
    def __init__(self, db_session=None, client: httpx.AsyncClient = None):
        self.db_session = db_session
        self.client = client or httpx.AsyncClient()

    async def get_or_create_profile(self, user_id: int, session: Optional[AsyncSession] = None) -> UserPersona:
        """Get or create a user persona profile."""
        # Use provided session or create one from session factory
        if session is None and self.db_session is not None:
            async with self.db_session() as db:
                return await self._get_or_create_profile_internal(user_id, db)
        elif session is not None:
            return await self._get_or_create_profile_internal(user_id, session)
        else:
            raise ValueError("No database session provided")

    async def _get_or_create_profile_internal(self, user_id: int, db: AsyncSession) -> UserPersona:
        """Internal method to get or create profile with a session."""
        stmt = select(UserPersona).where(UserPersona.user_id == user_id)
        result = await db.execute(stmt)
        profile = result.scalars().first()
        if not profile:
            # Create default profile with correct fields
            profile = UserPersona(
                user_id=user_id,
                persona_type="personal",
                name="Default Profile",
                description="Default user profile",
                traits={"writing_style": "balanced", "communication_style": "casual"},
                preferences={},
                is_active=True
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
        return profile

    async def personalize_response(self, user_id: int, content: str) -> str:
        """Adjusts AI output based on the user's learned cognitive style."""
        profile = await self.get_or_create_profile(user_id)
        
        # Extract writing style from traits
        traits = profile.traits or {}
        writing_style = traits.get("writing_style", "balanced")
        communication_style = traits.get("communication_style", "casual")
        
        if writing_style == "concise":
            content = f"[STRICT BREVITY] {content}"
        elif writing_style == "technical":
            content = f"[DETAILED/TECHNICAL] {content}"
        
        if communication_style == "formal":
            content = f"[FORMAL TONE] {content}"
            
        return content

    async def _analyze_writing_style(self, user_id: int):
        """Background task to update user persona based on new memories."""
        logger.info(f"Analyzing writing style for user {user_id}")
        
        if self.db_session is None:
            logger.error("No database session available for analysis")
            return
            
        async with self.db_session() as db:
            stmt = select(EpisodicEntry).where(
                EpisodicEntry.user_feedback == 1
            ).order_by(EpisodicEntry.timestamp.desc()).limit(10)
            result = await db.execute(stmt)
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
                ollama_url = Config.OLLAMA_BASE_URL
                res = await self.client.post(f"{ollama_url}/api/generate", json={
                    "model": getattr(Config, "OLLAMA_BASE_MODEL", "llama3"),
                    "prompt": prompt,
                    "stream": False
                }, timeout=30.0)
                if res.status_code == 200:
                    analysis = json.loads(res.json().get("response", "{}"))
                    profile = await self.get_or_create_profile(user_id, session=db)
                    traits = profile.traits or {}
                    traits["writing_style"] = analysis.get("writing_style", traits.get("writing_style", "balanced"))
                    traits["communication_style"] = analysis.get("communication_style", traits.get("communication_style", "casual"))
                    profile.traits = traits
                    await db.commit()
            except Exception as e:
                logger.error(f"Persona analysis failed: {e}")
