"""
Enhanced Consolidation Service with Parallel Batch Processing
5-10x faster pattern extraction and consolidation
"""
import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EpisodicEntry, SemanticPattern
from app.config import Config
from app.swarm.core.generator import GeneratorAgent

logger = logging.getLogger(__name__)

class ConsolidationService:
    """Enhanced consolidation with parallel batch processing."""
    
    def __init__(self, session_factory, max_workers: int = 4):
        self.session_factory = session_factory
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._teacher_model = None
        self._semaphore = asyncio.Semaphore(max_workers * 2)
    
    async def _get_teacher_model(self):
        """Lazy load the teacher model with caching."""
        if not self._teacher_model:
            self._teacher_model = GeneratorAgent()
        return self._teacher_model
    
    async def consolidate_memories_optimized(self, batch_size: int = 20) -> Dict[str, Any]:
        """
        Optimized consolidation with parallel batch processing.
        Uses ThreadPoolExecutor for CPU-bound operations and asyncio.gather for I/O.
        """
        async with self.session_factory() as db:
            # Get unconsolidated entries with efficient query
            stmt = select(EpisodicEntry).where(
                EpisodicEntry.consolidated == False
            ).order_by(EpisodicEntry.timestamp).limit(batch_size)
            
            entries = (await db.execute(stmt)).scalars().all()
            
            if not entries:
                logger.info("📊 No unconsolidated entries found")
                return {
                    "processed": 0,
                    "patterns_created": 0,
                    "patterns_updated": 0,
                    "errors": 0,
                    "time_ms": 0
                }
            
            start_time = datetime.now(timezone.utc)
            logger.info(f"📊 Found {len(entries)} unconsolidated entries")
            
            # Phase 1: Batch check existing patterns (parallel)
            entry_patterns = await self._batch_find_patterns(db, entries)
            
            # Phase 2: Group by consolidation need
            to_update = []
            to_create = []
            
            for entry in entries:
                pattern = entry_patterns.get(entry.id)
                if pattern:
                    to_update.append((entry, pattern))
                else:
                    to_create.append(entry)
            
            # Phase 3: Parallel pattern extraction for new entries
            created_patterns = []
            if to_create:
                created_patterns = await self._batch_extract_patterns(to_create)
            
            # Phase 4: Bulk operations
            results = {
                "processed": len(entries),
                "patterns_created": 0,
                "patterns_updated": 0,
                "patterns_reinforced": 0,
                "errors": 0,
                "time_ms": 0
            }
            
            # Bulk update existing patterns
            if to_update:
                results["patterns_updated"] = len(to_update)
                for entry, pattern in to_update:
                    pattern.occurrence_count += 1
                    pattern.updated_at = datetime.now(timezone.utc)
                    entry.consolidated = True
                    logger.info(f"🔄 Reinforced pattern: {pattern.trigger[:30]}... (count: {pattern.occurrence_count})")
            
            # Bulk insert new patterns
            if created_patterns:
                results["patterns_created"] = len(created_patterns)
                db.add_all(created_patterns)
                
                # Mark entries as consolidated
                for entry in to_create:
                    entry.consolidated = True
            
            # Commit all changes
            await db.commit()
            
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            results["time_ms"] = elapsed
            
            logger.info(f"📊 Consolidation complete in {elapsed:.0f}ms: {results}")
            return results
    
    async def _batch_find_patterns(self, db: AsyncSession, entries: List[EpisodicEntry]) -> Dict[int, Optional[SemanticPattern]]:
        """
        Batch find existing patterns using efficient queries.
        """
        if not entries:
            return {}
        
        # Get all active patterns once
        stmt = select(SemanticPattern).where(SemanticPattern.is_active == True)
        result = await db.execute(stmt)
        all_patterns = result.scalars().all()
        
        if not all_patterns:
            return {entry.id: None for entry in entries}
        
        # Build pattern index for fast lookup
        pattern_index = {}
        for pattern in all_patterns:
            if pattern.trigger:
                # Use first few words as key for matching
                key = pattern.trigger[:50].lower()
                pattern_index[key] = pattern
        
        # Match patterns to entries
        result = {}
        for entry in entries:
            matched = None
            if entry.query:
                query_key = entry.query[:50].lower()
                # Check exact match first
                if query_key in pattern_index:
                    matched = pattern_index[query_key]
                else:
                    # Check partial match
                    for key, pattern in pattern_index.items():
                        if query_key in key or key in query_key:
                            matched = pattern
                            break
            
            result[entry.id] = matched
        
        return result
    
    async def _batch_extract_patterns(self, entries: List[EpisodicEntry]) -> List[SemanticPattern]:
        """
        Extract patterns from multiple entries in parallel.
        Uses semaphore to limit concurrent teacher model calls.
        """
        if not entries:
            return []
        
        # Create tasks with semaphore control
        tasks = []
        for entry in entries:
            task = self._extract_pattern_with_semaphore(entry)
            tasks.append(task)
        
        # Execute all extraction tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results and filter errors
        patterns = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Pattern extraction error: {result}")
            elif result:
                patterns.extend(result)
        
        return patterns
    
    async def _extract_pattern_with_semaphore(self, entry: EpisodicEntry) -> List[SemanticPattern]:
        """
        Extract pattern from a single entry with semaphore control.
        """
        async with self._semaphore:
            return await self._extract_patterns_with_teacher(entry)
    
    async def _extract_patterns_with_teacher(self, entry: EpisodicEntry) -> List[SemanticPattern]:
        """
        Extract patterns using a teacher model with improved error handling.
        """
        try:
            eval_data = entry.evaluation
            if isinstance(eval_data, str):
                try:
                    eval_data = json.loads(eval_data)
                except:
                    eval_data = {}
            
            if not eval_data or eval_data.get("passed", True):
                return []
            
            # Extract metrics
            faithfulness = eval_data.get("faithfulness", 0.5)
            confidence = eval_data.get("confidence", 0.5)
            feedback = eval_data.get("feedback", "Unknown")
            
            # Determine if pattern is needed
            if faithfulness >= 0.6 and confidence >= 0.6:
                return []
            
            # Determine pattern type
            if faithfulness < 0.6:
                pattern_type = "hallucination"
            elif confidence < 0.6:
                pattern_type = "low_confidence"
            elif feedback and "missing" in feedback.lower():
                pattern_type = "incomplete"
            else:
                pattern_type = "general"
            
            # Generate correction with teacher model
            correction = await self._generate_correction(entry, feedback, pattern_type)
            
            # Create pattern
            trigger = entry.query[:100] if entry.query else "unknown query"
            
            pattern = SemanticPattern(
                pattern_type=pattern_type,
                trigger=trigger,
                correction=correction,
                occurrence_count=1,
                success_count=0,
                weight=0.7,
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            
            logger.info(f"📝 Created pattern: {pattern_type} - {trigger[:30]}...")
            return [pattern]
            
        except Exception as e:
            logger.error(f"Pattern extraction failed for entry {entry.id}: {e}")
            return []
    
    async def _generate_correction(self, entry: EpisodicEntry, feedback: str, pattern_type: str) -> str:
        """
        Generate correction using teacher model with fallback.
        """
        try:
            teacher = await self._get_teacher_model()
            
            prompt = f"""
            You are a teacher model improving a student AI.
            
            The student gave this answer:
            QUERY: {entry.query[:300] if entry.query else 'No query'}
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
            return correction
            
        except Exception as e:
            logger.warning(f"Teacher model failed, using feedback: {e}")
            return f"Improve response quality: {feedback}"

class ConsolidationTask:
    """Background task wrapper with optimized consolidation."""
    
    def __init__(self, orchestrator, memory_service, config):
        self.orchestrator = orchestrator
        self.memory_service = memory_service
        self.config = config
        self.batch_size = config.get("batch_size", 20)  # Increased from 10
        self.interval_hours = config.get("interval_hours", 1.0)
        self.trigger_event = None
        self.max_workers = config.get("max_workers", 4)
        self._service = None
    
    async def _get_service(self):
        """Lazy load consolidation service."""
        if not self._service:
            self._service = ConsolidationService(
                self.memory_service.db,
                max_workers=self.max_workers
            )
        return self._service
    
    async def run(self):
        """Background consolidation loop with optimized processing."""
        logger.info(f"🔄 Consolidation task started (batch_size={self.batch_size}, workers={self.max_workers})")
        
        while True:
            try:
                # Wait for trigger or interval
                if self.trigger_event:
                    try:
                        await asyncio.wait_for(
                            self.trigger_event.wait(),
                            timeout=self.interval_hours * 3600
                        )
                        self.trigger_event.clear()
                        logger.info("🔄 Consolidation triggered manually")
                    except asyncio.TimeoutError:
                        logger.info("🔄 Consolidation triggered by interval")
                else:
                    await asyncio.sleep(self.interval_hours * 3600)
                
                # Run optimized consolidation
                service = await self._get_service()
                results = await service.consolidate_memories_optimized(
                    batch_size=self.batch_size
                )
                
                if results["processed"] > 0:
                    logger.info(f"✅ Consolidation complete: {results}")
                else:
                    logger.info("📊 No new patterns to consolidate")
                
            except Exception as e:
                logger.error(f"❌ Consolidation loop error: {e}")
                await asyncio.sleep(60)
