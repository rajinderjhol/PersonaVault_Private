"""
Decision Linkage Engine - Links evidence to decisions.
"""
import json
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.learning.behaviour_event import BehaviourEvent
from app.models.evidence import EvidenceBlock, DecisionEvidenceLink

class DecisionLinkageEngine:
    """
    Links evidence blocks to decisions.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def link_to_decision(
        self,
        decision_id: int,
        evidence_ids: List[int],
        confidence: float = 0.8,
        reasoning: str = ""
    ) -> Dict:
        """
        Link evidence blocks to a decision using DecisionEvidenceLink.
        """
        # Validate decision exists
        stmt = select(BehaviourEvent).where(BehaviourEvent.id == decision_id)
        result = await self.db.execute(stmt)
        decision = result.scalars().first()
        
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")
        
        # Validate evidence blocks exist and create links
        linked = []
        for evidence_id in evidence_ids:
            stmt = select(EvidenceBlock).where(EvidenceBlock.id == evidence_id)
            result = await self.db.execute(stmt)
            evidence = result.scalars().first()
            
            if not evidence:
                continue
            
            # Create link
            link = DecisionEvidenceLink(
                decision_id=decision_id,
                evidence_id=evidence_id,
                confidence=confidence,
                reasoning=reasoning
            )
            self.db.add(link)
            linked.append({"evidence_id": evidence_id})
        
        await self.db.commit()
        
        return {
            "decision_id": decision_id,
            "linked_evidence": linked,
            "total": len(linked)
        }
    
    async def get_evidence_for_decision(self, decision_id: int) -> Dict:
        """
        Retrieve evidence for a decision.
        """
        stmt = select(DecisionEvidenceLink).where(DecisionEvidenceLink.decision_id == decision_id)
        result = await self.db.execute(stmt)
        links = result.scalars().all()
        
        evidence_list = []
        for link in links:
            stmt = select(EvidenceBlock).where(EvidenceBlock.id == link.evidence_id)
            result = await self.db.execute(stmt)
            evidence = result.scalars().first()
            if evidence:
                evidence_list.append({
                    "id": evidence.id,
                    "block_id": evidence.block_id,
                    "content": evidence.content[:500] + "..." if len(evidence.content) > 500 else evidence.content,
                    "source": evidence.source
                })
        
        return {
            "decision_id": decision_id,
            "evidence_count": len(evidence_list),
            "evidence": evidence_list
        }
        
    async def get_evidence_stats(self) -> Dict:
        """
        Get evidence statistics.
        """
        total_blocks = (await self.db.execute(select(func.count(EvidenceBlock.id)))).scalar_one() or 0
        total_links = (await self.db.execute(select(func.count(DecisionEvidenceLink.id)))).scalar_one() or 0
        qualified = (await self.db.execute(select(func.count(EvidenceBlock.id)).where(EvidenceBlock.is_qualified == True))).scalar_one() or 0
        
        return {
            "total_evidence_blocks": total_blocks,
            "qualified_evidence": qualified,
            "total_links": total_links,
            "quality_rate": qualified / total_blocks if total_blocks > 0 else 0
        }
