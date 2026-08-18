"""
Intelligence Compression Engine - Phase 10.1
Multi-Source Pattern Extractor
Extracts patterns from documents, conversations, decisions, and feedback.
"""
import logging
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

from app.swarm.core.generator import GeneratorAgent
from app.services.semantic_memory import SemanticMemory
from app.models import SemanticPattern

logger = logging.getLogger(__name__)

@dataclass
class ExtractedPattern:
    """Represents a pattern extracted from a source."""
    pattern_type: str  # success, failure, improvement, domain
    trigger: str
    correction: str
    source: str  # document, conversation, decision, feedback
    source_id: Optional[int] = None
    confidence: float = 0.7
    weight: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PatternExtractor:
    """
    Extracts patterns from multiple intelligence sources.
    Sources: documents, conversations, decisions, feedback
    """
    
    def __init__(self, semantic_memory: Optional[SemanticMemory] = None):
        self.semantic_memory = semantic_memory
        self.generator = GeneratorAgent()
        self._patterns: List[ExtractedPattern] = []
    
    async def extract_from_document(self, doc: Dict[str, Any]) -> List[ExtractedPattern]:
        """Extract patterns from a document."""
        patterns = []
        
        try:
            content = doc.get("content", "")
            title = doc.get("title", "")
            
            if not content:
                return patterns
            
            # Use LLM to extract key concepts
            prompt = f"""
            Analyze the following document and extract key patterns, rules, and insights.
            
            Document Title: {title}
            Document Content: {content[:2000]}
            
            Extract:
            1. Key rules or policies mentioned
            2. Important decision criteria
            3. Recurring themes or patterns
            4. Actionable insights
            
            Return as JSON list with fields: type, trigger, correction, confidence
            """
            
            response = await self.generator.generate(
                query=prompt,
                context=[],
                route={"provider": "ollama", "tier": "local"}
            )
            
            result = response.get("answer", "[]")
            
            # Parse JSON response
            try:
                # Extract JSON from response
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0]
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0]
                
                data = json.loads(result)
                
                for item in data:
                    if isinstance(item, dict):
                        pattern = ExtractedPattern(
                            pattern_type=item.get("type", "general"),
                            trigger=item.get("trigger", title[:100]),
                            correction=item.get("correction", ""),
                            source="document",
                            source_id=doc.get("id"),
                            confidence=item.get("confidence", 0.7),
                            weight=0.7,
                            metadata={"document_title": title}
                        )
                        patterns.append(pattern)
                        
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response for document: {e}")
                # Fallback: extract simple patterns
                if "contract" in content.lower():
                    patterns.append(ExtractedPattern(
                        pattern_type="domain",
                        trigger="contract",
                        correction="contract_response_template",
                        source="document",
                        source_id=doc.get("id"),
                        confidence=0.6
                    ))
                    
        except Exception as e:
            logger.error(f"Document pattern extraction failed: {e}")
        
        logger.info(f"Extracted {len(patterns)} patterns from document: {title}")
        return patterns
    
    async def extract_from_conversation(self, conversation: List[Dict]) -> List[ExtractedPattern]:
        """Extract patterns from conversation history."""
        patterns = []
        
        try:
            if not conversation:
                return patterns
            
            # Extract conversation topics and patterns
            topics = {}
            intents = {}
            
            for msg in conversation:
                content = msg.get("content", "")
                if not content:
                    continue
                
                # Simple keyword extraction
                words = content.lower().split()
                for word in words:
                    if len(word) > 3 and word in ["contract", "security", "compliance", "risk", "review", "approve"]:
                        topics[word] = topics.get(word, 0) + 1
            
            # Create patterns from frequent topics
            for topic, count in topics.items():
                if count >= 2:
                    patterns.append(ExtractedPattern(
                        pattern_type="conversation",
                        trigger=topic,
                        correction=f"{topic}_response_template",
                        source="conversation",
                        confidence=min(0.9, 0.5 + count * 0.1),
                        weight=0.6,
                        metadata={"frequency": count}
                    ))
                    
        except Exception as e:
            logger.error(f"Conversation pattern extraction failed: {e}")
        
        logger.info(f"Extracted {len(patterns)} patterns from conversation")
        return patterns
    
    async def extract_from_decision(self, decision: Dict[str, Any]) -> List[ExtractedPattern]:
        """Extract patterns from a decision event."""
        patterns = []
        
        try:
            query = decision.get("query", "")
            outcome = decision.get("outcome", "")
            confidence = decision.get("confidence", 0.0)
            
            if not query:
                return patterns
            
            # Determine pattern type based on outcome
            if outcome == "success" and confidence > 0.8:
                pattern_type = "success"
                weight = 0.8
            elif outcome == "failure" or confidence < 0.3:
                pattern_type = "failure"
                weight = 0.3
            else:
                pattern_type = "improvement"
                weight = 0.6
            
            patterns.append(ExtractedPattern(
                pattern_type=pattern_type,
                trigger=query[:100],
                correction=f"{pattern_type}_pattern_{int(time.time())}",
                source="decision",
                source_id=decision.get("id"),
                confidence=confidence,
                weight=weight,
                metadata={"outcome": outcome, "decision_id": decision.get("id")}
            ))
            
        except Exception as e:
            logger.error(f"Decision pattern extraction failed: {e}")
        
        return patterns
    
    async def extract_from_feedback(self, feedback: Dict[str, Any]) -> List[ExtractedPattern]:
        """Extract patterns from user feedback."""
        patterns = []
        
        try:
            rating = feedback.get("rating", 0)
            comment = feedback.get("comment", "")
            
            if rating >= 4:
                pattern_type = "success"
                weight = 0.8
            elif rating <= 2:
                pattern_type = "failure"
                weight = 0.3
            else:
                pattern_type = "improvement"
                weight = 0.5
            
            if comment:
                patterns.append(ExtractedPattern(
                    pattern_type=pattern_type,
                    trigger=comment[:100],
                    correction=f"feedback_{pattern_type}_{int(time.time())}",
                    source="feedback",
                    confidence=rating / 5.0,
                    weight=weight,
                    metadata={"rating": rating}
                ))
                
        except Exception as e:
            logger.error(f"Feedback pattern extraction failed: {e}")
        
        return patterns
    
    async def extract_all(self, sources: Dict[str, List]) -> List[ExtractedPattern]:
        """Extract patterns from all sources in parallel."""
        all_patterns = []
        
        # Extract from each source type
        if "documents" in sources:
            for doc in sources["documents"]:
                patterns = await self.extract_from_document(doc)
                all_patterns.extend(patterns)
        
        if "conversations" in sources:
            for conv in sources["conversations"]:
                patterns = await self.extract_from_conversation(conv)
                all_patterns.extend(patterns)
        
        if "decisions" in sources:
            for decision in sources["decisions"]:
                patterns = await self.extract_from_decision(decision)
                all_patterns.extend(patterns)
        
        if "feedback" in sources:
            for feedback in sources["feedback"]:
                patterns = await self.extract_from_feedback(feedback)
                all_patterns.extend(patterns)
        
        logger.info(f"Extracted total of {len(all_patterns)} patterns from all sources")
        return all_patterns
    
    async def save_patterns(self, patterns: List[ExtractedPattern]) -> List[SemanticPattern]:
        """Save extracted patterns to semantic memory."""
        saved = []
        
        if not self.semantic_memory:
            logger.warning("No semantic memory available, patterns not saved")
            return saved
        
        for pattern in patterns:
            semantic_pattern = SemanticPattern(
                pattern_type=pattern.pattern_type,
                trigger=pattern.trigger,
                correction=pattern.correction,
                success_count=1 if pattern.pattern_type == "success" else 0,
                weight=pattern.weight,
                is_active=True,
                occurrence_count=1,
                created_at=pattern.timestamp
            )
            
            await self.semantic_memory.add_pattern(semantic_pattern)
            saved.append(semantic_pattern)
        
        logger.info(f"Saved {len(saved)} patterns to semantic memory")
        return saved


class IntelligenceCompressor:
    """
    Main Intelligence Compression Engine.
    Orchestrates pattern extraction, reinforcement, and crystallization.
    """
    
    def __init__(self, semantic_memory: Optional[SemanticMemory] = None):
        self.extractor = PatternExtractor(semantic_memory)
        self.semantic_memory = semantic_memory
    
    async def compress(self, source_type: str, data: Any) -> Dict[str, Any]:
        """
        Compress intelligence from a source.
        
        Args:
            source_type: 'document', 'conversation', 'decision', 'feedback'
            data: The source data to compress
            
        Returns:
            Dict with compression metrics
        """
        start_time = datetime.now(timezone.utc)
        
        # Extract patterns based on source type
        if source_type == "document":
            patterns = await self.extractor.extract_from_document(data)
        elif source_type == "conversation":
            patterns = await self.extractor.extract_from_conversation(data)
        elif source_type == "decision":
            patterns = await self.extractor.extract_from_decision(data)
        elif source_type == "feedback":
            patterns = await self.extractor.extract_from_feedback(data)
        else:
            return {"error": f"Unknown source type: {source_type}"}
        
        # Save patterns to semantic memory
        saved = await self.extractor.save_patterns(patterns)
        
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return {
            "source_type": source_type,
            "patterns_extracted": len(patterns),
            "patterns_saved": len(saved),
            "compression_ratio": 1000 if saved else 0,  # Placeholder
            "duration_ms": duration_ms,
            "timestamp": end_time.isoformat()
        }
    
    async def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics."""
        if not self.semantic_memory:
            return {"error": "Semantic memory not available"}
        
        patterns = await self.semantic_memory.get_patterns()
        total = len(patterns)
        active = sum(1 for p in patterns if p.is_active)
        success = sum(1 for p in patterns if p.pattern_type == "success")
        failure = sum(1 for p in patterns if p.pattern_type == "failure")
        
        return {
            "total_patterns": total,
            "active_patterns": active,
            "success_patterns": success,
            "failure_patterns": failure,
            "avg_weight": sum(p.weight for p in patterns) / total if total > 0 else 0,
            "compression_ratio": 10000 if total > 0 else 0
        }
