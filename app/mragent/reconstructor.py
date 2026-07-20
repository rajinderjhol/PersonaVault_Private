"""
Active memory reconstruction service - MRAgent core implementation.
"""
import asyncio
from typing import List, Dict, Any, Optional
from app.models import MemoryCue, MemoryContent, MemoryTag
from app.mragent.cue_extractor import CueExtractor
from app.mragent.tag_selector import TagSelector
import logging

logger = logging.getLogger(__name__)

class ActiveMemoryReconstructor:
    """
    Active memory reconstruction inspired by MRAgent paper.
    Iteratively refines retrieval based on accumulated evidence.
    """
    
    def __init__(self, llm_client=None, vector_store=None, graph_store=None, max_turns: int = 3):
        self.llm = llm_client
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.max_turns = max_turns
        self.cue_extractor = CueExtractor(llm_client)
        self.tag_selector = TagSelector(llm_client)
        logger.info(f"ActiveMemoryReconstructor initialized with max_turns={max_turns}")
    
    async def reconstruct(self, query: str, user_id: int = 1) -> Dict[str, Any]:
        """
        Main reconstruction loop.
        """
        logger.info(f"Starting reconstruction for: {query[:50]}...")
        
        # Step 1: Extract initial cues
        cues = await self.cue_extractor.extract_cues(query)
        logger.info(f"Extracted {len(cues)} cues")
        
        accumulated_evidence = []
        reconstruction_turns = []
        
        # Step 2: Iterative reconstruction loop
        for turn in range(self.max_turns):
            logger.info(f"Reconstruction turn {turn + 1}/{self.max_turns}")
            
            # Select tags based on current cues and evidence
            tags = await self.tag_selector.select_tags(cues, accumulated_evidence)
            logger.info(f"Selected {len(tags)} tags")
            
            # Retrieve content using cues and tags
            content = await self._retrieve_content(cues, tags, user_id)
            logger.info(f"Retrieved {len(content)} content items")
            
            # Add to accumulated evidence
            accumulated_evidence.extend(content)
            
            # Update cues based on new evidence (active feedback)
            new_cues = await self._update_cues(cues, content)
            if new_cues:
                cues = new_cues
                logger.info(f"Updated cues: {len(cues)}")
            
            # Record turn
            reconstruction_turns.append({
                "turn": turn + 1,
                "cues": [c.text for c in cues],
                "tags": [t.text for t in tags],
                "evidence_count": len(accumulated_evidence)
            })
            
            # Check if evidence is sufficient
            if await self._is_sufficient(accumulated_evidence, query):
                logger.info(f"Evidence sufficient after {turn + 1} turns")
                break
        
        # Step 3: Generate answer
        answer = await self._generate_answer(query, accumulated_evidence)
        
        return {
            "answer": answer,
            "evidence": accumulated_evidence,
            "turns": reconstruction_turns,
            "total_evidence": len(accumulated_evidence)
        }
    
    async def _retrieve_content(self, cues: List[MemoryCue], tags: List[MemoryTag], user_id: int) -> List[MemoryContent]:
        """Retrieve content using vector store and graph store."""
        results = []
        
        # Build search query from cues and tags
        search_terms = [c.text for c in cues] + [t.text for t in tags]
        query = " ".join(search_terms)
        
        # Vector search
        if self.vector_store:
            try:
                vector_results = self.vector_store.search_similar(query, user_id, limit=5)
                for v in vector_results:
                    content = MemoryContent(
                        text=v.get("content", ""),
                        type="episodic",
                        metadata={"source": "vector", "score": v.get("score", 0)}
                    )
                    results.append(content)
            except Exception as e:
                logger.error(f"Vector search failed: {e}")
        
        # Graph search
        if self.graph_store:
            try:
                graph_results = self.graph_store.execute_query(f"MATCH (n) WHERE n.title CONTAINS '{query}' RETURN n")
                for g in graph_results:
                    content = MemoryContent(
                        text=g.get("n", {}).get("title", ""),
                        type="semantic",
                        metadata={"source": "graph"}
                    )
                    results.append(content)
            except Exception as e:
                logger.error(f"Graph search failed: {e}")
        
        return results
    
    async def _update_cues(self, current_cues: List[MemoryCue], new_content: List[MemoryContent]) -> List[MemoryCue]:
        """Update cues based on new evidence."""
        new_cues = list(current_cues)
        
        # Extract new cues from content
        for content in new_content:
            # Extract keywords from content
            words = content.text.split()
            for word in words:
                if len(word) > 3 and word[0].isalpha():
                    # Check if this word is already a cue
                    if not any(c.text.lower() == word.lower() for c in new_cues):
                        new_cues.append(MemoryCue(text=word.lower(), type="entity"))
        
        # Limit cues
        return new_cues[:20]  # Max 20 cues
    
    async def _is_sufficient(self, evidence: List[MemoryContent], query: str) -> bool:
        """Check if accumulated evidence is sufficient to answer the query."""
        if len(evidence) == 0:
            return False
        
        # Simple heuristic: if we have at least 2 pieces of evidence
        if len(evidence) >= 2:
            return True
        
        return False
    
    async def _generate_answer(self, query: str, evidence: List[MemoryContent]) -> str:
        """Generate final answer from accumulated evidence."""
        if not evidence:
            return "No evidence found to answer the query."
        
        # Build answer from evidence
        evidence_texts = [e.text for e in evidence]
        combined = " ".join(evidence_texts)
        
        if self.llm:
            try:
                prompt = f"""
                Query: {query}
                Evidence: {combined}
                Answer the query based on the evidence provided.
                """
                response = await self.llm.generate(prompt)
                return response.get("answer", combined)
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                return combined
        
        return combined

# Global instance
reconstructor = None

def get_reconstructor(llm_client=None, vector_store=None, graph_store=None):
    """Get or create a reconstructor instance."""
    global reconstructor
    if reconstructor is None:
        reconstructor = ActiveMemoryReconstructor(llm_client, vector_store, graph_store)
    return reconstructor
