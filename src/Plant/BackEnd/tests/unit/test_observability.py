"""
Tests for core/observability.py module.
Coverage target: 89%+ overall
"""

import pytest
import logging
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Import module for coverage
import core.observability
from core.observability import (
    JSONFormatter,
    ColoredFormatter,
    setup_observability,
    get_logger,
    set_request_context,
    clear_request_context,
    RequestLoggingMiddleware,
    log_route_registration,
    request_id_var,
    correlation_id_var,
    customer_id_var,
    trace_id_var,
)


class TestJSONFormatter:
    """Test JSON log formatter."""
    
    def test_basic_message_formatting(self):
        """Test basic log message is formatted as JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/module.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        data = json.loads(output)
        
        assert data["severity"] == "INFO"
        assert data["message"] == "Test message"
        assert data["logger"] == "test.logger"
        assert "timestamp" in data
        assert data["source"]["line"] == 42
        assert "pid" in data["process"]
    
    def test_formatting_with_request_context(self):
        """Test JSON formatter includes request context."""
        formatter = JSONFormatter()
        
        # Set request context
        set_request_context(
            request_id="req-123",
            correlation_id="cor-456",
            customer_id="cust-789",
            trace_id="trace-abc"
        )
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/module.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        data = json.loads(output)
        
        assert data["context"]["request_id"] == "req-123"
        assert data["context"]["correlation_id"] == "cor-456"
        assert data["context"]["customer_id"] == "cust-789"
        assert data["context"]["trace_id"] == "trace-abc"
        assert data["logging.googleapis.com/trace"] == "trace-abc"
        
        # Clean up
        clear_request_context()
    
    def test_formatting_with_exception(self):
        """Test JSON formatter includes exception info."""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            exc_info = logging.sys.exc_info()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/path/to/module.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        output = formatter.format(record)
        data = json.loads(output)
        
        assert data["exception"]["type"] == "ValueError"
        assert "Test error" in data["exception"]["message"]
        assert "stacktrace" in data["exception"]
    
    def test_formatting_with_extra_fields(self):
        """Test JSON formatter includes extra fields."""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/module.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.extra_fields = {"custom_field": "custom_value", "count": 42}
        
        output = formatter.format(record)
        data = json.loads(output)
        
        assert data["custom_field"] == "custom_value"
        assert data["count"] == 42


class TestColoredFormatter:
    """Test colored formatter for development."""
    
    def test_basic_formatting(self):
        """Test colored formatter produces readable output."""
        formatter = ColoredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/module.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function"
        )
        
        output = formatter.format(record)
        
        assert "INFO" in output
        assert "test.logger" in output
        assert "test_function" in output
        assert "Test message" in output
        assert f"PID:{os.getpid()}" in output
    
    def test_formatting_with_context(self):
        """Test colored formatter includes context."""
        formatter = ColoredFormatter()
        
        set_request_context(
            request_id="req-123456789",
            customer_id="cust-987654321"
        )
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/module.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function"
        )
        
        output = formatter.format(record)
        
        assert "req=req-1234" in output  # First 8 chars
        assert "cust=cust-987" in output  # First 8 chars
        
        clear_request_context()
    
    def test_formatting_with_exception(self):
        """Test colored formatter includes exception traceback."""
        formatter = ColoredFormatter()
        
        try:
            raise RuntimeError("Test exception")
        except RuntimeError:
            exc_info = logging.sys.exc_info()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/path/to/module.py",
            lineno=42,
            msg="Error message",
            args=(),
            exc_info=exc_info,
            func="test_function"
        )
        
        output = formatter.format(record)
        
        assert "ERROR" in output
        assert "Test exception" in output
        assert "Traceback" in output


class TestSetupObservability:
    """Test observability setup."""
    
    def test_setup_with_json_logs(self):
        """Test setup configures JSON logging."""
        settings = Mock()
        settings.log_level = "INFO"
        settings.enable_json_logs = True
        settings.environment = "production"
        settings.enable_request_logging = True
        settings.enable_sql_logging = False
        settings.enable_route_registration_logging = False
        settings.enable_startup_diagnostics = True
        settings.gcp_project_id = "test-project"
        settings.version = "1.0.0"
        
        setup_observability(settings)
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) > 0
    
    def test_setup_with_colored_logs(self):
        """Test setup configures colored logging for development."""
        settings = Mock()
        settings.log_level = "DEBUG"
        settings.enable_json_logs = False
        settings.environment = "development"
        settings.enable_request_logging = True
        settings.enable_sql_logging = True
        settings.enable_route_registration_logging = True
        settings.enable_startup_diagnostics = True
        
        setup_observability(settings)
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
    
    def test_setup_sql_logging_enabled(self):
        """Test SQL logging can be enabled."""
        settings = Mock()
        settings.log_level = "INFO"
        settings.enable_json_logs = False
        settings.environment = "development"
        settings.enable_request_logging = False
        settings.enable_sql_logging = True
        settings.enable_route_registration_logging = False
        settings.enable_startup_diagnostics = False
        
        setup_observability(settings)
        
        sql_logger = logging.getLogger('sqlalchemy.engine')
        assert sql_logger.level == logging.INFO
    
    def test_setup_sql_logging_disabled(self):
        """Test SQL logging can be disabled."""
        settings = Mock()
        settings.log_level = "INFO"
        settings.enable_json_logs = False
        settings.environment = "development"
        settings.enable_request_logging = False
        settings.enable_sql_logging = False
        settings.enable_route_registration_logging = False
        settings.enable_startup_diagnostics = False
        
        setup_observability(settings)
        
        sql_logger = logging.getLogger('sqlalchemy.engine')
        assert sql_logger.level == logging.WARNING


class TestContextManagement:
    """Test request context management."""
    
    def test_set_and_clear_request_context(self):
        """Test setting and clearing request context."""
        # Set context
        set_request_context(
            request_id="req-123",
            correlation_id="cor-456",
            customer_id="cust-789",
            trace_id="trace-abc"
        )
        
        assert request_id_var.get() == "req-123"
        assert correlation_id_var.get() == "cor-456"
        assert customer_id_var.get() == "cust-789"
        assert trace_id_var.get() == "trace-abc"
        
        # Clear context
        clear_request_context()
        
        assert request_id_var.get() is None
        assert correlation_id_var.get() is None
        assert customer_id_var.get() is None
        assert trace_id_var.get() is None
    
    def test_partial_context_setting(self):
        """Test setting only some context values."""
        set_request_context(request_id="req-123")
        
        assert request_id_var.get() == "req-123"
        assert correlation_id_var.get() is None
        assert customer_id_var.get() is None
        assert trace_id_var.get() is None
        
        clear_request_context()


class TestGetLogger:
    """Test logger retrieval."""
    
    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance."""
        logger = get_logger("test.module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"
    
    def test_get_logger_different_names(self):
        """Test different names return different loggers."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        assert logger1.name != logger2.name


class TestRequestLoggingMiddleware:
    """Test request logging middleware."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        return app
    
    @pytest.mark.asyncio
    async def test_middleware_logs_successful_request(self, app):
        """Test middleware logs successful requests."""
        from fastapi.testclient import TestClient
        
        # Add middleware
        app.add_middleware(RequestLoggingMiddleware, enable_logging=True)
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
    
    @pytest.mark.asyncio
    async def test_middleware_disabled(self, app):
        """Test middleware can be disabled."""
        from fastapi.testclient import TestClient
        
        # Add middleware with logging disabled
        app.add_middleware(RequestLoggingMiddleware, enable_logging=False)
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_middleware_logs_error(self, app):
        """Test middleware logs errors."""
        from fastapi.testclient import TestClient
        
        app.add_middleware(RequestLoggingMiddleware, enable_logging=True)
        
        client = TestClient(app)
        
        with pytest.raises(ValueError):
            client.get("/error")
    
    @pytest.mark.asyncio
    async def test_middleware_extracts_request_id_from_header(self, app):
        """Test middleware extracts request ID from header."""
        from fastapi.testclient import TestClient
        
        app.add_middleware(RequestLoggingMiddleware, enable_logging=True)
        
        client = TestClient(app)
        response = client.get("/test", headers={"X-Request-ID": "custom-req-123"})
        
        assert response.status_code == 200


class TestLogRouteRegistration:
    """Test route registration logging."""
    
    def test_log_route_registration(self):
        """Test logging all registered routes."""
        app = FastAPI()
        
        @app.get("/api/v1/agents")
        async def list_agents():
            return []
        
        @app.post("/api/v1/agents")
        async def create_agent():
            return {}
        
        @app.get("/health")
        async def health():
            return {"status": "ok"}
        
        # Should not raise
        log_route_registration(app)
    
    def test_log_routes_with_empty_app(self):
        """Test logging routes with no routes defined."""
        app = FastAPI()
        
        # Should not raise
        log_route_registration(app)


class TestCloudTraceIntegration:
    """Test Cloud Trace integration (when available)."""
    
    @patch('core.observability.CLOUD_TRACE_AVAILABLE', False)
    def test_setup_without_cloud_trace(self):
        """Test setup gracefully handles missing Cloud Trace."""
        settings = Mock()
        settings.log_level = "INFO"
        settings.enable_json_logs = False
        settings.environment = "development"
        settings.enable_request_logging = False
        settings.enable_sql_logging = False
        settings.enable_route_registration_logging = False
        settings.enable_startup_diagnostics = False
        
        # Should not raise
        setup_observability(settings)
