#!/usr/bin/env python3
"""
Test domain-aware GeneratorAgent integration.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.swarm.core.generator import GeneratorAgent


async def test_domain_generator():
    print("🧪 Testing Domain-Aware Generator")
    print("=" * 50)
    
    generator = GeneratorAgent()
    
    # Show available domains
    stats = generator.domain_router.get_domain_stats()
    print(f"\n📦 Available Domains: {stats['total_domains']}")
    for domain in stats['domains']:
        print(f"   - {domain['name']}: {domain['keyword_count']} keywords, {domain['pattern_count']} patterns")
    
    # Test queries
    test_queries = [
        ("patient presents with chest pain", "clinical"),
        ("analyze this security policy", "security"),
        ("teach me about photosynthesis", "education"),
        ("review this contract", "contracts")
    ]
    
    print("\n🔍 Testing domain detection:")
    print("-" * 50)
    
    for query, expected_domain in test_queries:
        print(f"\n📝 Query: {query[:40]}...")
        print(f"   Expected: {expected_domain}")
        
        # Route to get domain
        domain_result = await generator.domain_router.route(query)
        print(f"   Detected: {domain_result.domain} ({domain_result.confidence:.2%})")
        print(f"   Method: {domain_result.detection_method}")
        if domain_result.matched_keywords:
            print(f"   Keywords: {', '.join(domain_result.matched_keywords[:5])}")
        
        # Generate response (first 150 chars)
        print(f"\n   Generating response...")
        response_parts = []
        async for chunk in generator.generate_stream(query):
            response_parts.append(chunk)
            if len("".join(response_parts)) > 150:
                break
        
        preview = "".join(response_parts)[:150]
        print(f"   Response preview: {preview}...")
        print("-" * 30)
    
    print("\n✅ Test complete!")


async def test_conversation_continuity():
    """Test that conversation stays in domain."""
    print("\n🧪 Testing Conversation Continuity")
    print("=" * 50)
    
    generator = GeneratorAgent()
    
    conversation = [
        "analyze this security policy for access control",
        "what are the risks?",
        "how would you mitigate them?",
        "now tell me about patient data privacy",
        "what regulations apply?"
    ]
    
    print("\n💬 Simulating conversation:")
    print("-" * 50)
    
    for i, query in enumerate(conversation):
        print(f"\n[{i+1}] User: {query[:40]}...")
        domain_result = await generator.domain_router.route(query)
        print(f"   Domain: {domain_result.domain} ({domain_result.confidence:.2%})")
        print(f"   Method: {domain_result.detection_method}")
        
        state = generator.domain_router.get_conversation_state()
        print(f"   State: current={state['current_domain']}, confidence={state['confidence']:.2%}")
        print("-" * 20)


async def main():
    await test_domain_generator()
    await test_conversation_continuity()


if __name__ == "__main__":
    asyncio.run(main())
