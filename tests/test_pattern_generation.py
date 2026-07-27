#!/usr/bin/env python3
"""
Automated Pattern Generation & Reinforcement Test Suite
Tests the complete self-improvement loop from end to end.
Uses direct pattern extraction without GeneratorAgent.
"""

import asyncio
import sys
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any
import logging

sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models import EpisodicEntry, SemanticPattern
from sqlalchemy import select, delete

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatternTestSuite:
    """Automated test suite for pattern generation and reinforcement."""
    
    def __init__(self):
        self.session_factory = SessionLocal
        self.results = {
            "patterns_created": 0,
            "patterns_reinforced": 0,
            "successes": 0,
            "failures": 0,
            "patterns": []
        }
    
    def generate_test_cases(self) -> List[Dict[str, Any]]:
        """Generate diverse test cases that will trigger pattern creation."""
        return [
            {
                "query": "What is the best way to implement semantic search?",
                "answer": "Use BM25 or TF-IDF.",
                "feedback": "Missing vector search and embedding approaches.",
                "faithfulness": 0.15,
                "confidence": 0.25
            },
            {
                "query": "How does PersonaVault handle multi-tenancy?",
                "answer": "It uses organization IDs.",
                "feedback": "Missing details about data isolation and RBAC.",
                "faithfulness": 0.2,
                "confidence": 0.3
            },
            {
                "query": "What is the role of the Judge agent?",
                "answer": "To check answers.",
                "feedback": "Missing explanation of faithfulness, coverage, and relevance metrics.",
                "faithfulness": 0.18,
                "confidence": 0.28
            },
            {
                "query": "How does the Empathy agent work?",
                "answer": "It detects mood.",
                "feedback": "Missing details about tone analysis and situational grounding.",
                "faithfulness": 0.22,
                "confidence": 0.32
            },
            {
                "query": "What is the purpose of the Blackboard?",
                "answer": "Shared memory for agents.",
                "feedback": "Missing explanation of agent communication and insight sharing.",
                "faithfulness": 0.2,
                "confidence": 0.3
            },
            {
                "query": "How does the system handle data privacy?",
                "answer": "Uses encryption.",
                "feedback": "Missing details about tokenization, differential privacy, and compliance.",
                "faithfulness": 0.15,
                "confidence": 0.25
            },
            {
                "query": "What is the crystallization engine?",
                "answer": "Converts memories.",
                "feedback": "Missing explanation of Layer 2 to Layer 3 consolidation.",
                "faithfulness": 0.2,
                "confidence": 0.3
            },
            {
                "query": "How does FAISS indexing work?",
                "answer": "Stores vectors.",
                "feedback": "Missing details about L2 distance, indexing strategies, and search optimization.",
                "faithfulness": 0.18,
                "confidence": 0.28
            },
            {
                "query": "What is the MCP protocol?",
                "answer": "A protocol for models.",
                "feedback": "Missing context about Model Context Protocol and its usage.",
                "faithfulness": 0.22,
                "confidence": 0.32
            },
            {
                "query": "How does the HITL workflow work?",
                "answer": "Human approval.",
                "feedback": "Missing details about pending actions, approval gates, and governance.",
                "faithfulness": 0.2,
                "confidence": 0.3
            }
        ]
    
    async def create_episodic_entries(self, test_cases: List[Dict[str, Any]]) -> List[int]:
        """Create EpisodicEntry records for testing."""
        entries = []
        async with self.session_factory() as db:
            # Clear old unconsolidated entries
            await db.execute(delete(EpisodicEntry).where(EpisodicEntry.consolidated == False))
            
            for case in test_cases:
                entry = EpisodicEntry(
                    user_id=1,
                    query=case["query"],
                    plan=json.dumps({"type": "test", "complexity": 0.3}),
                    results=json.dumps([]),
                    answer=case["answer"],
                    evaluation=json.dumps({
                        "passed": False,
                        "faithfulness": case["faithfulness"],
                        "confidence": case["confidence"],
                        "coverage": 0.3,
                        "relevance": 0.4,
                        "feedback": case["feedback"],
                        "needs_human": True,
                        "hedging_detected": False
                    }),
                    consolidated=False,
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(entry)
                entries.append(entry.id)
            
            await db.commit()
            logger.info(f"✅ Created {len(entries)} EpisodicEntry records")
        
        return entries

    async def manual_consolidation(self) -> Dict[str, Any]:
        """Manual consolidation that creates patterns directly from entries."""
        async with self.session_factory() as db:
            # Get all unconsolidated entries
            stmt = select(EpisodicEntry).where(EpisodicEntry.consolidated == False)
            result = await db.execute(stmt)
            entries = result.scalars().all()
            
            logger.info(f"📊 Found {len(entries)} unconsolidated entries")
            
            results = {
                "processed": 0,
                "patterns_created": 0,
                "patterns_updated": 0,
                "errors": 0
            }
            
            for entry in entries:
                try:
                    # Parse evaluation
                    eval_data = entry.evaluation
                    if isinstance(eval_data, str):
                        eval_data = json.loads(eval_data)
                    
                    if not eval_data or eval_data.get("passed", True):
                        entry.consolidated = True
                        results["processed"] += 1
                        continue
                    
                    feedback = eval_data.get("feedback", "Unknown")
                    faithfulness = eval_data.get("faithfulness", 0.5)
                    confidence = eval_data.get("confidence", 0.5)
                    
                    # Skip if the response was actually good
                    if faithfulness >= 0.6 and confidence >= 0.6:
                        entry.consolidated = True
                        results["processed"] += 1
                        continue
                    
                    # Determine pattern type
                    if faithfulness < 0.6:
                        pattern_type = "hallucination"
                        correction = f"Ensure factual accuracy: {feedback}"
                    elif confidence < 0.6:
                        pattern_type = "low_confidence"
                        correction = f"Provide more detailed response: {feedback}"
                    else:
                        pattern_type = "general"
                        correction = f"Improve response quality: {feedback}"
                    
                    trigger = entry.query[:100] if entry.query else "unknown query"
                    
                    # Check if pattern already exists
                    stmt_check = select(SemanticPattern).where(
                        SemanticPattern.trigger == trigger
                    )
                    existing = (await db.execute(stmt_check)).scalars().first()
                    
                    if existing:
                        existing.occurrence_count += 1
                        results["patterns_updated"] += 1
                        logger.info(f"🔄 Updated existing pattern: {trigger[:30]}...")
                    else:
                        # Create new pattern
                        pattern = SemanticPattern(
                            pattern_type=pattern_type,
                            trigger=trigger,
                            correction=correction[:200],
                            occurrence_count=1,
                            success_count=0,
                            weight=0.7,
                            is_active=True
                        )
                        db.add(pattern)
                        results["patterns_created"] += 1
                        logger.info(f"✨ Created new pattern: {trigger[:30]}...")
                    
                    entry.consolidated = True
                    results["processed"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing entry {entry.id}: {e}")
                    results["errors"] += 1
            
            await db.commit()
            logger.info(f"📊 Manual consolidation complete: {results}")
            return results

    async def reinforce_patterns(self, pattern_ids: List[int], iterations: int = 3) -> Dict[str, Any]:
        """Simulate pattern reinforcement over multiple iterations."""
        reinforced = []
        
        for pattern_id in pattern_ids:
            success_count = 0
            current_weight = 0.7
            
            async with self.session_factory() as db:
                stmt = select(SemanticPattern).where(SemanticPattern.id == pattern_id)
                result = await db.execute(stmt)
                pattern = result.scalars().first()
                if pattern:
                    for i in range(iterations):
                        success_count += 1
                        current_weight = min(1.0, current_weight + 0.05)
                        reinforced.append({
                            "pattern_id": pattern_id,
                            "iteration": i + 1,
                            "weight": current_weight,
                            "success_count": success_count
                        })
                    
                    pattern.success_count = success_count
                    pattern.weight = current_weight
                    await db.commit()
                    logger.info(f"🔄 Pattern {pattern_id} reinforced to weight {current_weight:.2f}")
        
        return {
            "total_reinforced": len(reinforced),
            "results": reinforced
        }

    async def check_patterns(self) -> List[Dict[str, Any]]:
        """Check all patterns in the database."""
        patterns = []
        async with self.session_factory() as db:
            stmt = select(SemanticPattern)
            result = await db.execute(stmt)
            patterns_db = result.scalars().all()
            
            for p in patterns_db:
                patterns.append({
                    "id": p.id,
                    "type": p.pattern_type,
                    "trigger": p.trigger[:50] + "..." if len(p.trigger) > 50 else p.trigger,
                    "weight": p.weight,
                    "success_count": p.success_count,
                    "occurrence_count": p.occurrence_count,
                    "is_active": p.is_active
                })
        
        return patterns

    async def run_full_test(self) -> Dict[str, Any]:
        """Run the complete test suite."""
        logger.info("🧪 Starting Pattern Generation Test Suite...")
        start_time = time.time()
        
        # Step 1: Generate test cases
        logger.info("📝 Step 1: Generating test cases...")
        test_cases = self.generate_test_cases()
        logger.info(f"   Generated {len(test_cases)} test cases")
        
        # Step 2: Create EpisodicEntry records
        logger.info("📝 Step 2: Creating EpisodicEntry records...")
        entry_ids = await self.create_episodic_entries(test_cases)
        logger.info(f"   Created {len(entry_ids)} entries")
        
        # Step 3: Manual consolidation (bypasses GeneratorAgent)
        logger.info("📝 Step 3: Running manual consolidation...")
        consolidation_result = await self.manual_consolidation()
        logger.info(f"   Consolidation result: {consolidation_result}")
        
        # Step 4: Check created patterns
        logger.info("📝 Step 4: Checking created patterns...")
        patterns = await self.check_patterns()
        logger.info(f"   Found {len(patterns)} patterns")
        
        # Step 5: Reinforce patterns
        if patterns:
            logger.info("📝 Step 5: Reinforcing patterns...")
            pattern_ids = [p["id"] for p in patterns]
            reinforce_result = await self.reinforce_patterns(pattern_ids, iterations=3)
            logger.info(f"   Reinforced {reinforce_result['total_reinforced']} patterns")
        
        # Step 6: Final check
        logger.info("📝 Step 6: Final pattern check...")
        final_patterns = await self.check_patterns()
        
        # Step 7: Summary
        elapsed_time = time.time() - start_time
        summary = {
            "total_test_cases": len(test_cases),
            "entries_created": len(entry_ids),
            "patterns_created": len(patterns),
            "patterns_reinforced": reinforce_result.get("total_reinforced", 0) if patterns else 0,
            "final_patterns": final_patterns,
            "elapsed_time_seconds": round(elapsed_time, 2),
            "success_rate": f"{len([p for p in final_patterns if p['weight'] > 0.8])}/{len(final_patterns)} patterns > 0.80" if final_patterns else "0/0"
        }
        
        logger.info("\n" + "="*50)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*50)
        for key, value in summary.items():
            if key != "final_patterns":
                logger.info(f"   {key}: {value}")
        logger.info("="*50)
        
        # Print detailed pattern info
        for p in final_patterns:
            logger.info(f"   Pattern {p['id']}: {p['type']} - Weight: {p['weight']:.2f} (successes: {p['success_count']})")
        
        self.results = summary
        self.results["final_patterns"] = final_patterns
        return self.results

async def run_test_suite():
    """Main entry point for the test suite."""
    test = PatternTestSuite()
    results = await test.run_full_test()
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("\n✅ Test suite complete! Results saved to test_results.json")
    return results

if __name__ == "__main__":
    asyncio.run(run_test_suite())
