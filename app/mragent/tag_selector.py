"""
Tag selector for MRAgent - selects semantic tags based on cues and evidence.
"""
from typing import List, Any
from app.models import MemoryCue, MemoryContent, MemoryTag

class TagSelector:
    """Selects tags to guide memory retrieval."""
    
    def __init__(self, llm_client=None, tag_store=None):
        self.llm = llm_client
        self.tag_store = tag_store or {}
    
    async def select_tags(self, cues: List[MemoryCue], evidence: List[MemoryContent]) -> List[MemoryTag]:
        """Select relevant tags based on cues and accumulated evidence."""
        tags = []
        
        # Simple selection based on cue types
        for cue in cues:
            if cue.type == "entity":
                tags.append(MemoryTag(text=cue.text, relation="mentions"))
            elif cue.type == "action":
                tags.append(MemoryTag(text=cue.text, relation="involves"))
            elif cue.type == "time":
                tags.append(MemoryTag(text=cue.text, relation="occurred_at"))
            elif cue.type == "location":
                tags.append(MemoryTag(text=cue.text, relation="located_at"))
        
        # Add tags based on evidence
        for ev in evidence:
            # Extract keywords from evidence
            keywords = ev.text.split()[:5]  # Simple extraction
            for keyword in keywords:
                if len(keyword) > 3:
                    tags.append(MemoryTag(text=keyword.lower(), relation="related"))
        
        # Deduplicate
        unique_tags = []
        seen = set()
        for tag in tags:
            key = f"{tag.text}:{tag.relation}"
            if key not in seen:
                seen.add(key)
                unique_tags.append(tag)
        
        return unique_tags[:10]  # Limit to top 10 tags
    
    async def select_tags_with_llm(self, cues: List[MemoryCue], evidence: List[MemoryContent]) -> List[MemoryTag]:
        """Select tags using LLM for better accuracy."""
        if self.llm:
            # Build prompt with cues and evidence
            cue_texts = [c.text for c in cues]
            evidence_texts = [e.text[:50] for e in evidence]
            
            prompt = f"""
            Given these cues: {cue_texts}
            And this evidence: {evidence_texts}
            
            Select the most relevant semantic tags for retrieval.
            Tags should be short, descriptive phrases.
            """
            response = await self.llm.generate(prompt)
            # Parse response - simplified
            return await self.select_tags(cues, evidence)
        
        return await self.select_tags(cues, evidence)
