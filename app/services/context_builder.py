
"""
Enhanced Context Builder for PersonaVault.
Gathers context from memories, documents, files, and conversation history.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import Memory

class ContextBuilder:
    """Build rich context from all available sources."""
    
    def __init__(self, vector_service=None, memory_service=None):
        self.vector_service = vector_service
        self.memory_service = memory_service
    
    async def build_context(
        self, 
        query: str, 
        user_id: int,
        include_documents: bool = True,
        include_memories: bool = True,
        include_conversations: bool = True,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Build context from all sources."""
        context = {
            "memories": [],
            "documents": [],
            "conversations": [],
            "files": [],
            "sources": [],
            "combined": ""
        }
        
        # 1. Vector search across ALL content
        if self.vector_service:
            try:
                results = await self.vector_service.search_similar(query, user_id, limit=limit)
                
                for result in results:
                    result_type = result.get("modality", "memory")
                    if result_type == "document":
                        context["documents"].append(result)
                    elif result_type == "memory":
                        context["memories"].append(result)
                    else:
                        context["memories"].append(result)
                    
                    context["sources"].append({
                        "type": result_type,
                        "id": result.get("id"),
                        "title": result.get("title", "Untitled")
                    })
            except Exception as e:
                print(f"Vector search error: {e}")
        
        # 2. Conversation history
        if include_conversations:
            context["conversations"] = await self._get_conversation_history(user_id, limit=5)
        
        # 3. Combine context
        context["combined"] = self._combine_context(context)
        
        return context
    
    async def _get_conversation_history(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get recent conversation history."""
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
                    "user": user_part,
                    "ai": ai_part,
                    "timestamp": log.created_at.isoformat(),
                    "title": log.title
                })
            
            return conversations
    
    def _combine_context(self, context: Dict) -> str:
        """Combine all context sources into a single string."""
        parts = []
        
        if context["documents"]:
            doc_text = "\n".join([
                f"- [{d.get('title', 'Document')}]: {d.get('content', '')[:500]}"
                for d in context["documents"][:3]
            ])
            parts.append(f"<DOCUMENTS>\n{doc_text}\n</DOCUMENTS>")
        
        if context["memories"]:
            mem_text = "\n".join([
                f"- [{m.get('title', 'Memory')}]: {m.get('content', '')[:300]}"
                for m in context["memories"][:5]
            ])
            parts.append(f"<MEMORIES>\n{mem_text}\n</MEMORIES>")
        
        if context["conversations"]:
            conv_text = "\n".join([
                f"- User: {c['user'][:100]}\n  AI: {c['ai'][:100]}"
                for c in context["conversations"][:3]
            ])
            parts.append(f"<CONVERSATION_HISTORY>\n{conv_text}\n</CONVERSATION_HISTORY>")
        
        return "\n\n".join(parts)
