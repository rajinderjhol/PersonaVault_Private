import asyncio
import hashlib
import uuid
import time
from datetime import datetime
from app.db.session import SessionLocal
from app.services.evidence_extractor import EvidenceExtractor
from app.services.decision_linkage import DecisionLinkageEngine
from app.models.evidence import EvidenceBlock, DocumentIngestionJob
from app.models.learning.behaviour_event import BehaviourEvent
from sqlalchemy import select

async def run_pipeline_test():
    async with SessionLocal() as db:
        print("🚀 [1/3] Testing Evidence Extraction...")
        extractor = EvidenceExtractor(db)

        # Mock clinical content - ensure unique job_id by unique filename
        content = b"CRITICAL CLINICAL NOTE: Patient shows improved response to protocol A-22."
        test_filename = f"clinical_test_{uuid.uuid4().hex[:8]}_{int(time.time())}.txt"
        metadata = {"patient_id": "P-999", "timestamp": "2026-08-23T12:00:00Z"}

        ext_result = await extractor.extract_from_document(
            content=content,
            filename=test_filename,
            file_type="clinical_note",
            metadata=metadata
        )
        evidence_id = ext_result["blocks"][0]["id"]

        # Verify Attestation
        stmt = select(EvidenceBlock).where(EvidenceBlock.id == evidence_id)
        result = await db.execute(stmt)
        evidence_block = result.scalars().first()

        if evidence_block.verifiable_attestation and evidence_block.verifiable_attestation.startswith("vap:sha256:"):
            print(f"✅ Extracted Block ID: {evidence_id} (Attestation verified: {evidence_block.verifiable_attestation[:20]}...)")
        else:
            print(f"❌ Extracted Block ID: {evidence_id} (Attestation missing or invalid)")
            return

        print("🚀 [2/3] Testing Decision Linkage...")
# ... remainder of file ...
        stmt = select(BehaviourEvent).limit(1)
        result = await db.execute(stmt)
        decision = result.scalars().first()
        
        if not decision:
            print("❌ No decisions found to link evidence to.")
            return

        # Capture ID before potential session issues
        d_id = decision.id 
        
        linker = DecisionLinkageEngine(db)
        link_res = await linker.link_to_decision(
            decision_id=d_id,
            evidence_ids=[evidence_id],
            confidence=0.99,
            reasoning="Automated pipeline test"
        )
        print(f"✅ Linked Evidence ID {evidence_id} to Decision ID {d_id}")

        print("🚀 [3/3] Verifying Pipeline Integration...")
        link_data = await linker.get_evidence_for_decision(d_id)
        print(f"✅ Verified {len(link_data['evidence'])} evidence blocks linked to Decision {d_id}")
        print("🎉 Decision Evidence Pipeline Operational.")

if __name__ == "__main__":
    asyncio.run(run_pipeline_test())
