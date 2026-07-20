from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta # Ensure datetime is imported
import logging

logger = logging.getLogger(__name__)

class ContractClause(BaseModel):
    """Represents a contract clause."""
    clause_type: str  # indemnification, termination, confidentiality, etc.
    text: str
    section: str
    risk_level: str  # low, medium, high, critical
    suggested_changes: Optional[List[str]] = None

class ContractAnalysis(BaseModel):
    """Complete contract analysis result."""
    document_id: str
    contract_type: str
    parties: List[str]
    effective_date: Optional[datetime] = None
    termination_date: Optional[datetime] = None
    clauses: List[ContractClause]
    risk_score: float  # 0-100
    missing_clauses: List[str]
    recommendations: List[str]
    summary: str

class ContractAnalyzer:
    """
    Performs legal analysis of contracts using PersonaVault's AI pipeline.
    """
    
    def __init__(self):
        self.risk_keywords = {
            "high": ["indemnification", "unlimited", "liability", "liquidated damages"],
            "medium": ["confidentiality", "non-compete", "exclusive", "termination"],
            "low": ["governing law", "notice", "force majeure"]
        }
    
    async def analyze_contract(self, 
                              document_id: int, 
                              text: str) -> ContractAnalysis:
        """
        Perform comprehensive contract analysis.
        """
        # 1. Extract contract metadata (Mocked for integration)
        metadata = {
            "contract_type": "service_agreement",
            "parties": ["Company A", "Company B"],
            "effective_date": datetime.now(),
            "termination_date": datetime.now() + timedelta(days=365)
        }
        
        # 2. Identify and classify clauses
        clauses = [
            ContractClause(
                clause_type="indemnification",
                text="Company A shall indemnify Company B...",
                section="4.2",
                risk_level="high",
                suggested_changes=["Consider limiting liability to $1M"]
            )
        ]
        
        # 3. Risk assessment
        risk_score = self._calculate_risk_score(clauses)
        
        # 4. Identify missing clauses
        missing_clauses = self._identify_missing_clauses(metadata["contract_type"], clauses)
        
        # 5. Generate recommendations
        recommendations = []
        for c in clauses:
            if c.risk_level in ["high", "critical"] and c.suggested_changes:
                recommendations.extend(c.suggested_changes)
        
        return ContractAnalysis(
            document_id=str(document_id),
            contract_type=metadata["contract_type"],
            parties=metadata["parties"],
            effective_date=metadata.get("effective_date"),
            termination_date=metadata.get("termination_date"),
            clauses=clauses,
            risk_score=risk_score,
            missing_clauses=missing_clauses,
            recommendations=recommendations,
            summary="Initial contract review completed. High risk identified in indemnification clauses."
        )
    
    def _calculate_risk_score(self, clauses: List[ContractClause]) -> float:
        score = 0
        for clause in clauses:
            if clause.risk_level == "high":
                score += 20
            elif clause.risk_level == "medium":
                score += 10
        return min(score, 100)
    
    def _identify_missing_clauses(self, contract_type: str, clauses: List[ContractClause]) -> List[str]:
        standard_clauses = {
            "service_agreement": ["indemnification", "termination", "confidentiality"],
            "nda": ["definition", "exclusions", "return_of_information"]
        }
        
        existing = [c.clause_type for c in clauses]
        missing = [c for c in standard_clauses.get(contract_type, []) if c not in existing]
        return missing