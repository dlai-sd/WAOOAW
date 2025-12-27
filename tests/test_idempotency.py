"""
Unit Tests for Idempotency System - Story 5.4
"""
import pytest
import time

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.common.idempotency import (
    IdempotencyManager,
    OperationStatus
)


class TestIdempotencyManager:
    """Test idempotency manager."""
    
    def test_init(self):
        """Should initialize manager."""
        manager = IdempotencyManager(ttl=3600)
        
        assert manager.ttl == 3600
        assert len(manager.records) == 0
    
    def test_generate_key(self):
        """Should generate deterministic keys."""
        manager = IdempotencyManager()
        
        key1 = manager.generate_key("send_email", {"to": "user@example.com"})
        key2 = manager.generate_key("send_email", {"to": "user@example.com"})
        
        assert key1 == key2
        assert key1.startswith("idem_send_email_")
    
    def test_start_operation(self):
        """Should mark operation as started."""
        manager = IdempotencyManager()
        
        key = "test_key_1"
        manager.start_operation(key, "test_op")
        
        assert key in manager.records
        assert manager.records[key].status == OperationStatus.IN_PROGRESS
    
    def test_complete_operation(self):
        """Should mark operation as completed."""
        manager = IdempotencyManager()
        
        key = "test_key_1"
        manager.start_operation(key, "test_op")
        manager.complete_operation(key, {"status": "success"})
        
        assert manager.records[key].status == OperationStatus.COMPLETED
        assert manager.records[key].result == {"status": "success"}
    
    def test_fail_operation(self):
        """Should mark operation as failed."""
        manager = IdempotencyManager()
        
        key = "test_key_1"
        manager.start_operation(key, "test_op")
        manager.fail_operation(key, "Network error")
        
        assert manager.records[key].status == OperationStatus.FAILED
        assert manager.records[key].error == "Network error"
    
    def test_is_duplicate(self):
        """Should detect duplicate operations."""
        manager = IdempotencyManager()
        
        key = "test_key_1"
        
        # Not duplicate initially
        assert not manager.is_duplicate(key)
        
        # Start operation
        manager.start_operation(key, "test_op")
        
        # Now it's duplicate (in progress)
        assert manager.is_duplicate(key)
        
        # Complete
        manager.complete_operation(key, "result")
        
        # Still duplicate (completed)
        assert manager.is_duplicate(key)
    
    def test_get_result(self):
        """Should return cached result."""
        manager = IdempotencyManager()
        
        key = "test_key_1"
        manager.start_operation(key, "test_op")
        manager.complete_operation(key, {"data": "result"})
        
        result = manager.get_result(key)
        
        assert result == {"data": "result"}
    
    def test_can_retry(self):
        """Should check if retry allowed."""
        manager = IdempotencyManager()
        
        key = "test_key_1"
        
        # Can retry initially
        assert manager.can_retry(key, max_attempts=3)
        
        # Start and fail multiple times
        for i in range(3):
            manager.start_operation(key, "test_op")
            manager.fail_operation(key, "error")
        
        # Cannot retry after max attempts
        assert not manager.can_retry(key, max_attempts=3)
    
    def test_ttl_cleanup(self):
        """Should cleanup expired records."""
        manager = IdempotencyManager(ttl=1)  # 1 second TTL
        
        key = "test_key_1"
        manager.start_operation(key, "test_op")
        manager.complete_operation(key, "result")
        
        # Record exists
        assert key in manager.records
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Trigger cleanup
        manager._cleanup_expired()
        
        # Record removed
        assert key not in manager.records
    
    def test_stats(self):
        """Should report statistics."""
        manager = IdempotencyManager()
        
        manager.start_operation("key1", "op1")
        manager.complete_operation("key1", "result")
        
        manager.start_operation("key2", "op2")
        manager.fail_operation("key2", "error")
        
        manager.start_operation("key3", "op3")
        
        stats = manager.get_stats()
        
        assert stats["total_records"] == 3
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["in_progress"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
