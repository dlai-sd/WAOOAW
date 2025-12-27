"""
Integration Tests - Logging + Metrics + Idempotency

Tests operational components working together.
"""
import pytest
import time
import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.common.logging_framework import get_logger, configure_logging
from waooaw.common.metrics import MetricsCollector
from waooaw.common.idempotency import IdempotencyManager


class TestOperationsIntegration:
    """Integration tests for operational components."""
    
    def test_logging_metrics_integration(self):
        """Should integrate logging and metrics."""
        configure_logging(level="INFO", format="json")
        logger = get_logger("test")
        
        metrics = MetricsCollector()
        counter = metrics.counter("requests_total", "Total requests")
        histogram = metrics.histogram("request_duration", "Request duration")
        
        # Simulate operations with logging and metrics
        for i in range(5):
            logger.info(f"Processing request {i}")
            counter.inc()
            
            # Simulate work
            start = time.time()
            time.sleep(0.01)
            duration = time.time() - start
            
            histogram.observe(duration)
        
        # Should have metrics
        assert counter.get() == 5.0
        assert histogram.get_count() == 5
        
        # Should have logged
        # (Can't easily verify logs without capturing, but no errors is good)
    
    def test_metrics_idempotency_integration(self):
        """Should integrate metrics and idempotency."""
        metrics = MetricsCollector()
        idempotency = IdempotencyManager()
        
        # Track idempotent operations
        operations_counter = metrics.counter(
            "idempotent_operations",
            "Idempotent operations"
        )
        
        duplicates_counter = metrics.counter(
            "duplicate_operations",
            "Duplicate operations"
        )
        
        # Perform operations
        for i in range(10):
            key = idempotency.generate_key("send_email", {"to": f"user{i % 3}@example.com"})
            
            if idempotency.is_duplicate(key):
                duplicates_counter.inc()
            else:
                idempotency.start_operation(key, "send_email")
                idempotency.complete_operation(key, {"sent": True})
                operations_counter.inc()
        
        # Should have detected duplicates
        assert operations_counter.get() == 3  # Only 3 unique emails
        assert duplicates_counter.get() == 7  # 7 duplicates
    
    def test_logging_idempotency_integration(self):
        """Should integrate logging and idempotency."""
        configure_logging(level="DEBUG", format="json")
        logger = get_logger("idempotency_test")
        
        idempotency = IdempotencyManager()
        
        # Perform operation with logging
        key = idempotency.generate_key("process_payment", {"order_id": 123})
        
        if idempotency.is_duplicate(key):
            logger.warning("Duplicate payment attempt detected", extra={"key": key})
        else:
            logger.info("Processing payment", extra={"key": key})
            idempotency.start_operation(key, "process_payment")
            
            # Simulate processing
            result = {"status": "success", "transaction_id": "txn_123"}
            
            idempotency.complete_operation(key, result)
            logger.info("Payment processed", extra={"result": result})
        
        # Try duplicate
        if idempotency.is_duplicate(key):
            logger.warning("Duplicate detected - returning cached result")
            cached = idempotency.get_result(key)
            assert cached["status"] == "success"
    
    def test_full_operations_stack(self):
        """Should use full operations stack together."""
        # Set up logging
        configure_logging(level="INFO", format="json")
        logger = get_logger("operations")
        
        # Set up metrics
        metrics = MetricsCollector()
        operations = metrics.counter("operations_total", "Total operations")
        duration_histogram = metrics.histogram("operation_duration", "Operation duration")
        errors = metrics.counter("errors_total", "Total errors")
        
        # Set up idempotency
        idempotency = IdempotencyManager()
        
        # Simulate operations
        test_operations = [
            {"op": "create_user", "data": {"email": "user1@example.com"}},
            {"op": "create_user", "data": {"email": "user1@example.com"}},  # Duplicate
            {"op": "create_user", "data": {"email": "user2@example.com"}},
            {"op": "send_email", "data": {"to": "user1@example.com"}},
        ]
        
        for op_data in test_operations:
            op_name = op_data["op"]
            data = op_data["data"]
            
            # Generate idempotency key
            key = idempotency.generate_key(op_name, data)
            
            # Check for duplicate
            if idempotency.is_duplicate(key):
                logger.info(f"Duplicate {op_name} detected", extra={"key": key})
                continue
            
            # Log operation start
            logger.info(f"Starting {op_name}", extra={"data": data})
            
            # Start idempotent operation
            idempotency.start_operation(key, op_name)
            
            # Measure duration
            start = time.time()
            
            try:
                # Simulate work
                time.sleep(0.01)
                result = {"status": "success"}
                
                # Complete operation
                idempotency.complete_operation(key, result)
                
                # Record metrics
                operations.inc()
                duration = time.time() - start
                duration_histogram.observe(duration)
                
                logger.info(f"Completed {op_name}", extra={"duration": duration})
                
            except Exception as e:
                errors.inc()
                logger.error(f"Failed {op_name}", extra={"error": str(e)})
                idempotency.fail_operation(key, str(e))
        
        # Verify results
        assert operations.get() == 3  # 3 unique operations
        assert duration_histogram.get_count() == 3
        
        # Get idempotency stats
        idem_stats = idempotency.get_stats()
        assert idem_stats["total_records"] == 3
        assert idem_stats["completed"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
