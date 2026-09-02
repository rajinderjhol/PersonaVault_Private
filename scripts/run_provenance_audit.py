#!/usr/bin/env python
"""
Reasoning Provenance Audit Script
Run this script to audit the provenance of reasoning chains.
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.api.v2.services.audit.provenance_audit import ProvenanceAudit
from app.repositories.reasoning_repository import ReasoningChainRepository
from app.db.session import SessionLocal as get_session_factory

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"{BLUE}{text}{RESET}")
    print("=" * 70)

def print_success(text: str):
    """Print a success message."""
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text: str):
    """Print an error message."""
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text: str):
    """Print a warning message."""
    print(f"{YELLOW}⚠️ {text}{RESET}")

def print_info(text: str):
    """Print an info message."""
    print(f"{BLUE}ℹ️ {text}{RESET}")

async def run_audit(args):
    """Run the provenance audit and print results."""
    print_header("🔍 Reasoning Provenance Audit")
    
    # Initialize
    session_factory = get_session_factory()
    repository = ReasoningChainRepository(session_factory)
    audit_service = ProvenanceAudit(repository)
    
    # Get chains to audit
    if args.chain_id:
        print_info(f"Auditing specific chain: {args.chain_id}")
        chains = [await repository.get_chain(args.chain_id)]
        if not chains[0]:
            print_error(f"Chain {args.chain_id} not found")
            return
    else:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=args.days)
        print_info(f"Auditing chains from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        chains = await repository.get_chains_by_date_range(start_date, end_date, args.limit)
    
    if not chains or None in chains:
        print_warning("No reasoning chains found to audit")
        return
    
    print_info(f"Found {len(chains)} reasoning chains to audit")
    print("=" * 70)
    
    # Audit each chain
    results = []
    for i, chain in enumerate(chains, 1):
        print(f"\n[{i}/{len(chains)}] Auditing chain: {chain['id']}")
        result = await audit_service.audit_reasoning_chain(chain["id"])
        results.append(result)
        
        # Show progress
        if result["status"] == "passed":
            print_success(f"Chain {chain['id']} passed")
        else:
            print_error(f"Chain {chain['id']} failed with {len(result['issues'])} issues")
            for issue in result["issues"]:
                print_warning(f"  - {issue}")
    
    # Generate summary
    print_header("📊 Audit Summary")
    
    total_chains = len(results)
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = total_chains - passed
    total_issues = sum(len(r["issues"]) for r in results)
    
    print(f"Total Chains Audited:  {total_chains}")
    print(f"{GREEN}Passed:             {passed}{RESET}")
    print(f"{RED}Failed:             {failed}{RESET}")
    print(f"📈 Pass Rate:          {passed/total_chains*100:.1f}%" if total_chains > 0 else "📈 Pass Rate:          N/A")
    print(f"📋 Total Issues Found: {total_issues}")
    
    # Show detailed results for failed chains
    if failed > 0:
        print_header("🔍 Detailed Issue Report")
        for result in results:
            if result["issues"]:
                print(f"\n{YELLOW}Chain ID: {result['chain_id']}{RESET}")
                print(f"  Status: {RED}{result['status']}{RESET}")
                print(f"  Issues:")
                for issue in result["issues"]:
                    print(f"    - {issue}")
    
    # Show summary per issue type
    issue_counts = {}
    for result in results:
        for issue in result["issues"]:
            issue_type = issue.split(":")[0] if ":" in issue else issue
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
    
    if issue_counts:
        print_header("📊 Issue Type Breakdown")
        for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {issue_type}: {count} occurrences")
    
    print_header("🏁 Audit Complete")
    
    # Return summary for potential programmatic use
    return {
        "total_chains": total_chains,
        "passed": passed,
        "failed": failed,
        "total_issues": total_issues,
        "pass_rate": passed/total_chains*100 if total_chains > 0 else 0,
        "issue_counts": issue_counts
    }

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Run the reasoning provenance audit")
    parser.add_argument("--days", type=int, default=30, help="Number of days to audit (default: 30)")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of chains to audit (default: 50)")
    parser.add_argument("--chain-id", type=str, help="Audit a specific chain by ID")
    parser.add_argument("--output", type=str, help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    # Run the audit
    try:
        result = asyncio.run(run_audit(args))
        
        # Output to file if requested
        if args.output and result:
            import json
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n📄 Results saved to {args.output}")
    except Exception as e:
        print_error(f"Audit script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
