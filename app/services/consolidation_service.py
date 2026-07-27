import logging
import asyncio
import json
from datetime import datetime, timezone
from sqlalchemy import select
from app.models import EpisodicEntry, SemanticPattern
from app.config import Config

logger = logging.getLogger(__name__)

class ConsolidationService:
    """Enhanced consolidation with learning metrics and pattern reinforcement."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._teacher_model = None
    
    async def _get_teacher_model(self):
        """Lazy load the teacher model (could be a larger model for better instructions)."""
        if not self._teacher_model:
            from app.swarm.core.generator import GeneratorAgent
            self._teacher_model = GeneratorAgent()
        return self._teacher_model

    async def consolidate_memories(self, batch_size: int = 10) -> dict:
        """Consolidate episodic memories into semantic patterns with reinforcement."""
        async with self.session_factory() as db:
            stmt = select(EpisodicEntry).where(
                EpisodicEntry.consolidated == False
            ).limit(batch_size)
            entries = (await db.execute(stmt)).scalars().all()
            
            logger.info(f"📊 Found {len(entries)} unconsolidated entries")
            
            results = {
                "processed": 0,
                "patterns_created": 0,
                "patterns_updated": 0,
                "patterns_reinforced": 0,
                "errors": 0
            }
            
            for entry in entries:
                try:
                    logger.info(f"📝 Processing entry {entry.id}: {entry.query[:30]}...")
                    
                    # Check if this pattern already exists
                    existing_pattern = await self._find_matching_pattern(db, entry)
                    
                    if existing_pattern:
                        # Reinforce existing pattern
                        existing_pattern.occurrence_count += 1
                        existing_pattern.updated_at = datetime.now(timezone.utc)
                        results["patterns_updated"] += 1
                        logger.info(f"🔄 Reinforced pattern: {existing_pattern.trigger[:30]}... (count: {existing_pattern.occurrence_count})")
                    else:
                        # Create new pattern
                        patterns = await self._extract_patterns_with_teacher(entry)
                        for pattern in patterns:
                            db.add(pattern)
                            results["patterns_created"] += 1
                            logger.info(f"✨ Created new pattern: {pattern.trigger[:30]}...")
                    
                    entry.consolidated = True
                    results["processed"] += 1
                    
                except Exception as e:
                    logger.error(f"❌ Consolidation error for entry {entry.id}: {e}")
                    results["errors"] += 1
            
            await db.commit()
            logger.info(f"📊 Consolidation complete: {results}")
            return results

    async def _find_matching_pattern(self, db, entry: EpisodicEntry) -> SemanticPattern:
        """Find if a similar pattern already exists using vector similarity."""
        # For now, use simple trigger matching
        # In production, use vector similarity
        stmt = select(SemanticPattern)
        result = await db.execute(stmt)
        patterns = result.scalars().all()
        
        for pattern in patterns:
            # Simple similarity check - improve with vector search
            if pattern.trigger.lower() in entry.query.lower() or entry.query.lower() in pattern.trigger.lower():
                return pattern
        return None

    async def _extract_patterns_with_teacher(self, entry: EpisodicEntry):
        """Extract patterns using a teacher model for better instructions."""
        eval_data = entry.evaluation
        if isinstance(eval_data, str):
            try:
                eval_data = json.loads(eval_data)
            except:
                return []
        
        if not eval_data or eval_data.get("passed", True):
            return []
        
        feedback = eval_data.get("feedback", "Unknown")
        faithfulness = eval_data.get("faithfulness", 0.5)
        confidence = eval_data.get("confidence", 0.5)
        
        if faithfulness >= 0.6 and confidence >= 0.6:
            return []
        
        # Determine pattern type
        if faithfulness < 0.6:
            pattern_type = "hallucination"
        elif confidence < 0.6:
            pattern_type = "low_confidence"
        else:
            pattern_type = "general"
        
        # Use teacher model to generate better correction
        try:
            teacher = await self._get_teacher_model()
            prompt = f"""
            You are a teacher model improving a student AI.
            
            The student gave this answer:
            QUERY: {entry.query[:300]}
            ANSWER: {entry.answer[:200] if entry.answer else 'No answer'}
            
            Evaluation feedback: {feedback}
            Failure type: {pattern_type}
            
            Write a concise, actionable correction instruction (max 100 words) that would help the student improve.
            Make it specific to this type of failure.
            """
            
            response = await teacher.generate(
                query=prompt,
                context=[],
                route={"provider": "ollama", "tier": "local"}
            )
            
            correction = response.get("answer", feedback)[:200]
        except Exception as e:
            logger.warning(f"Teacher model failed, using feedback: {e}")
            correction = f"Improve response quality: {feedback}"
        
        trigger = entry.query[:100] if entry.query else "unknown query"
        
        pattern = SemanticPattern(
            pattern_type=pattern_type,
            trigger=trigger,
            correction=correction,
            occurrence_count=1,
            success_count=0,
            weight=0.7,
            is_active=True
        )
        
        logger.info(f"📝 Created enhanced pattern: {pattern_type} - {trigger[:30]}...")
        return [pattern]

class ConsolidationTask:
    """Background task wrapper for the crystallization engine."""
    def __init__(self, orchestrator, memory_service, config):
        self.orchestrator = orchestrator
        self.memory_service = memory_service
        self.config = config
        self.batch_size = config.get("batch_size", 10)
        self.interval_hours = config.get("interval_hours", 1.0)
        self.trigger_event = None

    async def run(self):
        logger.info("Consolidation task background loop started.")
        while True:
            try:
                if self.trigger_event:
                    try:
                        await asyncio.wait_for(self.trigger_event.wait(), timeout=self.interval_hours * 3600)
                        self.trigger_event.clear()
                        logger.info("Consolidation triggered manually.")
                    except asyncio.TimeoutError:
                        logger.info("Consolidation triggered by interval.")
                else:
                    await asyncio.sleep(self.interval_hours * 3600)

                service = ConsolidationService(self.memory_service.db)
                results = await service.consolidate_memories(batch_size=self.batch_size)
                logger.info(f"Consolidation results: {results}")
            except Exception as e:
                logger.error(f"Error in consolidation loop: {e}")
                await asyncio.sleep(60)
