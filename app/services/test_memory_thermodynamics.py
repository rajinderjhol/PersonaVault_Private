
import unittest
from app.services.memory_thermodynamics import PatternPhaseManager, MemoryPhase

class TestPatternPhaseManager(unittest.TestCase):
    def setUp(self):
        self.manager = PatternPhaseManager()

    def test_freezing_trigger(self):
        pattern = {
            "id": "test_1",
            "phase": MemoryPhase.LIQUID.value,
            "confidence": 0.9,
            "failure_rate": 0.05,
            "age_days": 10
        }
        new_phase = self.manager.check_transition_triggers(pattern)
        self.assertEqual(new_phase, MemoryPhase.ICE)

    def test_melting_trigger(self):
        pattern = {
            "id": "test_2",
            "phase": MemoryPhase.ICE.value,
            "confidence": 0.9,
            "failure_rate": 0.3,
            "age_days": 10
        }
        new_phase = self.manager.check_transition_triggers(pattern)
        self.assertEqual(new_phase, MemoryPhase.LIQUID)

if __name__ == '__main__':
    unittest.main()
