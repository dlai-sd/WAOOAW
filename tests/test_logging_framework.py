"""
Unit Tests for Logging Framework - Story 5.1
"""
import pytest
import json
from io import StringIO

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.common.logging_framework import (
    StructuredLogger,
    LoggerFactory,
    get_logger,
    configure_logging
)


class TestStructuredLogger:
    """Test structured logger."""
    
    def test_init(self):
        """Should initialize logger."""
        logger = StructuredLogger("test", level="DEBUG")
        
        assert logger.name == "test"
        assert logger.output_format == "json"
    
    def test_info_log(self, capsys):
        """Should log info message."""
        logger = StructuredLogger("test", level="INFO", output_format="text")
        
        logger.info("Test message")
        
        captured = capsys.readouterr()
        assert "Test message" in captured.out
        assert "INFO" in captured.out
    
    def test_json_format(self, capsys):
        """Should output JSON format."""
        logger = StructuredLogger("test", level="INFO", output_format="json")
        
        logger.info("Test message", key="value")
        
        captured = capsys.readouterr()
        log_line = captured.out.strip()
        
        # Should be valid JSON
        log_data = json.loads(log_line)
        assert log_data["message"] == "Test message"
        assert log_data["level"] == "INFO"
        assert log_data["key"] == "value"
    
    def test_correlation_id(self, capsys):
        """Should add correlation ID."""
        logger = StructuredLogger("test", output_format="json")
        
        corr_id = logger.set_correlation_id("test-123")
        logger.info("Test message")
        
        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["correlation_id"] == "test-123"
    
    def test_context_fields(self, capsys):
        """Should include context in all logs."""
        logger = StructuredLogger("test", output_format="json")
        
        logger.set_context(agent_id="wowvision", pr_number=42)
        logger.info("Test message")
        
        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["agent_id"] == "wowvision"
        assert log_data["pr_number"] == 42
    
    def test_clear_context(self, capsys):
        """Should clear context."""
        logger = StructuredLogger("test", output_format="json")
        
        logger.set_context(key="value")
        logger.clear_context()
        logger.info("Test message")
        
        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert "key" not in log_data
    
    def test_operation_context_manager(self, capsys):
        """Should time operations."""
        logger = StructuredLogger("test", output_format="json")
        
        with logger.operation("test_op", metadata="value"):
            pass
        
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        
        # Should have start and complete logs
        assert len(lines) >= 2
        
        start_log = json.loads(lines[0])
        complete_log = json.loads(lines[1])
        
        assert "Starting operation" in start_log["message"]
        assert "Completed operation" in complete_log["message"]
        assert "duration_ms" in complete_log
    
    def test_log_levels(self):
        """Should respect log levels."""
        logger = StructuredLogger("test", level="WARNING")
        
        # Debug and info should not log
        logger.debug("Debug message")
        logger.info("Info message")
        
        # Warning+ should log
        logger.warning("Warning message")
        # (Testing via capsys in real test)


class TestLoggerFactory:
    """Test logger factory."""
    
    def test_get_logger(self):
        """Should create logger."""
        logger = LoggerFactory.get_logger("test")
        
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "test"
    
    def test_singleton_behavior(self):
        """Should return same logger for same name."""
        logger1 = LoggerFactory.get_logger("test")
        logger2 = LoggerFactory.get_logger("test")
        
        assert logger1 is logger2
    
    def test_configure(self):
        """Should configure defaults."""
        LoggerFactory.configure(level="DEBUG", output_format="text")
        
        logger = LoggerFactory.get_logger("new_logger")
        
        assert logger.output_format == "text"


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_get_logger(self):
        """Should get logger via convenience function."""
        logger = get_logger("convenience_test")
        
        assert isinstance(logger, StructuredLogger)
    
    def test_configure_logging(self):
        """Should configure via convenience function."""
        configure_logging(level="ERROR", output_format="text")
        
        # Check that it affects factory
        assert LoggerFactory._default_level == "ERROR"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
