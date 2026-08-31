from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.decision_trace import DecisionTrace, ProvenanceRecord
from app.models.evidence import EvidenceBlock

class GraphBuilderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_decision_provenance_graph(self, decision_id: str) -> Dict[str, Any]:
        """Constructs a node/edge graph from SQL data for a specific decision."""
        
        # 1. Fetch Decision Trace
        stmt = select(DecisionTrace).where(DecisionTrace.decision_id == decision_id)
        result = await self.db.execute(stmt)
        trace = result.scalars().first()
        
        if not trace:
            return {"nodes": [], "edges": []}

        nodes = []
        edges = []
        
        # Add Decision Node
        nodes.append({
            "id": f"dec_{trace.decision_id}",
            "data": {"label": f"Decision: {trace.query[:30]}...", "type": "decision"},
            "type": "input"
        })
        
        # 2. Fetch Provenance Records (Evidence)
        stmt = select(ProvenanceRecord).where(ProvenanceRecord.trace_id == trace.id)
        result = await self.db.execute(stmt)
        provenance_records = result.scalars().all()
        
        for record in provenance_records:
            # Fetch Evidence Details
            stmt_ev = select(EvidenceBlock).where(EvidenceBlock.block_id == record.source_id)
            result_ev = await self.db.execute(stmt_ev)
            evidence = result_ev.scalars().first()
            
            ev_id = f"ev_{record.source_id}"
            nodes.append({
                "id": ev_id,
                "data": {"label": f"Evidence: {evidence.source if evidence else 'Unknown'}", "type": "evidence"},
            })
            
            edges.append({
                "id": f"e_{trace.decision_id}_{record.source_id}",
                "source": ev_id,
                "target": f"dec_{trace.decision_id}",
                "label": "USES_EVIDENCE"
            })
            
        return {"nodes": nodes, "edges": edges}
