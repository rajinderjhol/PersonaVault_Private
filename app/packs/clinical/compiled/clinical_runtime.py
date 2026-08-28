# clinical Runtime v1.0.0
# Domain: healthcare
# Compiled: 2026-08-28T09:09:33.399048
# Target: airgap
# Pattern Count: 0
# Agent Count: 2
# Policy Count: 2
#
# This runtime is AUTO-GENERATED. Do not edit manually.
# To modify, update the source DIU and recompile.

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

CONFIG = {"agents": [{"class": "ClinicalReasoningAgent", "fallback": "ollama/clinical-qwen", "model": "frontier"}, {"class": "ClinicalValidatorAgent", "fallback": "local", "model": "local"}], "compiler": {"optimization": "high", "signing": "required", "target": "airgap"}, "crystallized": [{"file": "crystallized/diagnosis_patterns.json", "source": "evidence_based_medicine"}], "description": "Clinical decision support with HIPAA-compliant reasoning", "domain": "healthcare", "name": "clinical", "version": "1.0.0"}

# ============================================================
# POLICIES (Compiled from declarative YAML)
# ============================================================

POLICIES = {"diagnostic_protocols": {"description": "Evidence-based diagnostic protocols", "domain": "clinical", "guidelines": [{"evidence_level": "A", "last_updated": "2026-01-15", "source": "National Institutes of Health", "url": "https://www.nih.gov/guidelines"}, {"evidence_level": "A", "last_updated": "2026-01-15", "source": "World Health Organization", "url": "https://www.who.int/guidelines"}, {"evidence_level": "A", "last_updated": "2026-01-15", "source": "American Medical Association", "url": "https://www.ama-assn.org/guidelines"}], "name": "Diagnostic Protocols", "protocols": [{"id": "DGN-001", "name": "Triage Assessment", "steps": ["Airway assessment", "Breathing assessment", "Circulation assessment", "Disability assessment", "Exposure assessment"]}, {"id": "DGN-002", "name": "Differential Diagnosis", "steps": ["Symptom analysis", "Risk factor identification", "Possible conditions list", "Evidence weighting", "Most likely diagnosis"]}, {"id": "DGN-003", "name": "Treatment Planning", "steps": ["Diagnosis confirmation", "Treatment options evaluation", "Evidence-based selection", "Patient factors consideration", "Plan documentation"]}], "version": "1.0.0"}, "hipaa": {"compliance_requirements": ["Patient data must be encrypted at rest and in transit", "All access to clinical data must be logged", "Data retention policies must be enforced", "Breach notification procedures must be in place"], "description": "HIPAA compliance rules for clinical reasoning", "domain": "clinical", "name": "HIPAA Compliance", "rules": [{"description": "PHI must be redacted or anonymized", "enforcement": "mandatory", "id": "HIPAA-001", "if": "contains_phi", "name": "PHI Redaction", "severity": "critical", "then": "redact_and_anonymize"}, {"description": "Must include clinical decision support disclaimer", "enforcement": "mandatory", "id": "HIPAA-002", "if": "contains_clinical_advice", "name": "Clinical Disclaimer", "severity": "medium", "then": "include_disclaimer"}, {"description": "All clinical decisions must have audit trail", "enforcement": "mandatory", "id": "HIPAA-003", "if": "clinical_decision", "name": "Audit Trail", "severity": "critical", "then": "generate_audit_trail"}, {"description": "Clinical data must stay within jurisdiction", "enforcement": "mandatory", "id": "HIPAA-004", "if": "contains_patient_data", "name": "Data Sovereignty", "severity": "critical", "then": "ensure_data_sovereignty"}], "version": "1.0.0"}}

# ============================================================
# CRYSTALLIZED PATTERNS (Pre-loaded from JSON)
# ============================================================

CRYSTALLIZED_PATTERNS = []

# ============================================================
# AGENTS (Bundled code)
# ============================================================


# Agent: ClinicalReasoningAgent
# Model: frontier
# Source: ClinicalReasoningAgent.py
&#34;&#34;&#34;
Clinical Reasoning Agent - Core reasoning engine for clinical DIU.
Supports frontier models (OpenAI, Anthropic, Gemini) with local fallback.
Implements the Self-Improving Crystallization Loop for clinical domain.
&#34;&#34;&#34;

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
    &#34;&#34;&#34;
    Clinical reasoning agent that connects to frontier models for deep reasoning.
    Designed for HIPAA-compliant clinical decision support with full auditability.
    &#34;&#34;&#34;
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        super().__init__(&#34;clinical_reasoning&#34;, client)
        
        # API Keys (optional, for frontier models)
        self.openai_key = os.getenv(&#34;OPENAI_API_KEY&#34;)
        self.anthropic_key = os.getenv(&#34;ANTHROPIC_API_KEY&#34;)
        self.gemini_key = os.getenv(&#34;GEMINI_API_KEY&#34;)
        self.groq_key = os.getenv(&#34;GROQ_API_KEY&#34;)
        
        # Local fallback
        self.ollama_url = os.getenv(&#34;OLLAMA_BASE_URL&#34;, &#34;http://localhost:11434&#34;)
        self.local_model = os.getenv(&#34;CLINICAL_LOCAL_MODEL&#34;, &#34;clinical-qwen&#34;)
        
        # Crystallization
        self.last_reasoning_path = None
        self.last_confidence = 0.0
        
        # Clinical context
        self.clinical_domains = [
            &#34;diagnosis&#34;, &#34;treatment&#34;, &#34;triage&#34;, &#34;medication&#34;,
            &#34;patient_history&#34;, &#34;symptom_analysis&#34;, &#34;risk_assessment&#34;
        ]
        
        logger.info(&#34;ClinicalReasoningAgent initialized&#34;)
        logger.info(f&#34;  Frontier models: {bool(self.openai_key or self.anthropic_key or self.gemini_key or self.groq_key)}&#34;)
        logger.info(f&#34;  Local model: {self.local_model}&#34;)
    
    async def stream(
        self, 
        query: str, 
        context: Dict[str, Any] = None,
        model: str = &#34;frontier&#34;
    ) -&gt; AsyncGenerator[str, None]:
        &#34;&#34;&#34;
        Stream clinical reasoning from the selected model.
        
        Args:
            query: Clinical query
            context: Clinical context (patient info, history, etc.)
            model: &#39;frontier&#39;, &#39;openai&#39;, &#39;anthropic&#39;, &#39;gemini&#39;, &#39;groq&#39;, &#39;local&#39;
        &#34;&#34;&#34;
        context = context or {}
        
        # Build clinical prompt
        prompt = self._build_clinical_prompt(query, context)
        
        # Route to appropriate model
        if model == &#34;frontier&#34; or model == &#34;auto&#34;:
            # Auto-select the best available model
            selected_model = self._select_frontier_model()
            if selected_model:
                async for chunk in self._stream_frontier(prompt, selected_model):
                    yield chunk
                return
        
        if model == &#34;openai&#34; and self.openai_key:
            async for chunk in self._stream_openai(prompt):
                yield chunk
            return
        
        elif model == &#34;anthropic&#34; and self.anthropic_key:
            async for chunk in self._stream_anthropic(prompt):
                yield chunk
            return
        
        elif model == &#34;gemini&#34; and self.gemini_key:
            async for chunk in self._stream_gemini(prompt):
                yield chunk
            return
        
        elif model == &#34;groq&#34; and self.groq_key:
            async for chunk in self._stream_groq(prompt):
                yield chunk
            return
        
        # Fallback to local model
        logger.warning(f&#34;Frontier model unavailable, falling back to local: {self.local_model}&#34;)
        async for chunk in self._stream_local(prompt):
            yield chunk
    
    async def reason(
        self, 
        query: str, 
        context: Dict[str, Any] = None,
        local_only: bool = False
    ) -&gt; Dict[str, Any]:
        &#34;&#34;&#34;
        Non-streaming clinical reasoning with full trace.
        
        Args:
            query: Clinical query
            context: Clinical context
            local_only: Force local model (air-gapped mode)
        
        Returns:
            Dict with response, reasoning_path, confidence, and trace
        &#34;&#34;&#34;
        context = context or {}
        
        # Build clinical prompt
        prompt = self._build_clinical_prompt(query, context)
        
        # Determine reasoning mode
        use_frontier = not local_only and self._has_frontier_available()
        
        try:
            if use_frontier:
                model = self._select_frontier_model()
                response = await self._reason_with_frontier(prompt, model)
                source = &#34;frontier&#34;
                confidence = 0.85  # Base confidence for frontier
            else:
                response = await self._reason_with_local(prompt)
                source = &#34;local&#34;
                confidence = 0.75  # Base confidence for local
            
            # Enhance confidence based on response quality
            confidence = self._calculate_clinical_confidence(response, context)
            
            # Store reasoning path for crystallization
            self.last_reasoning_path = {
                &#34;query&#34;: query,
                &#34;prompt&#34;: prompt,
                &#34;response&#34;: response,
                &#34;source&#34;: source,
                &#34;timestamp&#34;: datetime.now().isoformat()
            }
            self.last_confidence = confidence
            
            # Generate auditable trace
            trace = self.create_trace(
                input_data=query,
                explanation=f&#34;Clinical reasoning via {source}&#34;,
                confidence=confidence,
                decision=&#34;clinical_recommendation&#34;
            )
            
            return {
                &#34;response&#34;: response,
                &#34;source&#34;: source,
                &#34;confidence&#34;: confidence,
                &#34;reasoning_path&#34;: self.last_reasoning_path,
                &#34;trace&#34;: trace
            }
            
        except Exception as e:
            logger.error(f&#34;Clinical reasoning failed: {e}&#34;)
            return {
                &#34;response&#34;: f&#34;Error: {str(e)}&#34;,
                &#34;source&#34;: &#34;error&#34;,
                &#34;confidence&#34;: 0.0,
                &#34;error&#34;: str(e)
            }
    
    def _build_clinical_prompt(self, query: str, context: Dict) -&gt; str:
        &#34;&#34;&#34;Build a structured clinical prompt with domain-specific context.&#34;&#34;&#34;
        
        # Extract clinical context
        patient_info = context.get(&#34;patient&#34;, {})
        symptoms = context.get(&#34;symptoms&#34;, [])
        history = context.get(&#34;history&#34;, [])
        vitals = context.get(&#34;vitals&#34;, {})
        
        # Build the prompt
        prompt_parts = []
        
        # System instruction
        prompt_parts.append(&#34;&#34;&#34;You are a clinical reasoning AI assistant. 
Provide evidence-based, cautious, and well-reasoned clinical insights.
Always include:
1. Reasoning steps
2. Evidence cited
3. Confidence level
4. Alternative considerations
5. Clear recommendations

IMPORTANT: This is for clinical decision support, not definitive diagnosis.
Always recommend consultation with a qualified healthcare professional.
&#34;&#34;&#34;)
        
        # Context
        if patient_info:
            prompt_parts.append(f&#34;## Patient Information\n{json.dumps(patient_info, indent=2)}&#34;)
        
        if symptoms:
            prompt_parts.append(f&#34;## Symptoms\n- &#34; + &#34;\n- &#34;.join(symptoms))
        
        if history:
            prompt_parts.append(f&#34;## Medical History\n- &#34; + &#34;\n- &#34;.join(history))
        
        if vitals:
            prompt_parts.append(f&#34;## Vital Signs\n{json.dumps(vitals, indent=2)}&#34;)
        
        # Query
        prompt_parts.append(f&#34;## Clinical Query\n{query}&#34;)
        
        # Instructions for structured reasoning
        prompt_parts.append(&#34;&#34;&#34;
## Response Structure
Please format your response as:
1. **Assessment**: Brief summary of the clinical situation
2. **Analysis**: Step-by-step reasoning with evidence
3. **Recommendations**: Specific, actionable suggestions
4. **Confidence**: Your confidence level (0-100%)
5. **Alternatives**: Other considerations or differentials
6. **Next Steps**: What should be done next
&#34;&#34;&#34;)
        
        return &#34;\n\n&#34;.join(prompt_parts)
    
    def _select_frontier_model(self) -&gt; str:
        &#34;&#34;&#34;Auto-select the best available frontier model.&#34;&#34;&#34;
        # Priority: OpenAI &gt; Anthropic &gt; Gemini &gt; Groq
        if self.openai_key:
            return &#34;openai&#34;
        elif self.anthropic_key:
            return &#34;anthropic&#34;
        elif self.gemini_key:
            return &#34;gemini&#34;
        elif self.groq_key:
            return &#34;groq&#34;
        return None
    
    def _has_frontier_available(self) -&gt; bool:
        &#34;&#34;&#34;Check if any frontier model is available.&#34;&#34;&#34;
        return bool(self.openai_key or self.anthropic_key or self.gemini_key or self.groq_key)
    
    async def _stream_openai(self, prompt: str) -&gt; AsyncGenerator[str, None]:
        &#34;&#34;&#34;Stream from OpenAI API.&#34;&#34;&#34;
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_key)
            
            stream = await client.chat.completions.create(
                model=&#34;gpt-4-turbo-preview&#34;,
                messages=[{&#34;role&#34;: &#34;user&#34;, &#34;content&#34;: prompt}],
                stream=True,
                temperature=0.3
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f&#34;OpenAI streaming failed: {e}&#34;)
            yield f&#34;OpenAI error: {str(e)}&#34;
    
    async def _stream_anthropic(self, prompt: str) -&gt; AsyncGenerator[str, None]:
        &#34;&#34;&#34;Stream from Anthropic Claude API.&#34;&#34;&#34;
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.anthropic_key)
            
            stream = await client.messages.create(
                model=&#34;claude-3-sonnet-20240229&#34;,
                max_tokens=1024,
                messages=[{&#34;role&#34;: &#34;user&#34;, &#34;content&#34;: prompt}],
                stream=True
            )
            
            async for chunk in stream:
                if chunk.type == &#34;content_block_delta&#34;:
                    yield chunk.delta.text
                    
        except Exception as e:
            logger.error(f&#34;Anthropic streaming failed: {e}&#34;)
            yield f&#34;Anthropic error: {str(e)}&#34;
    
    async def _stream_gemini(self, prompt: str) -&gt; AsyncGenerator[str, None]:
        &#34;&#34;&#34;Stream from Google Gemini API.&#34;&#34;&#34;
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            model = genai.GenerativeModel(&#34;gemini-pro&#34;)
            
            response = await model.generate_content_async(
                prompt,
                stream=True
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f&#34;Gemini streaming failed: {e}&#34;)
            yield f&#34;Gemini error: {str(e)}&#34;
    
    async def _stream_groq(self, prompt: str) -&gt; AsyncGenerator[str, None]:
        &#34;&#34;&#34;Stream from Groq API.&#34;&#34;&#34;
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    &#34;POST&#34;,
                    &#34;https://api.groq.com/openai/v1/chat/completions&#34;,
                    headers={
                        &#34;Authorization&#34;: f&#34;Bearer {self.groq_key}&#34;,
                        &#34;Content-Type&#34;: &#34;application/json&#34;
                    },
                    json={
                        &#34;model&#34;: &#34;mixtral-8x7b-32768&#34;,
                        &#34;messages&#34;: [{&#34;role&#34;: &#34;user&#34;, &#34;content&#34;: prompt}],
                        &#34;temperature&#34;: 0.3,
                        &#34;max_tokens&#34;: 1024,
                        &#34;stream&#34;: True
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith(&#34;data: &#34;):
                            data = line[6:]
                            if data == &#34;[DONE]&#34;:
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk.get(&#34;choices&#34;, [{}])[0].get(&#34;delta&#34;, {}).get(&#34;content&#34;, &#34;&#34;)
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f&#34;Groq streaming failed: {e}&#34;)
            yield f&#34;Groq error: {str(e)}&#34;
    
    async def _stream_local(self, prompt: str) -&gt; AsyncGenerator[str, None]:
        &#34;&#34;&#34;Stream from local Ollama model.&#34;&#34;&#34;
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    &#34;POST&#34;,
                    f&#34;{self.ollama_url}/api/generate&#34;,
                    json={
                        &#34;model&#34;: self.local_model,
                        &#34;prompt&#34;: prompt,
                        &#34;stream&#34;: True,
                        &#34;temperature&#34;: 0.3,
                        &#34;options&#34;: {
                            &#34;num_ctx&#34;: 4096,
                            &#34;num_predict&#34;: 1024
                        }
                    }
                ) as response:
                    if response.status_code != 200:
                        yield f&#34;Ollama error: {response.status_code}&#34;
                        return
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if &#34;response&#34; in data:
                                    yield data[&#34;response&#34;]
                                if data.get(&#34;done&#34;, False):
                                    break
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f&#34;Local model streaming failed: {e}&#34;)
            yield f&#34;Local model error: {str(e)}&#34;
    
    async def _reason_with_frontier(self, prompt: str, model: str) -&gt; str:
        &#34;&#34;&#34;Non-streaming reasoning with frontier model.&#34;&#34;&#34;
        # Collect all chunks
        chunks = []
        async for chunk in self._stream_frontier(prompt, model):
            chunks.append(chunk)
        return &#34;&#34;.join(chunks)
    
    async def _stream_frontier(self, prompt: str, model: str) -&gt; AsyncGenerator[str, None]:
        &#34;&#34;&#34;Stream from the selected frontier model.&#34;&#34;&#34;
        if model == &#34;openai&#34;:
            async for chunk in self._stream_openai(prompt):
                yield chunk
        elif model == &#34;anthropic&#34;:
            async for chunk in self._stream_anthropic(prompt):
                yield chunk
        elif model == &#34;gemini&#34;:
            async for chunk in self._stream_gemini(prompt):
                yield chunk
        elif model == &#34;groq&#34;:
            async for chunk in self._stream_groq(prompt):
                yield chunk
        else:
            yield f&#34;Unknown model: {model}&#34;
    
    async def _reason_with_local(self, prompt: str) -&gt; str:
        &#34;&#34;&#34;Non-streaming reasoning with local model.&#34;&#34;&#34;
        chunks = []
        async for chunk in self._stream_local(prompt):
            chunks.append(chunk)
        return &#34;&#34;.join(chunks)
    
    def _calculate_clinical_confidence(self, response: str, context: Dict) -&gt; float:
        &#34;&#34;&#34;Calculate clinical confidence score based on response quality.&#34;&#34;&#34;
        base = 0.7
        
        # Length indicator (more detailed = more confident)
        length_factor = min(len(response) / 500, 1.0)
        base += length_factor * 0.15
        
        # If response includes structured sections, boost confidence
        sections = [&#34;Assessment&#34;, &#34;Analysis&#34;, &#34;Recommendations&#34;, &#34;Confidence&#34;]
        section_count = sum(1 for section in sections if section in response)
        base += (section_count / len(sections)) * 0.1
        
        # Cap at 0.95
        return min(base, 0.95)


# Agent instance wrapper
_ClinicalReasoningAgent_instance = None

def get_ClinicalReasoningAgent():
    global _ClinicalReasoningAgent_instance
    if _ClinicalReasoningAgent_instance is None:
        _ClinicalReasoningAgent_instance = ClinicalReasoningAgent()
    return _ClinicalReasoningAgent_instance


# Agent: ClinicalValidatorAgent
# Model: local
# Source: ClinicalValidatorAgent.py
&#34;&#34;&#34;
Clinical Validator Agent - Validates clinical reasoning against policies.
Always runs locally for HIPAA compliance and air-gapped environments.
&#34;&#34;&#34;

import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.swarm.base import BaseAgent

logger = logging.getLogger(__name__)


class ClinicalValidatorAgent(BaseAgent):
    &#34;&#34;&#34;
    Validates clinical reasoning against policies and guidelines.
    Runs locally to ensure HIPAA compliance and data sovereignty.
    &#34;&#34;&#34;
    
    def __init__(self, client=None):
        super().__init__(&#34;clinical_validator&#34;, client)
        self.policies = {}
        self.compliance_rules = []
        self.hipaa_patterns = self._load_hipaa_patterns()
        logger.info(&#34;ClinicalValidatorAgent initialized&#34;)
    
    async def validate(
        self, 
        response: str, 
        policies: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -&gt; Dict[str, Any]:
        &#34;&#34;&#34;
        Validate clinical response against all applicable policies.
        
        Args:
            response: Clinical reasoning response to validate
            policies: Policy definitions
            context: Clinical context
        
        Returns:
            Validation result with pass/fail, constraints, and audit trail
        &#34;&#34;&#34;
        context = context or {}
        violations = []
        warnings = []
        constraints = []
        
        # 1. HIPAA Compliance Check
        hipaa_result = await self._validate_hipaa(response, context)
        if not hipaa_result[&#34;passed&#34;]:
            violations.extend(hipaa_result.get(&#34;violations&#34;, []))
            constraints.append({&#34;type&#34;: &#34;hipaa&#34;, &#34;constraints&#34;: hipaa_result.get(&#34;constraints&#34;, [])})
        
        # 2. Policy Validation
        for policy_name, policy in policies.items():
            policy_result = await self._validate_policy(response, policy, context)
            if not policy_result[&#34;passed&#34;]:
                violations.append({
                    &#34;policy&#34;: policy_name,
                    &#34;violations&#34;: policy_result.get(&#34;violations&#34;, [])
                })
                if policy_result.get(&#34;constraints&#34;):
                    constraints.append({&#34;type&#34;: policy_name, &#34;constraints&#34;: policy_result[&#34;constraints&#34;]})
        
        # 3. Clinical Protocol Check
        protocol_result = await self._validate_clinical_protocols(response, context)
        if not protocol_result[&#34;passed&#34;]:
            warnings.append(protocol_result.get(&#34;warnings&#34;, []))
        
        # 4. Generate comprehensive result
        return {
            &#34;passed&#34;: len(violations) == 0,
            &#34;violations&#34;: violations,
            &#34;warnings&#34;: warnings,
            &#34;constraints&#34;: constraints,
            &#34;confidence_penalty&#34;: len(violations) * 0.15 + len(warnings) * 0.05,
            &#34;audit_trail&#34;: {
                &#34;validated_at&#34;: datetime.now().isoformat(),
                &#34;policies_checked&#34;: list(policies.keys()),
                &#34;violations_found&#34;: len(violations),
                &#34;warnings_found&#34;: len(warnings)
            }
        }
    
    async def _validate_hipaa(self, response: str, context: Dict) -&gt; Dict:
        &#34;&#34;&#34;Validate HIPAA compliance of the response.&#34;&#34;&#34;
        violations = []
        constraints = []
        
        # Check for PHI (Protected Health Information)
        for pattern_name, pattern in self.hipaa_patterns.items():
            if pattern[&#34;regex&#34;].search(response):
                violations.append({
                    &#34;type&#34;: &#34;phi_detected&#34;,
                    &#34;pattern&#34;: pattern_name,
                    &#34;description&#34;: pattern[&#34;description&#34;],
                    &#34;severity&#34;: &#34;critical&#34;
                })
                constraints.append({
                    &#34;type&#34;: &#34;redact_phi&#34;,
                    &#34;pattern&#34;: pattern_name,
                    &#34;action&#34;: &#34;redact&#34;
                })
        
        # Check for required HIPAA disclaimers
        required_disclaimers = [
            &#34;This is for clinical decision support&#34;,
            &#34;consult with a qualified healthcare professional&#34;,
            &#34;not a definitive diagnosis&#34;
        ]
        
        missing_disclaimers = [
            d for d in required_disclaimers 
            if d.lower() not in response.lower()
        ]
        
        if missing_disclaimers:
            violations.append({
                &#34;type&#34;: &#34;missing_disclaimer&#34;,
                &#34;disclaimers&#34;: missing_disclaimers,
                &#34;severity&#34;: &#34;medium&#34;
            })
        
        return {
            &#34;passed&#34;: len(violations) == 0,
            &#34;violations&#34;: violations,
            &#34;constraints&#34;: constraints
        }
    
    async def _validate_policy(self, response: str, policy: Dict, context: Dict) -&gt; Dict:
        &#34;&#34;&#34;Validate response against a specific policy.&#34;&#34;&#34;
        violations = []
        constraints = []
        
        rules = policy.get(&#34;rules&#34;, [])
        for rule in rules:
            condition = rule.get(&#34;if&#34;, &#34;&#34;)
            action = rule.get(&#34;then&#34;, &#34;&#34;)
            
            # Check if condition is met in response
            if self._check_condition(response, condition):
                # Check if action is properly taken
                if not self._check_action(response, action):
                    violations.append({
                        &#34;rule&#34;: condition,
                        &#34;expected_action&#34;: action,
                        &#34;actual&#34;: &#34;Missing&#34;
                    })
                    constraints.append({
                        &#34;rule&#34;: condition,
                        &#34;expected_action&#34;: action
                    })
        
        return {
            &#34;passed&#34;: len(violations) == 0,
            &#34;violations&#34;: violations,
            &#34;constraints&#34;: constraints
        }
    
    async def _validate_clinical_protocols(self, response: str, context: Dict) -&gt; Dict:
        &#34;&#34;&#34;Validate against clinical protocols and guidelines.&#34;&#34;&#34;
        warnings = []
        
        # Check for evidence-based terms
        evidence_terms = [&#34;evidence&#34;, &#34;study&#34;, &#34;trial&#34;, &#34;guideline&#34;, &#34;recommendation&#34;]
        has_evidence = any(term in response.lower() for term in evidence_terms)
        
        if not has_evidence:
            warnings.append(&#34;Response lacks explicit evidence-based references&#34;)
        
        # Check for confidence statement
        if &#34;confidence&#34; not in response.lower():
            warnings.append(&#34;Response does not include confidence level&#34;)
        
        return {
            &#34;passed&#34;: len(warnings) == 0,
            &#34;warnings&#34;: warnings
        }
    
    def _load_hipaa_patterns(self) -&gt; Dict:
        &#34;&#34;&#34;Load HIPAA PHI detection patterns.&#34;&#34;&#34;
        return {
            &#34;patient_name&#34;: {
                &#34;regex&#34;: re.compile(r&#39;\b[A-Z][a-z]+ [A-Z][a-z]+\b&#39;, re.IGNORECASE),
                &#34;description&#34;: &#34;Patient name detected (two capitalized words)&#34;
            },
            &#34;medical_record&#34;: {
                &#34;regex&#34;: re.compile(r&#39;MRN\s*[A-Z0-9\-]+&#39;, re.IGNORECASE),
                &#34;description&#34;: &#34;Medical Record Number detected&#34;
            },
            &#34;date_of_birth&#34;: {
                &#34;regex&#34;: re.compile(r&#39;(DOB|birth)\s*:?\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}&#39;, re.IGNORECASE),
                &#34;description&#34;: &#34;Date of Birth detected&#34;
            },
            &#34;phone&#34;: {
                &#34;regex&#34;: re.compile(r&#39;\b\d{3}[-.]?\d{3}[-.]?\d{4}\b&#39;),
                &#34;description&#34;: &#34;Phone number detected&#34;
            },
            &#34;email&#34;: {
                &#34;regex&#34;: re.compile(r&#39;\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b&#39;),
                &#34;description&#34;: &#34;Email address detected&#34;
            }
        }
    
    def _check_condition(self, response: str, condition: str) -&gt; bool:
        &#34;&#34;&#34;Check if a condition is met in the response.&#34;&#34;&#34;
        # Simple keyword matching
        keywords = condition.lower().split()
        return any(kw in response.lower() for kw in keywords)
    
    def _check_action(self, response: str, action: str) -&gt; bool:
        &#34;&#34;&#34;Check if an action is properly taken in the response.&#34;&#34;&#34;
        # Simple keyword matching for action
        keywords = action.lower().split()
        return any(kw in response.lower() for kw in keywords)


# Agent instance wrapper
_ClinicalValidatorAgent_instance = None

def get_ClinicalValidatorAgent():
    global _ClinicalValidatorAgent_instance
    if _ClinicalValidatorAgent_instance is None:
        _ClinicalValidatorAgent_instance = ClinicalValidatorAgent()
    return _ClinicalValidatorAgent_instance



# ============================================================
# RUNTIME EXECUTOR
# ============================================================

class ClinicalRuntime:
    """
    Runtime executor for the clinical Domain Intelligence Unit.
    """
    
    def __init__(self):
        self.config = CONFIG
        self.policies = POLICIES
        self.patterns = CRYSTALLIZED_PATTERNS
        self.name = "clinical"
        self.version = "1.0.0"
        self.target = "airgap"
        self.logger = logging.getLogger(f"runtime.clinical")
        
        # Initialize agents
        self.agents = {}
        
        self.agents["ClinicalReasoningAgent"] = get_ClinicalReasoningAgent()
        
        self.agents["ClinicalValidatorAgent"] = get_ClinicalValidatorAgent()
        
    
    async def execute(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the DIU on a query.
        
        Fast Path: Check crystallized patterns first (Ice Layer)
        Reasoning Path: Use agent swarm if no pattern found
        """
        context = context or {}
        
        # Step 1: Check crystallized patterns (FAST PATH)
        matched_pattern = await self._match_crystallized_pattern(query)
        if matched_pattern and matched_pattern.get("confidence", 0) > 0.8:
            self.logger.info(f"✅ Crystallized pattern hit (confidence: {matched_pattern['confidence']})")
            return {
                "response": matched_pattern.get("response"),
                "source": "crystallized",
                "confidence": matched_pattern["confidence"],
                "pattern_id": matched_pattern.get("id"),
                "latency": 0.005  # 5ms
            }
        
        # Step 2: Reasoning Path - Agent Swarm
        self.logger.info("🧠 No crystallized pattern found, entering reasoning path")
        
        # Get reasoning agent
        reasoning_agent = self.agents.get("ClinicalReasoningAgent")
        
        if not reasoning_agent:
            return {
                "response": "No reasoning agent available",
                "source": "error",
                "confidence": 0.0,
                "error": "NO_AGENT_AVAILABLE"
            }
        
        # Step 3: Generate reasoning
        try:
            # Step 4: Validate with validator agent
            # (Validation logic simplified for PoC)
            
            # Simplified execution
            response_text = "Clinical reasoning response (Mock)"
            confidence = 0.9
            
            return {
                "response": response_text,
                "source": "reasoning",
                "confidence": confidence,
            }
            
        except Exception as e:
            self.logger.error(f"Reasoning failed: {e}")
            return {
                "response": f"Error during reasoning: {str(e)}",
                "source": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _match_crystallized_pattern(self, query: str) -> Optional[Dict]:
        """Find the best matching crystallized pattern."""
        return None
    
    def get_statistics(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "target": self.target,
            "patterns_loaded": len(self.patterns),
            "agents_available": list(self.agents.keys()),
            "policies_loaded": list(self.policies.keys())
        }