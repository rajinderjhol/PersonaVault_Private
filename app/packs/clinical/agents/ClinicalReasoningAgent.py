"""
Clinical Reasoning Agent - Core reasoning engine for clinical DIU.
Supports frontier models (OpenAI, Anthropic, Gemini) with local fallback.
Implements the Self-Improving Crystallization Loop for clinical domain.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime

import httpx

from app.swarm.base import BaseAgent

logger = logging.getLogger(__name__)


class ClinicalReasoningAgent(BaseAgent):
    """
    Clinical reasoning agent that connects to frontier models for deep reasoning.
    Designed for HIPAA-compliant clinical decision support with full auditability.
    """
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        super().__init__("clinical_reasoning", client)
        
        # API Keys (optional, for frontier models)
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        
        # Local fallback
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.local_model = os.getenv("CLINICAL_LOCAL_MODEL", "clinical-qwen")
        
        # Crystallization
        self.last_reasoning_path = None
        self.last_confidence = 0.0
        
        # Clinical context
        self.clinical_domains = [
            "diagnosis", "treatment", "triage", "medication",
            "patient_history", "symptom_analysis", "risk_assessment"
        ]
        
        logger.info("ClinicalReasoningAgent initialized")
        logger.info(f"  Frontier models: {bool(self.openai_key or self.anthropic_key or self.gemini_key or self.groq_key)}")
        logger.info(f"  Local model: {self.local_model}")
    
    async def stream(
        self, 
        query: str, 
        context: Dict[str, Any] = None,
        model: str = "frontier"
    ) -> AsyncGenerator[str, None]:
        """
        Stream clinical reasoning from the selected model.
        
        Args:
            query: Clinical query
            context: Clinical context (patient info, history, etc.)
            model: 'frontier', 'openai', 'anthropic', 'gemini', 'groq', 'local'
        """
        context = context or {}
        
        # Build clinical prompt
        prompt = self._build_clinical_prompt(query, context)
        
        # Route to appropriate model
        if model == "frontier" or model == "auto":
            # Auto-select the best available model
            selected_model = self._select_frontier_model()
            if selected_model:
                async for chunk in self._stream_frontier(prompt, selected_model):
                    yield chunk
                return
        
        if model == "openai" and self.openai_key:
            async for chunk in self._stream_openai(prompt):
                yield chunk
            return
        
        elif model == "anthropic" and self.anthropic_key:
            async for chunk in self._stream_anthropic(prompt):
                yield chunk
            return
        
        elif model == "gemini" and self.gemini_key:
            async for chunk in self._stream_gemini(prompt):
                yield chunk
            return
        
        elif model == "groq" and self.groq_key:
            async for chunk in self._stream_groq(prompt):
                yield chunk
            return
        
        # Fallback to local model
        logger.warning(f"Frontier model unavailable, falling back to local: {self.local_model}")
        async for chunk in self._stream_local(prompt):
            yield chunk
    
    async def reason(
        self, 
        query: str, 
        context: Dict[str, Any] = None,
        local_only: bool = False
    ) -> Dict[str, Any]:
        """
        Non-streaming clinical reasoning with full trace.
        
        Args:
            query: Clinical query
            context: Clinical context
            local_only: Force local model (air-gapped mode)
        
        Returns:
            Dict with response, reasoning_path, confidence, and trace
        """
        context = context or {}
        
        # Build clinical prompt
        prompt = self._build_clinical_prompt(query, context)
        
        # Determine reasoning mode
        use_frontier = not local_only and self._has_frontier_available()
        
        try:
            if use_frontier:
                model = self._select_frontier_model()
                response = await self._reason_with_frontier(prompt, model)
                source = "frontier"
                confidence = 0.85  # Base confidence for frontier
            else:
                response = await self._reason_with_local(prompt)
                source = "local"
                confidence = 0.75  # Base confidence for local
            
            # Enhance confidence based on response quality
            confidence = self._calculate_clinical_confidence(response, context)
            
            # Store reasoning path for crystallization
            self.last_reasoning_path = {
                "query": query,
                "prompt": prompt,
                "response": response,
                "source": source,
                "timestamp": datetime.now().isoformat()
            }
            self.last_confidence = confidence
            
            # Generate auditable trace
            trace = self.create_trace(
                input_data=query,
                explanation=f"Clinical reasoning via {source}",
                confidence=confidence,
                decision="clinical_recommendation"
            )
            
            return {
                "response": response,
                "source": source,
                "confidence": confidence,
                "reasoning_path": self.last_reasoning_path,
                "trace": trace
            }
            
        except Exception as e:
            logger.error(f"Clinical reasoning failed: {e}")
            return {
                "response": f"Error: {str(e)}",
                "source": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _build_clinical_prompt(self, query: str, context: Dict) -> str:
        """Build a structured clinical prompt with domain-specific context."""
        
        # Extract clinical context
        patient_info = context.get("patient", {})
        symptoms = context.get("symptoms", [])
        history = context.get("history", [])
        vitals = context.get("vitals", {})
        
        # Build the prompt
        prompt_parts = []
        
        # System instruction
        prompt_parts.append("""You are a clinical reasoning AI assistant. 
Provide evidence-based, cautious, and well-reasoned clinical insights.
Always include:
1. Reasoning steps
2. Evidence cited
3. Confidence level
4. Alternative considerations
5. Clear recommendations

IMPORTANT: This is for clinical decision support, not definitive diagnosis.
Always recommend consultation with a qualified healthcare professional.
""")
        
        # Context
        if patient_info:
            prompt_parts.append(f"## Patient Information\n{json.dumps(patient_info, indent=2)}")
        
        if symptoms:
            prompt_parts.append(f"## Symptoms\n- " + "\n- ".join(symptoms))
        
        if history:
            prompt_parts.append(f"## Medical History\n- " + "\n- ".join(history))
        
        if vitals:
            prompt_parts.append(f"## Vital Signs\n{json.dumps(vitals, indent=2)}")
        
        # Query
        prompt_parts.append(f"## Clinical Query\n{query}")
        
        # Instructions for structured reasoning
        prompt_parts.append("""
## Response Structure
Please format your response as:
1. **Assessment**: Brief summary of the clinical situation
2. **Analysis**: Step-by-step reasoning with evidence
3. **Recommendations**: Specific, actionable suggestions
4. **Confidence**: Your confidence level (0-100%)
5. **Alternatives**: Other considerations or differentials
6. **Next Steps**: What should be done next
""")
        
        return "\n\n".join(prompt_parts)
    
    def _select_frontier_model(self) -> str:
        """Auto-select the best available frontier model."""
        # Priority: OpenAI > Anthropic > Gemini > Groq
        if self.openai_key:
            return "openai"
        elif self.anthropic_key:
            return "anthropic"
        elif self.gemini_key:
            return "gemini"
        elif self.groq_key:
            return "groq"
        return None
    
    def _has_frontier_available(self) -> bool:
        """Check if any frontier model is available."""
        return bool(self.openai_key or self.anthropic_key or self.gemini_key or self.groq_key)
    
    async def _stream_openai(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream from OpenAI API."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_key)
            
            stream = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                temperature=0.3
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            yield f"OpenAI error: {str(e)}"
    
    async def _stream_anthropic(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream from Anthropic Claude API."""
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.anthropic_key)
            
            stream = await client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    yield chunk.delta.text
                    
        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            yield f"Anthropic error: {str(e)}"
    
    async def _stream_gemini(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream from Google Gemini API."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            model = genai.GenerativeModel("gemini-pro")
            
            response = await model.generate_content_async(
                prompt,
                stream=True
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            yield f"Gemini error: {str(e)}"
    
    async def _stream_groq(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream from Groq API."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mixtral-8x7b-32768",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 1024,
                        "stream": True
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f"Groq streaming failed: {e}")
            yield f"Groq error: {str(e)}"
    
    async def _stream_local(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream from local Ollama model."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.local_model,
                        "prompt": prompt,
                        "stream": True,
                        "temperature": 0.3,
                        "options": {
                            "num_ctx": 4096,
                            "num_predict": 1024
                        }
                    }
                ) as response:
                    if response.status_code != 200:
                        yield f"Ollama error: {response.status_code}"
                        return
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f"Local model streaming failed: {e}")
            yield f"Local model error: {str(e)}"
    
    async def _reason_with_frontier(self, prompt: str, model: str) -> str:
        """Non-streaming reasoning with frontier model."""
        # Collect all chunks
        chunks = []
        async for chunk in self._stream_frontier(prompt, model):
            chunks.append(chunk)
        return "".join(chunks)
    
    async def _stream_frontier(self, prompt: str, model: str) -> AsyncGenerator[str, None]:
        """Stream from the selected frontier model."""
        if model == "openai":
            async for chunk in self._stream_openai(prompt):
                yield chunk
        elif model == "anthropic":
            async for chunk in self._stream_anthropic(prompt):
                yield chunk
        elif model == "gemini":
            async for chunk in self._stream_gemini(prompt):
                yield chunk
        elif model == "groq":
            async for chunk in self._stream_groq(prompt):
                yield chunk
        else:
            yield f"Unknown model: {model}"
    
    async def _reason_with_local(self, prompt: str) -> str:
        """Non-streaming reasoning with local model."""
        chunks = []
        async for chunk in self._stream_local(prompt):
            chunks.append(chunk)
        return "".join(chunks)
    
    def _calculate_clinical_confidence(self, response: str, context: Dict) -> float:
        """Calculate clinical confidence score based on response quality."""
        base = 0.7
        
        # Length indicator (more detailed = more confident)
        length_factor = min(len(response) / 500, 1.0)
        base += length_factor * 0.15
        
        # If response includes structured sections, boost confidence
        sections = ["Assessment", "Analysis", "Recommendations", "Confidence"]
        section_count = sum(1 for section in sections if section in response)
        base += (section_count / len(sections)) * 0.1
        
        # Cap at 0.95
        return min(base, 0.95)
