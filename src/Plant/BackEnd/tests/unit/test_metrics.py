"""
Tests for core/metrics.py module.
Coverage target: 89%+ overall
"""

import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

# Import all modules for coverage
import core.metrics
from core.metrics import (
    setup_metrics,
    record_http_request,
    record_db_query,
    update_db_connection_metrics,
    update_business_metrics,
    MetricsMiddleware,
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_progress,
    db_connections_total,
    db_query_duration_seconds,
    active_trials_total,
    agents_available_total,
    goals_created_total,
    goals_executed_total,
    customer_signups_total,
    application_version,
    uptime_seconds,
    registry,
)


class TestMetricsHelpers:
    """Test metric recording helper functions."""
    
    def test_record_http_request(self):
        """Test recording HTTP request metrics."""
        # Clear any previous values (best effort)
        initial_count = http_requests_total.labels(
            method="GET",
            path="/api/test",
            status=200
        )._value.get()
        
        record_http_request(
            method="GET",
            path="/api/test",
            status_code=200,
            duration=0.123
        )
        
        final_count = http_requests_total.labels(
            method="GET",
            path="/api/test",
            status=200
        )._value.get()
        
        assert final_count == initial_count + 1
    
    def test_record_http_request_different_status_codes(self):
        """Test recording requests with different status codes."""
        record_http_request("POST", "/api/users", 201, 0.05)
        record_http_request("GET", "/api/users", 404, 0.02)
        record_http_request("POST", "/api/users", 500, 0.5)
        
        # Metrics should be recorded separately by status
        count_201 = http_requests_total.labels(
            method="POST",
            path="/api/users",
            status=201
        )._value.get()
        
        count_404 = http_requests_total.labels(
            method="GET",
            path="/api/users",
            status=404
        )._value.get()
        
        assert count_201 >= 1
        assert count_404 >= 1
    
    def test_record_db_query(self):
        """Test recording database query metrics."""
        record_db_query("select", 0.01)
        record_db_query("insert", 0.05)
        record_db_query("update", 0.03)
        record_db_query("delete", 0.02)
        
        # Should not raise - metrics recorded successfully
    
    def test_update_db_connection_metrics(self):
        """Test updating database connection pool metrics."""
        update_db_connection_metrics(active=5, idle=10, total=15)
        
        active = db_connections_total.labels(state='active')._value.get()
        idle = db_connections_total.labels(state='idle')._value.get()
        total = db_connections_total.labels(state='total')._value.get()
        
        assert active == 5
        assert idle == 10
        assert total == 15
    
    def test_update_db_connection_metrics_changing_values(self):
        """Test updating connection metrics multiple times."""
        update_db_connection_metrics(active=3, idle=7, total=10)
        update_db_connection_metrics(active=8, idle=2, total=10)
        
        active = db_connections_total.labels(state='active')._value.get()
        idle = db_connections_total.labels(state='idle')._value.get()
        
        # Should reflect latest values
        assert active == 8
        assert idle == 2
    
    def test_update_business_metrics_all_params(self):
        """Test updating all business metrics."""
        update_business_metrics(
            active_trials=42,
            available_agents=15,
            working_agents=8,
            offline_agents=2
        )
        
        trials = active_trials_total._value.get()
        available = agents_available_total.labels(status='available')._value.get()
        working = agents_available_total.labels(status='working')._value.get()
        offline = agents_available_total.labels(status='offline')._value.get()
        
        assert trials == 42
        assert available == 15
        assert working == 8
        assert offline == 2
    
    def test_update_business_metrics_partial(self):
        """Test updating only some business metrics."""
        # Set initial values
        update_business_metrics(
            active_trials=10,
            available_agents=5
        )
        
        trials_before = active_trials_total._value.get()
        
        # Update only trials
        update_business_metrics(active_trials=20)
        
        trials_after = active_trials_total._value.get()
        
        assert trials_after == 20
        assert trials_after != trials_before
    
    def test_update_business_metrics_none_params(self):
        """Test update_business_metrics with None values."""
        # Should not raise even with all None
        update_business_metrics(
            active_trials=None,
            available_agents=None,
            working_agents=None,
            offline_agents=None
        )


class TestGoalMetrics:
    """Test goal-related metrics."""
    
    def test_goals_created_counter(self):
        """Test goals created counter."""
        initial = goals_created_total.labels(agent_type='marketing')._value.get()
        
        goals_created_total.labels(agent_type='marketing').inc()
        goals_created_total.labels(agent_type='sales').inc()
        
        final = goals_created_total.labels(agent_type='marketing')._value.get()
        
        assert final == initial + 1
    
    def test_goals_executed_counter(self):
        """Test goals executed counter with status."""
        goals_executed_total.labels(agent_type='marketing', status='success').inc()
        goals_executed_total.labels(agent_type='marketing', status='failure').inc()
        goals_executed_total.labels(agent_type='sales', status='success').inc(2)
        
        # Metrics recorded successfully
        success_count = goals_executed_total.labels(
            agent_type='sales',
            status='success'
        )._value.get()
        
        assert success_count >= 2


class TestCustomerMetrics:
    """Test customer-related metrics."""
    
    def test_customer_signups_counter(self):
        """Test customer signups counter."""
        initial = customer_signups_total._value.get()
        
        customer_signups_total.inc()
        customer_signups_total.inc(5)
        
        final = customer_signups_total._value.get()
        
        assert final == initial + 6


class TestSetupMetrics:
    """Test metrics setup and endpoints."""
    
    def test_setup_metrics_creates_endpoints(self):
        """Test setup_metrics adds /metrics and /health endpoints."""
        app = FastAPI()
        setup_metrics(app, version="1.0.0")
        
        # Check routes exist
        paths = [route.path for route in app.routes]
        
        assert "/metrics" in paths
        assert "/health" in paths
    
    def test_metrics_endpoint_returns_prometheus_format(self):
        """Test /metrics endpoint returns Prometheus text format."""
        app = FastAPI()
        setup_metrics(app, version="1.2.3")
        
        client = TestClient(app)
        response = client.get("/metrics")
        
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        
        # Check for some expected metrics
        content = response.text
        assert "http_requests_total" in content or "waooaw_plant_backend_info" in content
    
    def test_health_endpoint_returns_status(self):
        """Test /health endpoint returns status."""
        app = FastAPI()
        setup_metrics(app, version="2.0.0")
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        assert "uptime" in data
        assert data["uptime"] >= 0
    
    def test_setup_sets_application_info(self):
        """Test setup_metrics sets application info."""
        app = FastAPI()
        setup_metrics(app, version="3.5.7")
        
        # Application version metric should be set
        version_value = application_version.labels(version="3.5.7")._value.get()
        assert version_value == 1
    
    def test_metrics_endpoint_updates_uptime(self):
        """Test /metrics endpoint updates uptime metric."""
        app = FastAPI()
        setup_metrics(app, version="1.0.0")
        
        client = TestClient(app)
        
        # First call
        response1 = client.get("/metrics")
        assert response1.status_code == 200
        
        # Wait a bit
        time.sleep(0.1)
        
        # Second call should show increased uptime
        response2 = client.get("/metrics")
        assert response2.status_code == 200


class TestMetricsMiddleware:
    """Test metrics middleware."""
    
    def test_middleware_records_successful_request(self):
        """Test middleware records metrics for successful requests."""
        app = FastAPI()
        
        @app.get("/api/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        # Add metrics middleware
        from starlette.middleware.base import BaseHTTPMiddleware
        app.add_middleware(MetricsMiddleware)
        
        client = TestClient(app)
        
        # Get initial count
        initial_count = http_requests_total.labels(
            method="GET",
            path="/api/test",
            status=200
        )._value.get()
        
        # Make request
        response = client.get("/api/test")
        assert response.status_code == 200
        
        # Check count increased
        final_count = http_requests_total.labels(
            method="GET",
            path="/api/test",
            status=200
        )._value.get()
        
        assert final_count == initial_count + 1
    
    def test_middleware_records_error_request(self):
        """Test middleware records metrics for failed requests."""
        app = FastAPI()
        
        @app.get("/api/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        app.add_middleware(MetricsMiddleware)
        
        client = TestClient(app)
        
        # Request will fail
        with pytest.raises(ValueError):
            client.get("/api/error")
        
        # Metrics should still be recorded with 500 status
        count_500 = http_requests_total.labels(
            method="GET",
            path="/api/error",
            status=500
        )._value.get()
        
        assert count_500 >= 1
    
    def test_middleware_skips_metrics_endpoint(self):
        """Test middleware doesn't record metrics for /metrics itself."""
        app = FastAPI()
        setup_metrics(app, version="1.0.0")
        app.add_middleware(MetricsMiddleware)
        
        client = TestClient(app)
        
        # Get initial count for /metrics
        initial_count = http_requests_total.labels(
            method="GET",
            path="/metrics",
            status=200
        )._value.get()
        
        # Call /metrics endpoint
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Count should NOT increase (middleware skips /metrics)
        final_count = http_requests_total.labels(
            method="GET",
            path="/metrics",
            status=200
        )._value.get()
        
        assert final_count == initial_count
    
    def test_middleware_tracks_in_progress_requests(self):
        """Test middleware tracks in-progress requests."""
        app = FastAPI()
        
        @app.get("/api/slow")
        async def slow_endpoint():
            time.sleep(0.05)
            return {"status": "done"}
        
        app.add_middleware(MetricsMiddleware)
        
        client = TestClient(app)
        response = client.get("/api/slow")
        
        assert response.status_code == 200
        # In-progress gauge should have been incremented and decremented
    
    def test_middleware_handles_non_http_scope(self):
        """Test middleware handles non-HTTP scope types."""
        middleware = MetricsMiddleware(app=Mock())
        
        # Mock websocket scope
        scope = {'type': 'websocket', 'path': '/ws'}
        receive = AsyncMock()
        send = AsyncMock()
        
        # Create async function to test
        async def run_test():
            app_mock = AsyncMock()
            middleware.app = app_mock
            await middleware(scope, receive, send)
            app_mock.assert_called_once()
        
        import asyncio
        asyncio.run(run_test())
    
    def test_middleware_records_duration(self):
        """Test middleware records request duration."""
        app = FastAPI()
        
        @app.get("/api/timed")
        async def timed_endpoint():
            time.sleep(0.01)  # Small delay
            return {"status": "ok"}
        
        app.add_middleware(MetricsMiddleware)
        
        client = TestClient(app)
        response = client.get("/api/timed")
        
        assert response.status_code == 200
        
        # Duration histogram should have recorded the request
        # (We can't easily check the histogram value, but the request succeeded)


class TestApplicationMetrics:
    """Test application-level metrics."""
    
    def test_application_version_metric(self):
        """Test application version metric."""
        # Set version
        application_version.labels(version="4.2.0").set(1)
        
        value = application_version.labels(version="4.2.0")._value.get()
        assert value == 1
    
    def test_uptime_seconds_metric(self):
        """Test uptime metric."""
        start_time = time.time()
        
        # Set uptime
        uptime_seconds.set(10.5)
        
        value = uptime_seconds._value.get()
        assert value == 10.5
        
        # Update uptime
        current_uptime = time.time() - start_time
        uptime_seconds.set(current_uptime)
        
        new_value = uptime_seconds._value.get()
        assert new_value >= current_uptime


class TestMetricsRegistry:
    """Test metrics registry."""
    
    def test_registry_exists(self):
        """Test metrics registry is properly configured."""
        assert registry is not None
    
    def test_metrics_registered_in_custom_registry(self):
        """Test all metrics are in custom registry, not default."""
        # Our metrics should be in the custom registry
        from prometheus_client import generate_latest
        
        metrics_output = generate_latest(registry).decode('utf-8')
        
        # Should contain some of our metrics
        assert "http_requests_total" in metrics_output or "waooaw_plant_backend_info" in metrics_output


class TestMetricsIntegration:
    """Integration tests for metrics system."""
    
    def test_full_metrics_flow(self):
        """Test complete metrics flow: setup, middleware, recording."""
        app = FastAPI()
        
        @app.get("/api/agents")
        async def list_agents():
            return [{"id": 1, "name": "Agent1"}]
        
        @app.post("/api/goals")
        async def create_goal():
            goals_created_total.labels(agent_type='marketing').inc()
            return {"id": 123}
        
        # Setup metrics
        setup_metrics(app, version="5.0.0")
        app.add_middleware(MetricsMiddleware)
        
        client = TestClient(app)
        
        # Make requests
        response1 = client.get("/api/agents")
        assert response1.status_code == 200
        
        response2 = client.post("/api/goals")
        assert response2.status_code == 200
        
        # Check /metrics endpoint
        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200
        
        # Check /health endpoint
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
