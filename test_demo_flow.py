#!/usr/bin/env python3
"""
PersonaVault Demo Flow Diagnostic Test
Tests ALL features needed for the 2-minute demo
"""

import asyncio
import json
import sys
import os
import httpx
import sqlite3
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

# ============================================================
# HELPERS
# ============================================================

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_result(test_name, passed, details=""):
    icon = "✅" if passed else "❌"
    status = "PASS" if passed else "FAIL"
    print(f"{icon} {test_name:40} [{status}]")
    if details and not passed:
        print(f"   → {details}")

# ============================================================
# TESTS
# ============================================================

class DemoFlowTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.cookies = None
        self.user_id = None
        self.results = []
    
    def record(self, name, passed, details=""):
        self.results.append({"name": name, "passed": passed, "details": details})
        print_result(name, passed, details)
    
    async def test_1_login(self):
        """Step 2: Login"""
        print_header("STEP 2: Login")
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"username": USERNAME, "password": PASSWORD}
            )
            if response.status_code == 200:
                data = response.json()
                self.cookies = response.cookies
                self.user_id = data.get("user", {}).get("id")
                self.record("Login", True, f"User ID: {self.user_id}")
                return True
            else:
                self.record("Login", False, f"HTTP {response.status_code}: {response.text[:100]}")
                return False
        except Exception as e:
            self.record("Login", False, str(e))
            return False
    
    async def test_2_chat_tab(self):
        """Step 3: Chat tab loads"""
        print_header("STEP 3: Chat Tab")
        try:
            response = await self.client.get(
                f"{BASE_URL}/api/v1/admin/dashboard/tab/chat",
                cookies=self.cookies
            )
            if response.status_code == 200:
                html = response.text
                # Check if chat HTML loaded
                if "chat-input" in html or "chat-messages" in html:
                    self.record("Chat Tab Loads", True, "HTML loaded with chat elements")
                    return True
                else:
                    self.record("Chat Tab Loads", False, "HTML loaded but missing chat elements")
                    return False
            else:
                self.record("Chat Tab Loads", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.record("Chat Tab Loads", False, str(e))
            return False
    
    async def test_3_chat_response(self):
        """Step 4: Chat responds to query"""
        print_header("STEP 4: Chat Response")
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/v1/chat",
                cookies=self.cookies,
                json={"query": "What do you know about project X?"}
            )
            if response.status_code == 200:
                data = response.json()
                if "response" in data and data["response"]:
                    self.record("Chat Responds", True, f"Response: {data['response'][:50]}...")
                    # Check if provider is shown
                    if "provider" in data:
                        print(f"   → Provider: {data['provider']}")
                    if "confidence" in data:
                        print(f"   → Confidence: {data['confidence']}")
                    return True
                else:
                    self.record("Chat Responds", False, "No response in data")
                    return False
            else:
                self.record("Chat Responds", False, f"HTTP {response.status_code}: {response.text[:100]}")
                return False
        except Exception as e:
            self.record("Chat Responds", False, str(e))
            return False
    
    async def test_4_agents_tab(self):
        """Step 6: Agents tab loads"""
        print_header("STEP 6: Agents Tab")
        try:
            response = await self.client.get(
                f"{BASE_URL}/api/v1/admin/dashboard/tab/agents",
                cookies=self.cookies
            )
            if response.status_code == 200:
                html = response.text
                if "agent-load-stats" in html or "thought-log" in html:
                    self.record("Agents Tab Loads", True, "HTML loaded with agent elements")
                    return True
                else:
                    self.record("Agents Tab Loads", False, "Missing agent elements")
                    return False
            else:
                self.record("Agents Tab Loads", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.record("Agents Tab Loads", False, str(e))
            return False
    
    async def test_5_agent_status(self):
        """Step 7: Agent status API works"""
        print_header("STEP 7: Agent Status / Swarm")
        try:
            # Test cognitive load
            response = await self.client.get(
                f"{BASE_URL}/api/v1/admin/dashboard/cognitive-load",
                cookies=self.cookies
            )
            if response.status_code == 200:
                data = response.json()
                if "active_tasks" in data:
                    self.record("Agent Status API", True, f"Active tasks: {data.get('active_tasks', 0)}")
                    return True
                else:
                    self.record("Agent Status API", False, "Missing active_tasks")
                    return False
            else:
                self.record("Agent Status API", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.record("Agent Status API", False, str(e))
            return False
    
    async def test_6_domain_packs(self):
        """Step 9: Domain Intelligence packs"""
        print_header("STEP 9: Domain Intelligence")
        try:
            # Test packs endpoint
            response = await self.client.get(
                f"{BASE_URL}/api/v1/packs/",
                cookies=self.cookies
            )
            if response.status_code == 200:
                data = response.json()
                # Handle both formats
                packs = data if isinstance(data, list) else data.get("packs", [])
                if len(packs) > 0:
                    self.record("Domain Packs Load", True, f"Found {len(packs)} packs")
                    for p in packs[:3]:
                        print(f"   → {p.get('name', 'Unknown')} ({p.get('domain', 'unknown')})")
                    return True
                else:
                    self.record("Domain Packs Load", False, "No packs found (empty array)")
                    return False
            else:
                self.record("Domain Packs Load", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.record("Domain Packs Load", False, str(e))
            return False
    
    async def test_7_timeline_tab(self):
        """Step 11: Decision Timeline tab"""
        print_header("STEP 11: Decision Timeline")
        try:
            response = await self.client.get(
                f"{BASE_URL}/api/v1/admin/dashboard/tab/timeline",
                cookies=self.cookies
            )
            if response.status_code == 200:
                html = response.text
                if "timeline-list" in html or "timeline-event-id" in html:
                    self.record("Timeline Tab Loads", True, "HTML loaded")
                    return True
                else:
                    self.record("Timeline Tab Loads", False, "Missing timeline elements")
                    return False
            else:
                self.record("Timeline Tab Loads", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.record("Timeline Tab Loads", False, str(e))
            return False
    
    async def test_8_decision_timeline(self):
        """Step 12: Decision timeline data"""
        print_header("STEP 12: Decision Timeline Data")
        try:
            # Try to get events
            response = await self.client.get(
                f"{BASE_URL}/api/v1/behaviour/events?limit=5",
                cookies=self.cookies
            )
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    self.record("Decision Timeline Data", True, f"Found {len(data)} events")
                    for e in data[:2]:
                        print(f"   → Event {e.get('id')}: {e.get('event_type')} → {e.get('decision')}")
                    return True
                else:
                    self.record("Decision Timeline Data", False, "No events found")
                    return False
            else:
                self.record("Decision Timeline Data", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.record("Decision Timeline Data", False, str(e))
            return False
    
    async def test_9_mcp_registry(self):
        """Step: MCP Registry (bonus test)"""
        print_header("MCP Registry (Bonus)")
        try:
            response = await self.client.get(
                f"{BASE_URL}/api/v1/mcp/tools",
                cookies=self.cookies
            )
            if response.status_code == 200:
                data = response.json()
                tools = data.get("tools", [])
                if len(tools) > 0:
                    self.record("MCP Registry", True, f"Found {len(tools)} tools")
                    for t in tools[:3]:
                        print(f"   → {t.get('name')}")
                    return True
                else:
                    self.record("MCP Registry", False, "No tools found")
                    return False
            else:
                self.record("MCP Registry", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.record("MCP Registry", False, str(e))
            return False
    
    async def test_10_intelligence_status(self):
        """Step: Intelligence Gateway status"""
        print_header("Intelligence Status (Bonus)")
        try:
            response = await self.client.get(
                f"{BASE_URL}/api/v1/intelligence/status",
                cookies=self.cookies
            )
            if response.status_code == 200:
                data = response.json()
                self.record("Intelligence Gateway", True, 
                    f"Mode: {data.get('mode')}, Providers: {data.get('providers', [])}")
                return True
            else:
                self.record("Intelligence Gateway", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.record("Intelligence Gateway", False, str(e))
            return False
    
    async def run_all(self):
        """Run all tests in sequence"""
        print_header("PERSONAVAULT DEMO FLOW DIAGNOSTIC")
        print("Testing the complete demo flow...")
        
        # Login first
        if not await self.test_1_login():
            print("\n❌ Login failed. Cannot continue.")
            return self.results
        
        # Run tests
        await self.test_2_chat_tab()
        await self.test_3_chat_response()
        await self.test_4_agents_tab()
        await self.test_5_agent_status()
        await self.test_6_domain_packs()
        await self.test_7_timeline_tab()
        await self.test_8_decision_timeline()
        await self.test_9_mcp_registry()
        await self.test_10_intelligence_status()
        
        # Summary
        print_header("SUMMARY")
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        print(f"\n  Total Tests: {total}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  Success Rate: {round(passed/total*100, 1)}%")
        
        # Show failures
        if failed > 0:
            print("\n  ⚠️  FAILED TESTS:")
            for r in self.results:
                if not r["passed"]:
                    print(f"     • {r['name']}: {r['details']}")
        
        # Recommendations
        print("\n  📋 RECOMMENDATIONS:")
        if self.results and self.results[0]["passed"]:
            print("     ✅ Login: Working")
        if failed == 0:
            print("     🎉 ALL TESTS PASSED! Your system is ready for the demo!")
        else:
            print("     ⚠️  Some tests failed. Fix the issues above and re-run.")
        
        return self.results
    
    async def close(self):
        await self.client.aclose()

# ============================================================
# MAIN
# ============================================================

async def main():
    tester = DemoFlowTester()
    try:
        results = await tester.run_all()
        return results
    finally:
        await tester.close()

if __name__ == "__main__":
    results = asyncio.run(main())
    
    # Exit with appropriate code
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)
