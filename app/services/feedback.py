
"""
User Feedback Service - Collect and learn from user feedback.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select
from app.db.session import SessionLocal

class FeedbackService:
    """Collect and learn from user feedback."""
    
    async def record_feedback(
        self, 
        user_id: int, 
        query: str, 
        response: str, 
        rating: int,
        correction: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record user feedback and update patterns."""
        # 1. Save feedback
        async with SessionLocal() as db:
            # Create feedback table if needed (simplified - using memory)
            feedback_entry = {
                "user_id": user_id,
                "query": query,
                "response": response,
                "rating": rating,
                "correction": correction,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in memory as a memory entry
            from app.models import Memory
            content = f"User Feedback: {query}\nRating: {rating}/5\nCorrection: {correction or 'None'}"
            memory = Memory(
                user_id=user_id,
                title=f"Feedback: {query[:30]}...",
                content=content,
                tags="feedback",
                modality="text",
                extra_data={"rating": rating, "query": query, "response": response[:200]}
            )
            db.add(memory)
            await db.commit()
        
        # 2. If rating < 3 and correction provided, extract pattern
        if rating < 3 and correction:
            await self.extract_pattern(query, response, correction, user_id)
        
        return {
            "status": "success",
            "rating": rating,
            "correction_saved": bool(correction),
            "message": "Thank you for your feedback!"
        }
    
    async def extract_pattern(self, query: str, response: str, correction: str, user_id: int):
        """Extract a learning pattern from user correction."""
        try:
            from app.models import SemanticPattern
            async with SessionLocal() as db:
                pattern = SemanticPattern(
                    pattern_type="user_correction",
                    trigger=f"When user asks about '{query[:50]}'",
                    correction=correction,
                    weight=0.5,
                    success_count=1,
                    is_active=True
                )
                db.add(pattern)
                await db.commit()
                print(f"✅ Extracted pattern from user feedback: {query[:30]}...")
        except Exception as e:
            print(f"Failed to extract pattern: {e}")
