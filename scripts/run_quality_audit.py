#!/usr/bin/env python
"""
Crystallization Quality Audit Script
Run this script to audit the quality of crystallized knowledge patterns.
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.api.v2.services.audit.quality_audit import QualityAudit
from app.repositories.sqlalchemy.semantic_pattern import SQLSemanticPatternRepository
from app.services.crystallization_service import CrystallizationService
from app.db.session import SessionLocal

async def run_audit(args):
    """Run the crystallization quality audit."""
    print("🔍 Starting Crystallization Quality Audit...")
    
    # Initialize
    # Creating a dependency chain for the service
    # In a real environment, this might be handled by an IoC container
    async with SessionLocal() as session:
        pattern_repo = SQLSemanticPatternRepository(session)
        crystallization_service = CrystallizationService(SessionLocal) 
        
        audit_service = QualityAudit(pattern_repo, crystallization_service)
        
        results = await audit_service.audit_crystallization_quality(
            days=args.days, 
            sample_size=args.limit
        )
    
    print("\n📊 CRYSTALLIZATION QUALITY AUDIT RESULTS")
    print("=" * 60)
    for key, value in results.items():
        print(f"{key}: {value}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Run the crystallization quality audit")
    parser.add_argument("--days", type=int, default=30, help="Number of days to audit (default: 30)")
    parser.add_argument("--limit", type=int, default=100, help="Sample size for audit (default: 100)")
    
    args = parser.parse_args()
    asyncio.run(run_audit(args))

if __name__ == "__main__":
    main()
