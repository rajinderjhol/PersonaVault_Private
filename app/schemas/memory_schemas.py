from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DeploymentType(str, Enum):
    LOCAL = "local"
    INTERNET = "internet"
    HYBRID = "hybrid"

class ProviderType(str, Enum):
    OLLAMA = "Ollama"
    INTERNET = "Internet"
    HYBRID = "Hybrid"

class AISettingsBase(BaseModel):
    profile_name: str
    provider_type: ProviderType
    deployment_type: DeploymentType
    model_name: str
    model_description: Optional[str] = ""
    api_endpoint: Optional[str] = ""
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 100
    top_p: Optional[float] = 0.9
    system_prompt: Optional[str] = ""
    is_active: Optional[bool] = True

class AISettingsCreate(AISettingsBase):
    api_key: Optional[str] = None

class AISettingsResponse(AISettingsBase):
    id: Optional[int]

class ChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    stream: Optional[bool] = True

class MemorySearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10

class RetrievalPlan(BaseModel):
    needs_retrieval: bool
    semantic_queries: List[str] = Field(default_factory=list)
    keyword_queries: List[str] = Field(default_factory=list)
    graph_traversals: List[str] = Field(default_factory=list)
    reasoning: str
    complexity_score: float = 0.5

class MemoryResult(BaseModel):
    content: str
    source: str  # 'faiss', 'bm25', or 'neo4j'
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GenerationResult(BaseModel):
    answer: str
    confidence: float
    reasoning_steps: List[str]

class EvaluationMetrics(BaseModel):
    coverage: float = Field(ge=0, le=1)
    relevance: float = Field(ge=0, le=1)
    faithfulness: float = Field(ge=0, le=1)
    confidence: float = Field(default=1.0, ge=0, le=1)
    passed: bool
    needs_human: bool = False
    hedging_detected: bool = False
    feedback: Optional[str] = None

class EpisodicEntry(BaseModel):
    query: str
    plan: RetrievalPlan
    results: List[MemoryResult]
    answer: str
    evaluation: Optional[EvaluationMetrics] = None
    governance_receipt_id: Optional[str] = None
    signature: Optional[str] = None
    hitl_approved: bool = False
    user_feedback: Optional[int] = None  # -1, 0, 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SemanticPattern(BaseModel):
    pattern_type: str  # 'hallucination_prevention', 'query_refinement'
    trigger: str       # keyword or query pattern
    correction: str    # the learned fix
    occurrence_count: int = 1