"""
Tests for WorkingMemory service - matching actual implementation.
"""
import pytest
from app.services.working_memory import WorkingMemory

class TestWorkingMemory:
    """Test suite for WorkingMemory."""
    
    def test_init(self):
        """Test WorkingMemory initialization."""
        memory = WorkingMemory()
        assert memory is not None
        assert memory.session_data == {}
    
    def test_set_and_get(self):
        """Test setting and getting values."""
        memory = WorkingMemory()
        
        memory.set("key1", "value1")
        value = memory.get("key1")
        assert value == "value1"
    
    def test_get_nonexistent_key(self):
        """Test getting a nonexistent key."""
        memory = WorkingMemory()
        value = memory.get("nonexistent")
        assert value is None
    
    def test_update_existing_key(self):
        """Test updating an existing key."""
        memory = WorkingMemory()
        
        memory.set("key1", "value1")
        assert memory.get("key1") == "value1"
        
        memory.update("key1", "value2")
        assert memory.get("key1") == "value2"
    
    def test_update_new_key(self):
        """Test updating a new key (should work like set)."""
        memory = WorkingMemory()
        
        memory.update("newkey", "newvalue")
        assert memory.get("newkey") == "newvalue"
    
    def test_clear_memory(self):
        """Test clearing all memory."""
        memory = WorkingMemory()
        
        memory.set("key1", "value1")
        memory.set("key2", "value2")
        
        assert memory.get("key1") == "value1"
        assert memory.get("key2") == "value2"
        
        memory.clear()
        
        assert memory.get("key1") is None
        assert memory.get("key2") is None
    
    def test_get_all(self):
        """Test getting all session data."""
        memory = WorkingMemory()
        
        memory.set("key1", "value1")
        memory.set("key2", "value2")
        
        all_data = memory.get_all()
        assert all_data["key1"] == "value1"
        assert all_data["key2"] == "value2"
    
    def test_get_all_returns_copy(self):
        """Test that get_all returns a copy, not the original."""
        memory = WorkingMemory()
        
        memory.set("key1", "value1")
        all_data = memory.get_all()
        
        # Modifying the returned dict should not affect the original
        all_data["key1"] = "modified"
        assert memory.get("key1") == "value1"
    
    def test_set_multiple_keys(self):
        """Test setting multiple keys."""
        memory = WorkingMemory()
        
        memory.set("a", 1)
        memory.set("b", 2)
        memory.set("c", 3)
        
        assert memory.get("a") == 1
        assert memory.get("b") == 2
        assert memory.get("c") == 3

if __name__ == "__main__":
    pytest.main(["-v", __file__])
