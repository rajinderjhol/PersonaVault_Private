"""
Self-Improving Intelligence Service
The core leapfrog differentiator - learns from every decision.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.models import SemanticPattern
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

class SelfImprovingIntelligence:
    """
    The system learns from every decision and interaction.
    This is what makes PersonaVault different from ChatGPT.
    """
    
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.patterns = []
        self._initialized = False
    
    async def initialize(self):
        """Load existing patterns on startup."""
        if self._initialized:
            return
        if not self.db:
            async with SessionLocal() as db:
                self.db = db
                await self._load_patterns()
        else:
            await self._load_patterns()
        self._initialized = True
        logger.info(f"✅ Self-Improving Intelligence initialized with {len(self.patterns)} patterns")
    
    async def _load_patterns(self):
        """Load active patterns from the database."""
        stmt = select(SemanticPattern).where(
            SemanticPattern.is_active == True
        ).order_by(desc(SemanticPattern.weight))
        result = await self.db.execute(stmt)
        self.patterns = result.scalars().all()
    
    async def analyze_interaction(self, user_id: int, query: str, response: str, confidence: float, metadata: Dict = None):
        """
        Analyze every interaction to extract patterns.
        This runs automatically after each chat.
        """
        if not self.db:
            async with SessionLocal() as db:
                self.db = db
                await self._load_patterns()
        
        # 1. Store the interaction for analysis
        interaction = {
            "user_id": user_id,
            "query": query,
            "response": response,
            "confidence": confidence,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 2. Extract patterns
        patterns = await self._extract_patterns(interaction)
        
        # 3. Update policies if needed
        updated_count = 0
        for pattern in patterns:
            if pattern["strength"] > 0.6:
                await self._update_policy(pattern)
                updated_count += 1
        
        if updated_count > 0:
            logger.info(f"✅ Updated {updated_count} policies based on interaction")
            # Reload patterns
            await self._load_patterns()
        
        return patterns
    
    async def _extract_patterns(self, interaction: Dict) -> List[Dict]:
        """Extract patterns from a single interaction."""
        patterns = []
        confidence = interaction.get("confidence", 0.5)
        query = interaction.get("query", "")
        response = interaction.get("response", "")
        
        # Check for success patterns (high confidence)
        if confidence > 0.85:
            patterns.append({
                "type": "success",
                "trigger": query[:100],  # Truncate for storage
                "pattern": response[:200],
                "strength": confidence,
                "weight": 0.05  # +0.05 per success
            })
            logger.info(f"📈 Success pattern detected (confidence: {confidence:.2f})")
        
        # Check for failure patterns (low confidence)
        elif confidence < 0.5:
            patterns.append({
                "type": "failure",
                "trigger": query[:100],
                "pattern": "low_confidence_response",
                "strength": 1.0 - confidence,
                "weight": -0.10  # -0.10 per failure
            })
            logger.info(f"📉 Failure pattern detected (confidence: {confidence:.2f})")
        
        # Check for improvement patterns (medium confidence with good outcome)
        elif 0.5 <= confidence <= 0.85:
            # Look for patterns that could be improved
            patterns.append({
                "type": "improvement",
                "trigger": query[:100],
                "pattern": "medium_confidence_requires_refinement",
                "strength": confidence,
                "weight": 0.02  # Small positive reinforcement
            })
            logger.info(f"🔄 Improvement pattern detected (confidence: {confidence:.2f})")
        
        # Check for repeating patterns (same type of query)
        if "security" in query.lower():
            patterns.append({
                "type": "domain",
                "trigger": "security",
                "pattern": "security_response_template",
                "strength": 0.7,
                "weight": 0.01
            })
        elif "contract" in query.lower():
            patterns.append({
                "type": "domain",
                "trigger": "contract",
                "pattern": "contract_response_template",
                "strength": 0.7,
                "weight": 0.01
            })
        elif "compliance" in query.lower():
            patterns.append({
                "type": "domain",
                "trigger": "compliance",
                "pattern": "compliance_response_template",
                "strength": 0.7,
                "weight": 0.01
            })
        
        return patterns
    
    async def _update_policy(self, pattern: Dict):
        """Update the policy based on discovered patterns."""
        # Check if pattern already exists
        stmt = select(SemanticPattern).where(
            SemanticPattern.trigger == pattern["trigger"]
        )
        result = await self.db.execute(stmt)
        existing = result.scalars().first()
        
        if existing:
            # Update existing pattern
            existing.weight += pattern["weight"]
            existing.success_count += 1 if pattern["type"] == "success" else 0
            existing.occurrence_count += 1
            # Auto-deactivate if below threshold
            if existing.weight < 0.40:
                existing.is_active = False
                logger.info(f"⚠️ Pattern deactivated (weight: {existing.weight:.2f})")
            else:
                logger.info(f"✅ Pattern updated (weight: {existing.weight:.2f})")
        else:
            # Create new pattern
            new_pattern = SemanticPattern(
                pattern_type=pattern["type"],
                trigger=pattern["trigger"],
                correction=pattern["pattern"],
                weight=0.7,
                success_count=1 if pattern["type"] == "success" else 0,
                occurrence_count=1,
                is_active=True
            )
            self.db.add(new_pattern)
            logger.info(f"🆕 New pattern created: {pattern['type']} - {pattern['trigger'][:50]}...")
        
        await self.db.commit()
    
    async def get_active_patterns(self) -> List[Dict]:
        """Get all active patterns for use in decision making."""
        if not self._initialized:
            await self.initialize()
        
        return [
            {
                "id": p.id,
                "type": p.pattern_type,
                "trigger": p.trigger,
                "correction": p.correction,
                "weight": p.weight,
                "confidence": p.success_count / (p.success_count + 1) if p.success_count > 0 else 0.5,
                "occurrences": p.occurrence_count
            }
            for p in self.patterns
            if p.is_active
        ]
    
    async def get_patterns_by_type(self, pattern_type: str) -> List[Dict]:
        """Get patterns filtered by type."""
        all_patterns = await self.get_active_patterns()
        return [p for p in all_patterns if p["type"] == pattern_type]
    
    async def apply_patterns_to_response(self, query: str, response: str) -> str:
        """
        Apply learned patterns to improve a response.
        This is called before sending the response to the user.
        """
        if not self._initialized:
            await self.initialize()
        
        # Find matching patterns
        matched_patterns = []
        for pattern in self.patterns:
            if pattern.trigger and pattern.trigger in query.lower():
                matched_patterns.append(pattern)
            elif any(keyword in query.lower() for keyword in ["security", "contract", "compliance"]):
                if pattern.pattern_type == "domain":
                    matched_patterns.append(pattern)
        
        if not matched_patterns:
            return response
        
        # Sort by weight
        matched_patterns.sort(key=lambda x: x.weight, reverse=True)
        
        # Apply the best pattern
        best_pattern = matched_patterns[0]
        if best_pattern.correction and best_pattern.weight > 0.6:
            # Enhance response with pattern insight
            enhanced = f"{response}\n\n💡 Based on learned patterns ({best_pattern.pattern_type}): {best_pattern.correction[:100]}..."
            logger.info(f"✅ Applied pattern: {best_pattern.pattern_type} (weight: {best_pattern.weight:.2f})")
            return enhanced
        
        return response
    
    async def get_learning_stats(self) -> Dict:
        """Get statistics about the learning system."""
        if not self._initialized:
            await self.initialize()
        
        total_patterns = len(self.patterns)
        active_patterns = sum(1 for p in self.patterns if p.is_active)
        success_patterns = sum(1 for p in self.patterns if p.pattern_type == "success" and p.is_active)
        failure_patterns = sum(1 for p in self.patterns if p.pattern_type == "failure" and p.is_active)
        
        return {
            "total_patterns": total_patterns,
            "active_patterns": active_patterns,
            "success_patterns": success_patterns,
            "failure_patterns": failure_patterns,
            "avg_weight": sum(p.weight for p in self.patterns) / len(self.patterns) if self.patterns else 0,
            "improvement_rate": (success_patterns / (success_patterns + failure_patterns + 1)) * 100
        }
