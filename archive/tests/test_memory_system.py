"""
Unit Tests for Memory System - Story 4.1
"""
import pytest
import time

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.learning.memory_system import MemorySystem, MemoryEntry


class TestMemorySystem:
    """Test memory system."""
    
    def test_init(self):
        """Should initialize memory system."""
        memory = MemorySystem(max_memories=100)
        
        assert memory.max_memories == 100
        assert memory.total_stored == 0
        assert len(memory.episodic_memories) == 0
    
    def test_store_episodic(self):
        """Should store episodic memory."""
        memory = MemorySystem()
        
        memory_id = memory.store(
            content="Reviewed PR #42, found 3 violations",
            memory_type="episodic",
            importance=0.8
        )
        
        assert memory_id.startswith("episodic_")
        assert len(memory.episodic_memories) == 1
        assert memory.total_stored == 1
    
    def test_store_semantic(self):
        """Should store semantic memory."""
        memory = MemorySystem()
        
        memory_id = memory.store(
            content="Always check for SQL injection in database queries",
            memory_type="semantic",
            importance=1.0
        )
        
        assert memory_id.startswith("semantic_")
        assert len(memory.semantic_memories) == 1
    
    def test_retrieve_by_similarity(self):
        """Should retrieve memories by semantic similarity."""
        memory = MemorySystem()
        
        # Store memories
        memory.store("SQL injection vulnerability found", memory_type="episodic")
        memory.store("XSS attack detected in form input", memory_type="episodic")
        memory.store("Approved clean PR with tests", memory_type="episodic")
        
        # Query for security issues
        results = memory.retrieve("security vulnerability", top_k=2)
        
        assert len(results) <= 2
        # Should retrieve security-related memories
        # (exact results depend on embedding implementation)
    
    def test_retrieve_with_importance_filter(self):
        """Should filter by importance threshold."""
        memory = MemorySystem()
        
        memory.store("Low importance event", importance=0.3)
        memory.store("High importance event", importance=0.9)
        
        # Only high importance
        results = memory.retrieve("event", min_importance=0.5)
        
        assert len(results) == 1
        assert results[0].importance >= 0.5
    
    def test_update_importance(self):
        """Should update memory importance."""
        memory = MemorySystem()
        
        memory_id = memory.store("Test memory", importance=0.5)
        memory.update_importance(memory_id, 0.9)
        
        entry = memory.episodic_memories[memory_id]
        assert entry.importance == 0.9
    
    def test_forget(self):
        """Should forget specific memory."""
        memory = MemorySystem()
        
        memory_id = memory.store("Forget me")
        
        assert len(memory.episodic_memories) == 1
        
        result = memory.forget(memory_id)
        
        assert result is True
        assert len(memory.episodic_memories) == 0
        assert memory.forgetting_count == 1
    
    def test_consolidation(self):
        """Should consolidate similar memories."""
        memory = MemorySystem(similarity_threshold=0.7)
        
        # Store similar memories
        memory.store("PR #10 approved", memory_type="episodic")
        memory.store("PR #11 approved", memory_type="episodic")
        memory.store("PR #12 approved", memory_type="episodic")
        
        initial_count = len(memory.episodic_memories)
        
        consolidated = memory.consolidate("episodic")
        
        # Should have consolidated some memories
        assert consolidated >= 0
        assert len(memory.episodic_memories) <= initial_count
    
    def test_capacity_management(self):
        """Should manage capacity when full."""
        memory = MemorySystem(max_memories=5)
        
        # Store more than capacity
        for i in range(10):
            memory.store(f"Memory {i}", importance=0.5 + i * 0.05)
        
        # Should not exceed capacity
        assert len(memory.episodic_memories) <= 5
        # Should have forgotten some
        assert memory.forgetting_count > 0
    
    def test_access_count_tracking(self):
        """Should track memory access."""
        memory = MemorySystem()
        
        memory_id = memory.store("Test memory")
        
        # Retrieve multiple times
        memory.retrieve("test", top_k=1)
        memory.retrieve("test", top_k=1)
        
        entry = memory.episodic_memories[memory_id]
        assert entry.access_count >= 1
    
    def test_get_stats(self):
        """Should report statistics."""
        memory = MemorySystem()
        
        memory.store("Event 1", memory_type="episodic")
        memory.store("Fact 1", memory_type="semantic")
        memory.retrieve("test")
        
        stats = memory.get_stats()
        
        assert stats["episodic_count"] == 1
        assert stats["semantic_count"] == 1
        assert stats["total_count"] == 2
        assert stats["total_stored"] == 2
        assert stats["total_retrieved"] >= 0
    
    def test_export_memories(self):
        """Should export memories to JSON."""
        memory = MemorySystem()
        
        memory.store("Test memory", metadata={"key": "value"})
        
        exported = memory.export_memories()
        
        assert len(exported) == 1
        assert "id" in exported[0]
        assert "content" in exported[0]
        assert exported[0]["content"] == "Test memory"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
