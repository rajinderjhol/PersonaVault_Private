
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.v1.endpoints.thermodynamics import router

class TestThermodynamicsAPI(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)

    def test_thermodynamics_endpoints(self):
        """Test thermodynamics API endpoints in isolation."""
        # Test Phase Distribution
        response = self.client.get("/api/v1/thermodynamics/phase-distribution")
        self.assertEqual(response.status_code, 200)
        self.assertIn("gas", response.json())

        # Test Transitions
        response = self.client.get("/api/v1/thermodynamics/transitions")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

        # Test Snowflakes
        response = self.client.get("/api/v1/thermodynamics/snowflakes")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

        # Test Branching
        response = self.client.post("/api/v1/thermodynamics/snowflakes/p_base_001/branch/security")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

if __name__ == '__main__':
    unittest.main()
