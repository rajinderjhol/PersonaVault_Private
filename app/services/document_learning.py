"""
Phase 10.8: Document Learning
Extract and learn patterns from documents.
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

from app.models import Memory
from app.services.semantic_memory import SemanticMemory
from app.services.intelligence_compressor import PatternExtractor

logger = logging.getLogger(__name__)

class DocumentLearning:
    """
    Learn patterns from documents and add them to the knowledge base.
    """
    
    def __init__(self, session_factory, semantic_memory: Optional[SemanticMemory] = None):
        self.session_factory = session_factory
        self.semantic_memory = semantic_memory or SemanticMemory(session_factory)
        self.extractor = PatternExtractor(semantic_memory)
        self._processed_docs: set = set()
        self._stats = {"processed": 0, "patterns_created": 0, "errors": 0}
    
    async def learn_from_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract patterns from a document and add to semantic memory.
        """
        doc_id = doc.get("id")
        
        # Skip if already processed
        if doc_id in self._processed_docs:
            return {"status": "skipped", "reason": "Already processed"}
        
        try:
            # Extract patterns from document
            patterns = await self.extractor.extract_from_document(doc)
            
            if not patterns:
                return {"status": "no_patterns", "doc_id": doc_id}
            
            # Save patterns to semantic memory
            saved = await self.extractor.save_patterns(patterns)
            
            self._processed_docs.add(doc_id)
            self._stats["processed"] += 1
            self._stats["patterns_created"] += len(saved)
            
            logger.info(f"📚 Learned {len(saved)} patterns from document {doc_id}")
            
            return {
                "status": "success",
                "doc_id": doc_id,
                "patterns_extracted": len(patterns),
                "patterns_saved": len(saved)
            }
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Error learning from document {doc_id}: {e}")
            return {"status": "error", "doc_id": doc_id, "error": str(e)}
    
    async def learn_from_all_documents(self, limit: int = 50) -> Dict[str, Any]:
        """
        Learn patterns from all unprocessed documents.
        """
        self._stats = {"processed": 0, "patterns_created": 0, "errors": 0}
        
        async with self.session_factory() as db:
            from sqlalchemy import select
            stmt = select(Memory).where(
                Memory.id.not_in(list(self._processed_docs) if self._processed_docs else [0])
            ).limit(limit)
            
            result = await db.execute(stmt)
            documents = result.scalars().all()
            
            if not documents:
                return {
                    "processed": 0,
                    "patterns_created": 0,
                    "message": "No documents found"
                }
            
            logger.info(f"📚 Processing {len(documents)} documents for learning")
            
            results = []
            for doc in documents:
                doc_data = {
                    "id": doc.id,
                    "title": doc.title or "Untitled",
                    "content": doc.content,
                    "tags": doc.tags or ""
                }
                result = await self.learn_from_document(doc_data)
                results.append(result)
            
            return {
                "processed": self._stats["processed"],
                "patterns_created": self._stats["patterns_created"],
                "errors": self._stats["errors"],
                "results": results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get document learning statistics."""
        return {
            "processed_documents": len(self._processed_docs),
            "total_patterns_created": self._stats["patterns_created"],
            "pending_documents": "pending",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
