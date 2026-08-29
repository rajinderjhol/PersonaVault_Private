"""
Document Ingestion Service - Ingest documents from local folders
Supports PDF, Word, Excel, CSV, Markdown, TXT files
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib

import aiofiles
import aiofiles.os

logger = logging.getLogger(__name__)


@dataclass
class DocumentInfo:
    """Information about a document."""
    path: str
    name: str
    extension: str
    size_bytes: int
    modified_at: datetime
    content: Optional[str] = None
    summary: Optional[str] = None
    hash: Optional[str] = None
    processed: bool = False


@dataclass
class IngestionResult:
    """Result of document ingestion."""
    doc_id: str
    doc_path: str
    doc_name: str
    status: str  # success, failed, skipped
    error: Optional[str] = None
    memory_ids: List[str] = None
    patterns_crystallized: int = 0


class DocumentIngestionService:
    """
    Service for ingesting documents from local folders.
    Supports multiple file formats and can be run in watch mode.
    """
    
    SUPPORTED_EXTENSIONS = {
        '.pdf', '.docx', '.doc', '.xlsx', '.xls', 
        '.csv', '.md', '.txt', '.json', '.yaml', '.yml'
    }
    
    def __init__(self):
        self.ingestion_history_path = Path("data/ingestion_history.json")
        self.ingestion_history = {}
        self._load_history()
    
    def _load_history(self):
        """Load ingestion history from disk."""
        if self.ingestion_history_path.exists():
            try:
                import json
                with open(self.ingestion_history_path, 'r') as f:
                    self.ingestion_history = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load ingestion history: {e}")
    
    def _save_history(self):
        """Save ingestion history to disk."""
        try:
            import json
            self.ingestion_history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ingestion_history_path, 'w') as f:
                json.dump(self.ingestion_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save ingestion history: {e}")
    
    async def ingest_folder(
        self,
        folder_path: str,
        user_id: int = 1,
        recursive: bool = True,
        watch: bool = False,
        max_files: Optional[int] = None
    ) -> List[IngestionResult]:
        """
        Ingest all documents from a folder.
        
        Args:
            folder_path: Path to the folder to ingest
            user_id: User ID to associate with the documents
            recursive: Whether to scan subfolders
            watch: Whether to watch for changes (future)
            max_files: Maximum number of files to ingest
        
        Returns:
            List of IngestionResult objects
        """
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder not found: {folder_path}")
        
        if not folder.is_dir():
            raise ValueError(f"Path is not a directory: {folder_path}")
        
        # Get all documents
        documents = await self._scan_folder(folder, recursive)
        
        if max_files:
            documents = documents[:max_files]
        
        # Filter already ingested (if not force)
        new_documents = []
        for doc in documents:
            doc_hash = self._compute_hash(doc.path)
            doc.hash = doc_hash
            
            history_key = f"{user_id}:{doc_hash}"
            if history_key not in self.ingestion_history:
                new_documents.append(doc)
            else:
                # Check if file was modified
                last_modified = self.ingestion_history[history_key]
                if doc.modified_at > datetime.fromisoformat(last_modified):
                    new_documents.append(doc)
        
        logger.info(f"Found {len(documents)} documents, {len(new_documents)} new/modified")
        
        # Ingest documents
        results = []
        for doc in new_documents:
            result = await self._ingest_document(doc, user_id)
            results.append(result)
            
            if result.status == "success":
                # Update history
                history_key = f"{user_id}:{doc.hash}"
                self.ingestion_history[history_key] = doc.modified_at.isoformat()
                self._save_history()
        
        return results
    
    async def _scan_folder(
        self,
        folder: Path,
        recursive: bool = True
    ) -> List[DocumentInfo]:
        """Scan a folder for supported documents."""
        documents = []
        
        for item in folder.iterdir():
            if item.is_dir() and recursive:
                sub_docs = await self._scan_folder(item, recursive)
                documents.extend(sub_docs)
            elif item.is_file():
                extension = item.suffix.lower()
                if extension in self.SUPPORTED_EXTENSIONS:
                    try:
                        stat = await aiofiles.os.stat(item)
                        documents.append(DocumentInfo(
                            path=str(item),
                            name=item.name,
                            extension=extension,
                            size_bytes=stat.st_size,
                            modified_at=datetime.fromtimestamp(stat.st_mtime)
                        ))
                    except Exception as e:
                        logger.warning(f"Failed to stat {item}: {e}")
        
        return documents
    
    async def _ingest_document(
        self,
        doc: DocumentInfo,
        user_id: int
    ) -> IngestionResult:
        """Ingest a single document."""
        try:
            # Read the file
            content = await self._read_file(doc.path)
            if not content:
                return IngestionResult(
                    doc_id=doc.hash,
                    doc_path=doc.path,
                    doc_name=doc.name,
                    status="failed",
                    error="Failed to read file"
                )
            
            doc.content = content
            
            # Generate summary
            summary = await self._summarize_document(content, doc.name)
            doc.summary = summary
            
            # Store in memory
            memory_ids = await self._store_in_memory(doc, user_id, content)
            
            # Crystallize patterns
            patterns = await self._crystallize_content(content, doc.name, user_id)
            
            return IngestionResult(
                doc_id=doc.hash,
                doc_path=doc.path,
                doc_name=doc.name,
                status="success",
                memory_ids=memory_ids,
                patterns_crystallized=len(patterns)
            )
            
        except Exception as e:
            logger.error(f"Failed to ingest {doc.path}: {e}")
            return IngestionResult(
                doc_id=doc.hash or "",
                doc_path=doc.path,
                doc_name=doc.name,
                status="failed",
                error=str(e)
            )
    
    async def _read_file(self, file_path: str) -> Optional[str]:
        """Read a file's content."""
        try:
            extension = Path(file_path).suffix.lower()
            
            # PDF handling
            if extension == '.pdf':
                try:
                    import PyPDF2
                    content = ""
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            content += page.extract_text() + "\n"
                    return content
                except ImportError:
                    logger.warning("PyPDF2 not installed, PDF support limited")
                    return f"[PDF Document: {Path(file_path).name}]"
            
            # Word handling
            elif extension in ['.docx', '.doc']:
                try:
                    import docx
                    doc = docx.Document(file_path)
                    return "\n".join([p.text for p in doc.paragraphs])
                except ImportError:
                    logger.warning("python-docx not installed, Word support limited")
                    return f"[Word Document: {Path(file_path).name}]"
            
            # Excel handling
            elif extension in ['.xlsx', '.xls']:
                try:
                    import pandas as pd
                    df = pd.read_excel(file_path)
                    return df.to_string()
                except ImportError:
                    logger.warning("pandas not installed, Excel support limited")
                    return f"[Excel Document: {Path(file_path).name}]"
            
            # Text-based formats
            else:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    return await f.read()
                    
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return None
    
    async def _summarize_document(self, content: str, name: str) -> str:
        """Generate a summary of the document."""
        # Simple summary: first 500 chars + file name
        # Future: Use AI to generate intelligent summary
        preview = content[:500] + "..." if len(content) > 500 else content
        return f"File: {name}\nPreview: {preview}"
    
    async def _store_in_memory(
        self,
        doc: DocumentInfo,
        user_id: int,
        content: str
    ) -> List[str]:
        """Store the document in the memory system."""
        from app.services.memory.ice_repository import IceMemoryRepository
        from app.db.session import SessionLocal
        
        memory_ids = []
        session_factory = SessionLocal
        repo = IceMemoryRepository(session_factory)
        
        # Store in Liquid memory (Layer 2)
        memory_record = {
            "type": "document",
            "layer": 2,
            "user_id": user_id,
            "trigger": doc.name[:200],
            "correction": content[:500],
            "confidence": 0.8,
            "raw_text": content[:10000],
            "content": {
                "filename": doc.name,
                "path": doc.path,
                "extension": doc.extension,
                "size_bytes": doc.size_bytes,
                "modified_at": doc.modified_at.isoformat(),
                "summary": doc.summary
            },
            "metadata": {
                "source": "folder_ingestion",
                "file_hash": doc.hash,
                "ingested_at": datetime.now().isoformat()
            }
        }
        
        try:
            memory_id = await repo.store(memory_record)
            memory_ids.append(memory_id)
        except Exception as e:
            logger.error(f"Failed to store document in memory: {e}")
        
        return memory_ids
    
    async def _crystallize_content(
        self,
        content: str,
        filename: str,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """Crystallize patterns from the document content."""
        from app.services.memory.ice_repository import IceMemoryRepository
        from app.db.session import SessionLocal
        
        patterns = []
        
        # Simple pattern extraction: break content into chunks
        # Future: Use AI for intelligent pattern extraction
        chunks = [content[i:i+2000] for i in range(0, min(len(content), 10000), 2000)]
        
        for i, chunk in enumerate(chunks[:3]):  # Limit to 3 patterns per doc
            pattern = {
                "type": "document_pattern",
                "layer": 3,
                "user_id": user_id,
                "trigger": f"From document: {filename} - chunk {i+1}",
                "correction": chunk[:300],
                "confidence": 0.7,
                "raw_text": chunk,
                "content": {
                    "source_document": filename,
                    "chunk_index": i,
                    "text": chunk
                },
                "metadata": {
                    "source": "folder_ingestion",
                    "document_name": filename
                }
            }
            
            session_factory = SessionLocal
            repo = IceMemoryRepository(session_factory)
            try:
                pattern_id = await repo.store(pattern)
                patterns.append({"id": pattern_id, "chunk": i})
            except Exception as e:
                logger.error(f"Failed to crystallize pattern: {e}")
        
        return patterns
    
    def _compute_hash(self, file_path: str) -> str:
        """Compute a hash for a file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        except Exception:
            return str(hash(file_path))
    
    async def get_ingestion_status(self, user_id: int) -> Dict[str, Any]:
        """Get ingestion status for a user."""
        user_history = {
            k: v for k, v in self.ingestion_history.items()
            if k.startswith(f"{user_id}:")
        }
        
        return {
            "total_documents": len(user_history),
            "last_ingestion": max(user_history.values()) if user_history else None
        }
