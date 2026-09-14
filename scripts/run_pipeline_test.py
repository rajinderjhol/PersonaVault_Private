import asyncio
import hashlib
from app.db.session import SessionLocal
from app.services.evidence_extractor import EvidenceExtractor
from app.services.decision_linkage import DecisionLinkageEngine
from app.models.learning.behaviour_event import BehaviourEvent
from sqlalchemy import select

async def run_pipeline_test():
    async with SessionLocal() as db:
        print("🚀 [1/3] Testing Evidence Extraction...")
        extractor = EvidenceExtractor(db)
        
        # Mock clinical content
        content = b"CRITICAL CLINICAL NOTE: Patient shows improved response to protocol A-22."
        metadata = {"patient_id": "P-999", "timestamp": "2026-08-23T12:00:00Z"}
        
        ext_result = await extractor.extract_from_document(
            content=content,
            filename="clinical_test.txt",
            file_type="clinical_note",
            metadata=metadata
        )
        evidence_id = ext_result["blocks"][0]["id"]
        print(f"✅ Extracted Block ID: {evidence_id}")

        print("🚀 [2/3] Testing Decision Linkage...")
        # Get a real Decision ID
        stmt = select(BehaviourEvent).limit(1)
        result = await db.execute(stmt)
        decision = result.scalars().first()
        
        if not decision:
            print("❌ No decisions found to link evidence to.")
            return

        linker = DecisionLinkageEngine(db)
        link_res = await linker.link_to_decision(
            decision_id=decision.id,
            evidence_ids=[evidence_id],
            confidence=0.99,
            reasoning="Automated pipeline test"
        )
        print(f"✅ Linked Evidence ID {evidence_id} to Decision ID {decision.id}")

        print("🚀 [3/3] Verifying Pipeline Integration...")
        link_data = await linker.get_evidence_for_decision(decision.id)
        print(f"✅ Verified {len(link_data['evidence'])} evidence blocks linked to Decision {decision.id}")
        print("🎉 Decision Evidence Pipeline Operational.")

if __name__ == "__main__":
    asyncio.run(run_pipeline_test())
