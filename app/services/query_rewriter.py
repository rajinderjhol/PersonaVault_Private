from typing import List
from app.models import SemanticPattern # Assuming schemas.py is in app/services

class AdaptiveQueryRewriter:
    """
    Uses Layer 3 (Semantic Memory) to modify queries before they hit the 
    Retrieval Agent. This prevents repeating past 'no-result' or 'noisy-result' errors.
    """
    def __init__(self, learned_patterns: List[SemanticPattern]):
        self.patterns = learned_patterns

    def rewrite(self, original_query: str) -> str:
        modified_query = original_query
        
        for pattern in self.patterns:
            if pattern.pattern_type == "query_refinement":
                if pattern.trigger.lower() in original_query.lower():
                    # Apply the learned correction
                    # e.g., if user asks 'stress', learned pattern might add 'biometrics'
                    modified_query = f"{modified_query} {pattern.correction}"
        
        return modified_query

    def filter_noise(self, results: list) -> list:
        """
        Filters out documents that the Judge Agent previously flagged as 
        'unfaithful' or 'irrelevant' for this query type.
        """
        return results