
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
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = self.client.post(f"/api/v1/thermodynamics/snowflakes/{valid_uuid}/branch/security")
        # This might fail with 404 (not found), which is fine, but it should not be 400.
        self.assertNotEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
