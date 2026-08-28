import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from datetime import datetime
from app.swarm.routing.domain_detector import DomainDetector, DomainResult

logger = logging.getLogger(__name__)

@dataclass
class ConversationState:
    current_domain: Optional[str] = None
    confidence: float = 0.0
    history: List[Dict] = field(default_factory=list)
    last_query_time: Optional[datetime] = None

class DomainRouter:
    def __init__(self, packs_dir=None):
        self.detector = DomainDetector(packs_dir)
        self.conversation = ConversationState()
        self.confidence_threshold = 0.3
        
    async def route(self, query: str, context: Optional[Dict] = None, force_domain: Optional[str] = None) -> DomainResult:
        if force_domain and force_domain in self.detector.pack_keywords:
            return await self.detector.detect(query, context, force_domain=force_domain)
        
        if self.conversation.current_domain and await self._should_continue(query):
            result = await self.detector.detect(query, context, force_domain=self.conversation.current_domain)
            result.confidence = min(result.confidence + 0.1, 0.95)
            self._update_conversation(result)
            return result
        
        result = await self.detector.detect(query, context)
        if result.confidence > self.confidence_threshold:
            self._update_conversation(result)
        
        return result
    
    async def _should_continue(self, query: str) -> bool:
        if not self.conversation.current_domain: return False
        if self.conversation.last_query_time and (datetime.now() - self.conversation.last_query_time).seconds > 600: return False
        return len(query.split()) <= 3 or any(w in query.lower() for w in ["but", "and", "also", "what about"])
    
    def _update_conversation(self, result: DomainResult):
        if result.domain != "general":
            self.conversation.current_domain = result.domain
            self.conversation.confidence = result.confidence
        self.conversation.last_query_time = datetime.now()
        
    def reset_conversation(self):
        self.conversation = ConversationState()

    def get_domain_stats(self) -> Dict[str, Any]:
        return self.detector.get_domain_stats()

    def get_conversation_state(self) -> Dict[str, Any]:
        return {
            "current_domain": self.conversation.current_domain,
            "confidence": self.conversation.confidence,
            "last_query_time": self.conversation.last_query_time.isoformat() if self.conversation.last_query_time else None
        }
