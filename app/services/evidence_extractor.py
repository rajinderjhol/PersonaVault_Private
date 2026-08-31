"""
Decision Evidence Pipeline - Extract evidence from documents.
"""
import hashlib
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.evidence import EvidenceBlock, DocumentIngestionJob
import logging

logger = logging.getLogger(__name__)

class EvidenceExtractor:
    """Extract evidence blocks from various document types."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def extract_from_document(
        self,
        content: bytes,
        filename: str,
        file_type: str,
        metadata: Dict = None
    ) -> Dict:
        """Main entry point for document extraction."""
        metadata = metadata or {}
        
        job_id = f"job_{hashlib.md5(filename.encode()).hexdigest()[:8]}"
        job = DocumentIngestionJob(
            job_id=job_id,
            filename=filename,
            file_type=file_type,
            status="processing",
            metadata=metadata
        )
        self.db.add(job)
        await self.db.flush() # Get the ID
        job_id = job.job_id
        
        try:
            if file_type in ["pdf"]:
                blocks = await self._extract_pdf(content, filename)
            elif file_type in ["txt", "text"]:
                blocks = await self._extract_text(content, filename)
            elif file_type in ["clinical_note"]:
                blocks = await self._extract_clinical_note(content, metadata)
            elif file_type in ["contract"]:
                blocks = await self._extract_contract(content, filename)
            else:
                blocks = await self._extract_generic(content, filename)
            
            stored_blocks = []
            for block in blocks:
                stored = await self._store_evidence_block(block, job.id)
                stored_blocks.append(stored)
            
            job.status = "completed"
            job.total_blocks = len(blocks)
            job.completed_at = datetime.utcnow()
            await self.db.commit()
            
            return {
                "job_id": job_id,
                "status": "completed",
                "total_blocks": len(blocks),
                "qualified_blocks": sum(1 for b in blocks if b.get("is_qualified", False)),
                "blocks": stored_blocks
            }
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            await self.db.commit()
            logger.error(f"Extraction failed: {e}")
            raise
    
    async def _extract_pdf(self, content: bytes, filename: str) -> List[Dict]:
        text = content.decode('utf-8', errors='ignore')
        sections = text.split('\n\n')
        blocks = []
        for i, section in enumerate(sections):
            if len(section.strip()) > 50:
                blocks.append({
                    "content": section.strip(),
                    "source": filename,
                    "source_type": "pdf",
                    "confidence": 0.85,
                    "provenance_score": 0.90,
                    "tags": ["pdf", "document", f"section_{i+1}"],
                    "metadata": {"page": i+1, "total_pages": len(sections)}
                })
        return blocks
    
    async def _extract_text(self, content: bytes, filename: str) -> List[Dict]:
        text = content.decode('utf-8', errors='ignore')
        paragraphs = text.split('\n\n')
        blocks = []
        for i, para in enumerate(paragraphs):
            if len(para.strip()) > 50:
                blocks.append({
                    "content": para.strip(),
                    "source": filename,
                    "source_type": "text",
                    "confidence": 0.90,
                    "provenance_score": 0.85,
                    "tags": ["text", "document"],
                    "metadata": {"paragraph": i+1}
                })
        return blocks
    
    async def _extract_clinical_note(self, content: bytes, metadata: Dict) -> List[Dict]:
        text = content.decode('utf-8', errors='ignore')
        sections = self._extract_clinical_sections(text)
        blocks = []
        for section_name, section_text in sections.items():
            if len(section_text.strip()) > 50:
                blocks.append({
                    "content": section_text.strip(),
                    "source": metadata.get("patient_id", "unknown"),
                    "source_type": "clinical_note",
                    "confidence": 0.92,
                    "provenance_score": 0.95,
                    "tags": ["clinical", "patient_record", section_name.lower()],
                    "metadata": {
                        "patient_id": metadata.get("patient_id"),
                        "section": section_name,
                        "timestamp": metadata.get("timestamp")
                    }
                })
        return blocks
    
    async def _extract_contract(self, content: bytes, filename: str) -> List[Dict]:
        text = content.decode('utf-8', errors='ignore')
        clauses = self._extract_contract_clauses(text)
        blocks = []
        for clause_name, clause_text in clauses.items():
            if len(clause_text.strip()) > 50:
                blocks.append({
                    "content": clause_text.strip(),
                    "source": filename,
                    "source_type": "contract",
                    "confidence": 0.88,
                    "provenance_score": 0.92,
                    "tags": ["contract", "legal", clause_name.lower()],
                    "metadata": {"clause": clause_name}
                })
        return blocks
    
    async def _extract_generic(self, content: bytes, filename: str) -> List[Dict]:
        text = content.decode('utf-8', errors='ignore')
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
        blocks = []
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) > 50:
                blocks.append({
                    "content": chunk.strip(),
                    "source": filename,
                    "source_type": "generic",
                    "confidence": 0.70,
                    "provenance_score": 0.60,
                    "tags": ["generic", "document"],
                    "metadata": {"chunk": i+1}
                })
        return blocks
    
    def _extract_clinical_sections(self, text: str) -> Dict[str, str]:
        sections = {}
        patterns = [
            (r"(?i)HISTORY OF PRESENTING COMPLAINT[:.](.*?)(?=\n\n|\Z)", "HPC"),
            (r"(?i)PAST MEDICAL HISTORY[:.](.*?)(?=\n\n|\Z)", "PMH"),
            (r"(?i)MEDICATIONS[:.](.*?)(?=\n\n|\Z)", "Medications"),
            (r"(?i)ALLERGIES[:.](.*?)(?=\n\n|\Z)", "Allergies"),
            (r"(?i)EXAMINATION[:.](.*?)(?=\n\n|\Z)", "Examination"),
            (r"(?i)IMPRESSION[:.](.*?)(?=\n\n|\Z)", "Impression"),
            (r"(?i)PLAN[:.](.*?)(?=\n\n|\Z)", "Plan")
        ]
        for pattern, name in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                sections[name] = match.group(1).strip()
        if not sections:
            sections["Full Text"] = text
        return sections
    
    def _extract_contract_clauses(self, text: str) -> Dict[str, str]:
        clauses = {}
        section_pattern = r"(?:Section|ARTICLE|Clause)\s+(\d+[\.\d]*)\s*[:. ]+(.*?)(?=\s*(?:Section|ARTICLE|Clause)\s+\d+|\Z)"
        matches = re.findall(section_pattern, text, re.DOTALL)
        if matches:
            for number, content in matches:
                clauses[f"Section_{number}"] = content.strip()
        else:
            parts = re.split(r'\b(?:WHEREAS|THEREFORE|NOW, THEREFORE|IN WITNESS)\b', text, flags=re.IGNORECASE)
            for i, part in enumerate(parts):
                if len(part.strip()) > 100:
                    clauses[f"Clause_{i+1}"] = part.strip()
        if not clauses:
            clauses["Full Text"] = text
        return clauses
    
    def _generate_attestation(self, content: str, metadata: Dict) -> str:
        """Generate a basic attestation for the evidence block."""
        data_to_sign = f"{content[:100]}{json.dumps(metadata)}{datetime.utcnow().isoformat()}"
        return f"vap:sha256:{hashlib.sha256(data_to_sign.encode()).hexdigest()[:32]}"

    async def _store_evidence_block(self, block_data: Dict, job_id: int) -> Dict:
        content = block_data.get("content", "")
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        block_id = f"ev_{content_hash[:16]}"
        
        stmt = select(EvidenceBlock).where(EvidenceBlock.block_id == block_id)
        result = await self.db.execute(stmt)
        existing = result.scalars().first()
        
        if existing:
            return {"id": existing.id, "block_id": existing.block_id, "exists": True}
        
        # We need a way to assess quality during extraction
        from app.services.evidence_quality import EvidenceQualityAssessment
        
        # Temporary block object for assessment
        temp_block = EvidenceBlock(**{
            "block_id": block_id, "content": content, "content_hash": content_hash,
            "source": block_data.get("source"), "source_type": block_data.get("source_type"),
            "tags": block_data.get("tags"), "block_metadata": block_data.get("metadata", {})
        })
        assessment = EvidenceQualityAssessment.assess(temp_block)
        
        attestation = self._generate_attestation(content, block_data.get("metadata", {}))
        
        block = EvidenceBlock(
            block_id=block_id,
            content=content,
            content_hash=content_hash,
            source=block_data.get("source", "unknown"),
            source_type=block_data.get("source_type", "generic"),
            block_metadata=block_data.get("metadata", {}),
            confidence=block_data.get("confidence", 0.8),
            provenance_score=block_data.get("provenance_score", 0.8),
            quality_score=assessment["score"],
            is_qualified=assessment["is_qualified"],
            tags=block_data.get("tags", []),
            verifiable_attestation=attestation,
            extracted_at=datetime.utcnow()
        )
        
        self.db.add(block)
        await self.db.flush()
        await self.db.refresh(block)
        
        # Integrate with GraphService
        from app.services.graph_service import graph_service
        graph_service.create_evidence_node(
            evidence_id=str(block.block_id),
            source_type=block.source_type,
            quality_score=block.quality_score
        )
        
        return {"id": block.id, "block_id": block.block_id, "exists": False}
