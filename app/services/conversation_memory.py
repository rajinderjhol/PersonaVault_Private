
"""
Conversation Memory Service - Maintains context across conversations.
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import Memory

class ConversationMemory:
    """Maintain context across conversations."""
    
    async def get_context(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get recent conversation context."""
        async with SessionLocal() as db:
            stmt = select(Memory).where(
                Memory.user_id == user_id,
                Memory.tags == "interaction_log"
            ).order_by(Memory.id.desc()).limit(limit)
            result = await db.execute(stmt)
            logs = result.scalars().all()
            
            conversations = []
            for log in reversed(logs):
                parts = log.content.split("\nAI: ")
                user_part = parts[0].replace("User: ", "") if parts else ""
                ai_part = parts[1] if len(parts) > 1 else ""
                
                conversations.append({
                    "query": user_part,
                    "response": ai_part,
                    "timestamp": log.created_at.isoformat(),
                    "title": log.title
                })
            
            return conversations
    
    async def get_summary(self, user_id: int) -> str:
        """Get a summary of recent conversations."""
        history = await self.get_context(user_id, limit=10)
        if not history:
            return ""
        
        summary_parts = []
        for h in history:
            if h["query"]:
                summary_parts.append(f"User asked: {h['query'][:50]}...")
        
        return "\n".join(summary_parts[:5])
    
    async def save_conversation(self, user_id: int, query: str, response: str):
        """Save a conversation turn."""
        try:
            async with SessionLocal() as db:
                log_entry = Memory(
                    user_id=user_id,
                    title=f"Chat: {query[:30]}...",
                    content=f"User: {query}\nAI: {response}",
                    tags="interaction_log",
                    modality="text"
                )
                db.add(log_entry)
                await db.commit()
        except Exception as e:
            print(f"Failed to save conversation: {e}")
