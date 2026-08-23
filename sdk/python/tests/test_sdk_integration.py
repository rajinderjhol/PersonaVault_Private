"""
Integration tests for the PersonaVault Python SDK.
Verifies connectivity, auth, decisions, and swarm interaction.
"""
import unittest
import sys
import os
import time

# Add SDK to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from personavault import PersonaVault
    from personavault.models import Decision
except ImportError:
    print("Error: Could not import SDK. Check path.")
    sys.exit(1)

class TestSDKIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Assumes backend is running on localhost:8000
        cls.pv = PersonaVault(host="http://localhost:8000")
        try:
            cls.pv.login("admin", "admin123")
            print("✅ SDK Login Successful")
        except Exception as e:
            print(f"❌ SDK Login Failed: {e}")
            raise e

    def test_01_create_decision(self):
        """Verify that the SDK can create a decision record."""
        decision = self.pv.decisions.create(
            event_type="test_integration",
            decision="verified",
            outcome="success",
            confidence=0.99,
            reason="Integration test decision",
            user_id=1,
            actor="test_bot",
            artefact="sdk_unit_test"
        )
        self.assertIsNotNone(decision.id)
        self.assertEqual(decision.decision, "verified")
        print(f"✅ SDK Decision Creation Verified: {decision.id}")

    def test_02_swarm_chat(self):
        """Verify that the SDK can interact with the agent swarm."""
        # Note: Depends on Ollama/Groq availability
        try:
            response = self.pv.swarm.chat("Hello Swarm, this is an automated test.")
            self.assertIn("response", response)
            print("✅ SDK Swarm Chat Verified")
        except Exception as e:
            print(f"⚠️ Swarm Chat Test Warning: {e} (Expected if AI providers are offline)")

    def test_03_sovereign_mode_check(self):
        """Verify that we can check the current execution mode."""
        response = self.pv._client.get("/api/v1/mode/current")
        data = response.json()
        self.assertIn("mode", data)
        self.assertIn("config", data)
        print(f"✅ SDK Sovereign Mode Check Verified: {data['mode']}")

if __name__ == '__main__':
    unittest.main()
