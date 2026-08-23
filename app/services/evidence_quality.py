"""
Evidence Quality Assessment - Governs what becomes Decision Evidence.
"""
from typing import Dict, Any, List
from app.services.evidence_extractor import EvidenceBlock

class EvidenceQualityAssessment:
    """
    Assesses whether evidence is qualified to anchor a decision.
    """
    
    @staticmethod
    def assess(evidence: EvidenceBlock) -> Dict:
        """
        Assess evidence quality.
        """
        score = 0.0
        
        # 1. Source authenticated?
        if evidence.source and evidence.source != "unknown":
            score += 0.25
        
        # 2. Timestamp present?
        if evidence.block_metadata.get("timestamp"):
            score += 0.25
        
        # 3. Content length (meaningful evidence)
        if len(evidence.content) > 100:
            score += 0.25
        
        # 4. Tags present (domain classification)
        if evidence.tags:
            score += 0.25
        
        return {
            "score": score,
            "is_qualified": score >= 0.6,
            "reason": "Qualified evidence" if score >= 0.6 else "Insufficient evidence quality",
            "details": {
                "source_authenticated": evidence.source != "unknown",
                "has_timestamp": bool(evidence.block_metadata.get("timestamp")),
                "meaningful_content": len(evidence.content) > 100,
                "has_tags": bool(evidence.tags)
            }
        }
    
    @staticmethod
    def get_governance_verdict(score: float) -> str:
        """Return governance verdict based on score."""
        if score >= 0.8:
            return "HIGH_CONFIDENCE"
        elif score >= 0.6:
            return "MEDIUM_CONFIDENCE"
        else:
            return "LOW_CONFIDENCE"
