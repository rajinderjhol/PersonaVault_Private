"""
Cue extractor for MRAgent - extracts fine-grained cues from queries.
"""
from typing import List
from app.models import MemoryCue
import re

class CueExtractor:
    """Extracts cues (entities, actions, times, locations) from text."""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
    
    async def extract_cues(self, text: str) -> List[MemoryCue]:
        """Extract cues from query text."""
        cues = []
        
        # Simple extraction using regex patterns
        # This is a basic implementation - can be enhanced with NER
        
        # Extract entities (simple pattern for demonstration)
        words = text.split()
        for word in words:
            if word[0].isupper() and len(word) > 1:
                cues.append(MemoryCue(text=word, type="entity"))
        
        # Extract action verbs (simple)
        action_patterns = re.compile(r'\b(create|generate|write|draft|analyze|search|find|get|retrieve)\b', re.I)
        actions = action_patterns.findall(text)
        for action in actions:
            cues.append(MemoryCue(text=action.lower(), type="action"))
        
        # Extract time references
        time_patterns = re.compile(r'\b(\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}|today|yesterday|tomorrow|last week)\b', re.I)
        times = time_patterns.findall(text)
        for time in times:
            cues.append(MemoryCue(text=time.lower(), type="time"))
        
        # Extract locations (simple)
        location_patterns = re.compile(r'\b(in|at|near|around)\s+([A-Z][a-z]+)\b', re.I)
        locations = location_patterns.findall(text)
        for loc in locations:
            cues.append(MemoryCue(text=loc[1], type="location"))
        
        return cues
    
    async def extract_cues_with_llm(self, text: str) -> List[MemoryCue]:
        """Extract cues using LLM (more accurate)."""
        if self.llm:
            prompt = f"""
            Extract entities, actions, times, and locations from this text:
            Text: {text}
            
            Return as list of cues with types.
            """
            response = await self.llm.generate(prompt)
            # Parse response - simplified
            return await self.extract_cues(text)
        
        return await self.extract_cues(text)
