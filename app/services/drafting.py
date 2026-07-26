import logging
from typing import Dict, Any
from app.swarm.core.generator import GeneratorAgent
from app.swarm.core.judge import JudgeAgent
from app.schemas.memory_schemas import MemoryResult

logger = logging.getLogger(__name__)

class LegalDrafter:
    """Drafts legal documents using PersonaVault's generator agent."""
    
    def __init__(self):
        self.generator = GeneratorAgent()
        self.judge = JudgeAgent()
        logger.info("LegalDrafter initialized")
    
    async def draft_document(self,
                            template_text: str,
                            variables: dict,
                            instructions: str) -> Dict[str, Any]:
        """
        Draft a legal document from a template.
        """
        try:
            logger.info(f"Drafting document with template: {template_text[:50]}...")
            
            # Replace variables in template
            filled_template = template_text
            for k, v in variables.items():
                # Support both {{var}} and {var}
                filled_template = filled_template.replace(f"{{{{{k}}}}}", str(v))
                filled_template = filled_template.replace(f"{{{k}}}", str(v))
            
            # Create MemoryResult object with variables in metadata for the generator
            context = [MemoryResult(
                content=filled_template, 
                source="template", 
                score=1.0,
                metadata={"variables": variables}
            )]
            
            # Use Generator Agent for refinement
            res = await self.generator.generate(instructions, context)
            
            # Extract the answer (the draft document)
            draft_text = res.get("answer", filled_template)
            
            # Optionally, use Judge Agent to evaluate the draft
            # For now, just return the draft
            
            return {
                "status": "success",
                "draft": draft_text,
                "source": res.get("source", "generator"),
                "warning": res.get("warning", None)
            }
        except Exception as e:
            logger.error(f"Error in draft_document: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
