import pytest
from compiler.validator import PackValidator

class TestPackValidator:
    def test_valid_pack_passes(self, valid_pack_data):
        """A correctly formatted pack should pass validation"""
        validator = PackValidator()
        assert validator.validate(valid_pack_data) == True
        assert len(validator.errors) == 0

    def test_missing_required_field_fails(self, valid_pack_data):
        """Missing required fields should cause validation to fail"""
        invalid_data = valid_pack_data.copy()
        del invalid_data['pack']['version']
        
        validator = PackValidator()
        # The current validator implementation returns False if 'pack' is missing version
        # Let's verify our implementation
        assert validator.validate(invalid_data) == False
        assert any("version" in err.message for err in validator.errors)

    def test_invalid_autonomy_level_fails(self, valid_pack_data):
        """Only allowed autonomy levels should pass"""
        invalid_data = valid_pack_data.copy()
        invalid_data["policies"][0]["autonomy"]["level"] = "impossible_level"
        validator = PackValidator()
        assert validator.validate(invalid_data) == False

    def test_invalid_confidence_threshold_fails(self, valid_pack_data):
        """Confidence threshold must be between 0 and 1"""
        invalid_data = valid_pack_data.copy()
        invalid_data["policies"][0]["confidence_threshold"] = 1.5
        validator = PackValidator()
        assert validator.validate(invalid_data) == False
