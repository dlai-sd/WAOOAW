"""
Unit Tests for Health Checks - Story 5.5
"""
import pytest

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.common.health_checks import (
    HealthCheckManager,
    FunctionHealthCheck,
    HealthStatus
)


class TestHealthChecks:
    """Test health checks."""
    
    def test_init(self):
        """Should initialize manager."""
        manager = HealthCheckManager()
        
        assert len(manager.checks) == 0
    
    def test_register_function(self):
        """Should register function-based check."""
        manager = HealthCheckManager()
        
        def check():
            return True
        
        manager.register_function("test_check", check)
        
        assert "test_check" in manager.checks
    
    def test_healthy_check(self):
        """Should report healthy status."""
        manager = HealthCheckManager()
        
        manager.register_function("test", lambda: True)
        
        result = manager.run_check("test")
        
        assert result.status == HealthStatus.HEALTHY
    
    def test_unhealthy_check(self):
        """Should report unhealthy status."""
        manager = HealthCheckManager()
        
        manager.register_function("test", lambda: False)
        
        result = manager.run_check("test")
        
        assert result.status == HealthStatus.UNHEALTHY
    
    def test_check_exception(self):
        """Should handle check exceptions."""
        manager = HealthCheckManager()
        
        def failing_check():
            raise Exception("Connection failed")
        
        manager.register_function("test", failing_check)
        
        result = manager.run_check("test")
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "Connection failed" in result.message
    
    def test_run_all_checks(self):
        """Should run all checks."""
        manager = HealthCheckManager()
        
        manager.register_function("check1", lambda: True)
        manager.register_function("check2", lambda: True)
        
        results = manager.run_all_checks()
        
        assert len(results) == 2
        assert "check1" in results
        assert "check2" in results
    
    def test_overall_status_healthy(self):
        """Should aggregate healthy status."""
        manager = HealthCheckManager()
        
        manager.register_function("check1", lambda: True)
        manager.register_function("check2", lambda: True)
        
        manager.run_all_checks()
        status = manager.get_overall_status()
        
        assert status == HealthStatus.HEALTHY
    
    def test_overall_status_unhealthy(self):
        """Should aggregate unhealthy status."""
        manager = HealthCheckManager()
        
        manager.register_function("check1", lambda: True)
        manager.register_function("check2", lambda: False, critical=True)
        
        manager.run_all_checks()
        status = manager.get_overall_status()
        
        assert status == HealthStatus.UNHEALTHY
    
    def test_overall_status_degraded(self):
        """Should aggregate degraded status."""
        manager = HealthCheckManager()
        
        manager.register_function("check1", lambda: True)
        manager.register_function("check2", lambda: False, critical=False)
        
        manager.run_all_checks()
        status = manager.get_overall_status()
        
        assert status == HealthStatus.DEGRADED
    
    def test_liveness_probe(self):
        """Should report liveness."""
        manager = HealthCheckManager()
        
        assert manager.liveness_probe() is True
    
    def test_readiness_probe(self):
        """Should report readiness."""
        manager = HealthCheckManager()
        
        manager.register_function("check", lambda: True)
        
        assert manager.readiness_probe() is True
    
    def test_health_report(self):
        """Should generate health report."""
        manager = HealthCheckManager()
        
        manager.register_function("check1", lambda: True)
        manager.register_function("check2", lambda: False)
        
        report = manager.get_health_report()
        
        assert "status" in report
        assert "checks" in report
        assert len(report["checks"]) == 2
    
    def test_stats(self):
        """Should report statistics."""
        manager = HealthCheckManager()
        
        manager.register_function("check", lambda: True)
        manager.run_check("check")
        
        stats = manager.get_stats()
        
        assert stats["total_checks"] == 1
        assert stats["checks_run"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
