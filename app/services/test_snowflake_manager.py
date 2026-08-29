
import unittest
from unittest.mock import MagicMock
from app.services.snowflake_manager import SnowflakeManager
from app.services.memory_thermodynamics import MemoryPhase

class TestSnowflakeManager(unittest.TestCase):
    def setUp(self):
        # Mock PackExecutor
        self.mock_executor = MagicMock()
        
        # Mock Pack Instance
        self.mock_pack = MagicMock()
        self.mock_pack.get_snowflake_template.return_value = {
            "domain": "security",
            "focus": ["threat detection"],
            "keywords": ["security", "threat"],
            "actions": ["block_ip"],
            "patterns": ["failed_login"],
            "rules": ["if: failed_login > 5"],
            "version": "1.0.0"
        }
        
        self.mock_executor.loaded_packs = {"security": self.mock_pack}
        self.manager = SnowflakeManager(self.mock_executor)

    def test_get_domain_specializations(self):
        specs = self.manager.get_domain_specializations()
        self.assertIn("security", specs)
        self.assertEqual(specs["security"]["domain"], "security")

    def test_create_snowflake(self):
        base_pattern = {"id": "p1", "type": "auth"}
        
        # Using run to execute async create_snowflake
        import asyncio
        loop = asyncio.get_event_loop()
        snowflake = loop.run_until_complete(self.manager.create_snowflake(base_pattern, "security"))
        
        self.assertEqual(snowflake["id"], "p1_security")
        self.assertEqual(snowflake["phase"], MemoryPhase.SNOWFLAKE.value)
        self.assertEqual(snowflake["domain"], "security")
        self.assertEqual(snowflake["specialization"]["domain"], "security")

if __name__ == '__main__':
    unittest.main()
