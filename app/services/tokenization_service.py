import re
import uuid
import hashlib
from typing import Dict, Tuple # Ensure typing is imported

class TokenizationService:
    """
    Tokenizes personal data before it leaves the safe environment.
    """
    
    def __init__(self):
        self.token_mappings: Dict[str, Tuple[int, str]] = {} 
        self.revocation_list = set()
    
    def tokenize_data(self, data: str, user_id: int) -> str:
        """
        Identifies PII using entity patterns and replaces them with transient tokens.
        """
        pii_patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "EMAIL"),
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "PHONE"),
            (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', "IP")
        ]
        
        result = data
        for pattern, label in pii_patterns:
            def replace_match(match):
                val = match.group(0)
                token = hashlib.sha256(f"{user_id}:{val}:{uuid.uuid4()}".encode()).hexdigest()
                self.token_mappings[token] = (user_id, val)
                return f"PV_TOKEN_{token[:16]}"

            result = re.sub(pattern, replace_match, result)
            
        return result
    
    def detokenize_data(self, token_str: str, user_id: int) -> str:
        """
        Convert token back to original data.
        """
        clean_token = token_str.replace("PV_TOKEN_", "")
        for full_token, mapping in self.token_mappings.items():
            if full_token.startswith(clean_token):
                if full_token in self.revocation_list:
                    return "[REVOKED]"
                if mapping[0] != user_id:
                    return "[ACCESS DENIED]"
                return mapping[1]
        return "[TOKEN NOT FOUND]"

    def revoke_token(self, token: str):
        self.revocation_list.add(token.replace("PV_TOKEN_", ""))

# Instantiate a global service instance for use throughout the application
tokenization_service = TokenizationService()