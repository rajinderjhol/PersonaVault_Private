"""
Clinical Validator Agent - Validates clinical reasoning against policies.
Always runs locally for HIPAA compliance and air-gapped environments.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.swarm.base import BaseAgent

logger = logging.getLogger(__name__)


class ClinicalValidatorAgent(BaseAgent):
    """
    Validates clinical reasoning against policies and guidelines.
    Runs locally to ensure HIPAA compliance and data sovereignty.
    """
    
    def __init__(self, client=None):
        super().__init__("clinical_validator", client)
        self.policies = {}
        self.compliance_rules = []
        self.hipaa_patterns = self._load_hipaa_patterns()
        logger.info("ClinicalValidatorAgent initialized")
    
    async def validate(
        self, 
        response: str, 
        policies: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate clinical response against all applicable policies.
        
        Args:
            response: Clinical reasoning response to validate
            policies: Policy definitions
            context: Clinical context
        
        Returns:
            Validation result with pass/fail, constraints, and audit trail
        """
        context = context or {}
        violations = []
        warnings = []
        constraints = []
        
        # 1. HIPAA Compliance Check
        hipaa_result = await self._validate_hipaa(response, context)
        if not hipaa_result["passed"]:
            violations.extend(hipaa_result.get("violations", []))
            constraints.append({"type": "hipaa", "constraints": hipaa_result.get("constraints", [])})
        
        # 2. Policy Validation
        for policy_name, policy in policies.items():
            policy_result = await self._validate_policy(response, policy, context)
            if not policy_result["passed"]:
                violations.append({
                    "policy": policy_name,
                    "violations": policy_result.get("violations", [])
                })
                if policy_result.get("constraints"):
                    constraints.append({"type": policy_name, "constraints": policy_result["constraints"]})
        
        # 3. Clinical Protocol Check
        protocol_result = await self._validate_clinical_protocols(response, context)
        if not protocol_result["passed"]:
            warnings.append(protocol_result.get("warnings", []))
        
        # 4. Generate comprehensive result
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "constraints": constraints,
            "confidence_penalty": len(violations) * 0.15 + len(warnings) * 0.05,
            "audit_trail": {
                "validated_at": datetime.now().isoformat(),
                "policies_checked": list(policies.keys()),
                "violations_found": len(violations),
                "warnings_found": len(warnings)
            }
        }
    
    async def _validate_hipaa(self, response: str, context: Dict) -> Dict:
        """Validate HIPAA compliance of the response."""
        violations = []
        constraints = []
        
        # Check for PHI (Protected Health Information)
        for pattern_name, pattern in self.hipaa_patterns.items():
            if pattern["regex"].search(response):
                violations.append({
                    "type": "phi_detected",
                    "pattern": pattern_name,
                    "description": pattern["description"],
                    "severity": "critical"
                })
                constraints.append({
                    "type": "redact_phi",
                    "pattern": pattern_name,
                    "action": "redact"
                })
        
        # Check for required HIPAA disclaimers
        required_disclaimers = [
            "This is for clinical decision support",
            "consult with a qualified healthcare professional",
            "not a definitive diagnosis"
        ]
        
        missing_disclaimers = [
            d for d in required_disclaimers 
            if d.lower() not in response.lower()
        ]
        
        if missing_disclaimers:
            violations.append({
                "type": "missing_disclaimer",
                "disclaimers": missing_disclaimers,
                "severity": "medium"
            })
        
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "constraints": constraints
        }
    
    async def _validate_policy(self, response: str, policy: Dict, context: Dict) -> Dict:
        """Validate response against a specific policy."""
        violations = []
        constraints = []
        
        rules = policy.get("rules", [])
        for rule in rules:
            condition = rule.get("if", "")
            action = rule.get("then", "")
            
            # Check if condition is met in response
            if self._check_condition(response, condition):
                # Check if action is properly taken
                if not self._check_action(response, action):
                    violations.append({
                        "rule": condition,
                        "expected_action": action,
                        "actual": "Missing"
                    })
                    constraints.append({
                        "rule": condition,
                        "expected_action": action
                    })
        
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "constraints": constraints
        }
    
    async def _validate_clinical_protocols(self, response: str, context: Dict) -> Dict:
        """Validate against clinical protocols and guidelines."""
        warnings = []
        
        # Check for evidence-based terms
        evidence_terms = ["evidence", "study", "trial", "guideline", "recommendation"]
        has_evidence = any(term in response.lower() for term in evidence_terms)
        
        if not has_evidence:
            warnings.append("Response lacks explicit evidence-based references")
        
        # Check for confidence statement
        if "confidence" not in response.lower():
            warnings.append("Response does not include confidence level")
        
        return {
            "passed": len(warnings) == 0,
            "warnings": warnings
        }
    
    def _load_hipaa_patterns(self) -> Dict:
        """Load HIPAA PHI detection patterns."""
        return {
            "patient_name": {
                "regex": re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', re.IGNORECASE),
                "description": "Patient name detected (two capitalized words)"
            },
            "medical_record": {
                "regex": re.compile(r'MRN\s*[A-Z0-9\-]+', re.IGNORECASE),
                "description": "Medical Record Number detected"
            },
            "date_of_birth": {
                "regex": re.compile(r'(DOB|birth)\s*:?\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', re.IGNORECASE),
                "description": "Date of Birth detected"
            },
            "phone": {
                "regex": re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
                "description": "Phone number detected"
            },
            "email": {
                "regex": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                "description": "Email address detected"
            }
        }
    
    def _check_condition(self, response: str, condition: str) -> bool:
        """Check if a condition is met in the response."""
        # Simple keyword matching
        keywords = condition.lower().split()
        return any(kw in response.lower() for kw in keywords)
    
    def _check_action(self, response: str, action: str) -> bool:
        """Check if an action is properly taken in the response."""
        # Simple keyword matching for action
        keywords = action.lower().split()
        return any(kw in response.lower() for kw in keywords)
