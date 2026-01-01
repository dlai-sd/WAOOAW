"""
Unit tests for HealthChecker service
"""

import pytest
import asyncio
from datetime import datetime
from waooaw_portal.services.health_checker import (
    HealthChecker,
    HealthStatus,
    HealthCheck,
    HealthReport,
)


@pytest.fixture
def health_checker():
    """Create health checker instance"""
    return HealthChecker()


@pytest.fixture
def simple_check():
    """Create a simple passing health check"""

    async def check():
        return True

    return HealthCheck(name="simple_check", check_func=check, interval=60, timeout=5)


@pytest.fixture
def failing_check():
    """Create a failing health check"""

    async def check():
        return False

    return HealthCheck(name="failing_check", check_func=check, interval=60, timeout=5)


class TestHealthChecker:
    """Test HealthChecker basic functionality"""

    @pytest.mark.asyncio
    async def test_start_stop(self, health_checker):
        """Test health checker start/stop"""
        await health_checker.start()
        assert health_checker._running is True

        await health_checker.stop()
        assert health_checker._running is False

    @pytest.mark.asyncio
    async def test_add_remove_check(self, health_checker, simple_check):
        """Test adding and removing checks"""
        await health_checker.start()

        # Add check
        health_checker.add_check(simple_check)
        assert "simple_check" in health_checker.checks

        # Remove check
        health_checker.remove_check("simple_check")
        assert "simple_check" not in health_checker.checks

        await health_checker.stop()

    @pytest.mark.asyncio
    async def test_add_multiple_checks(self, health_checker):
        """Test adding multiple checks"""
        await health_checker.start()

        async def check1():
            return True

        async def check2():
            return True

        health_checker.add_check(
            HealthCheck(name="check1", check_func=check1, interval=60, timeout=5)
        )
        health_checker.add_check(
            HealthCheck(name="check2", check_func=check2, interval=60, timeout=5)
        )

        assert len(health_checker.checks) == 2

        await health_checker.stop()


class TestHealthReports:
    """Test health report generation"""

    @pytest.mark.asyncio
    async def test_passing_check(self, health_checker, simple_check):
        """Test passing health check"""
        await health_checker.start()

        health_checker.add_check(simple_check)

        # Wait for first check
        await asyncio.sleep(0.2)

        report = health_checker.get_report("simple_check")

        assert report is not None
        assert report.status == HealthStatus.HEALTHY
        assert report.failure_count == 0

        await health_checker.stop()

    @pytest.mark.asyncio
    async def test_failing_check(self, health_checker, failing_check):
        """Test failing health check"""
        await health_checker.start()

        health_checker.add_check(failing_check)

        # Wait for first check
        await asyncio.sleep(0.2)

        report = health_checker.get_report("failing_check")

        assert report is not None
        assert report.status == HealthStatus.UNHEALTHY

        await health_checker.stop()

    @pytest.mark.asyncio
    async def test_check_with_timeout(self, health_checker):
        """Test check that times out"""

        async def slow_check():
            await asyncio.sleep(10)
            return True

        check = HealthCheck(
            name="slow_check", check_func=slow_check, interval=60, timeout=0.1
        )

        await health_checker.start()
        health_checker.add_check(check)

        await asyncio.sleep(0.3)

        report = health_checker.get_report("slow_check")
        assert report.status == HealthStatus.UNHEALTHY

        await health_checker.stop()

    @pytest.mark.asyncio
    async def test_check_with_exception(self, health_checker):
        """Test check that raises exception"""

        async def error_check():
            raise ValueError("Test error")

        check = HealthCheck(
            name="error_check", check_func=error_check, interval=60, timeout=5
        )

        await health_checker.start()
        health_checker.add_check(check)

        await asyncio.sleep(0.2)

        report = health_checker.get_report("error_check")
        assert report.status == HealthStatus.UNHEALTHY
        assert "Test error" in report.message

        await health_checker.stop()


class TestHealthStatus:
    """Test health status management"""

    @pytest.mark.asyncio
    async def test_failure_threshold(self, health_checker):
        """Test failure threshold tracking"""

        failure_count = 0

        async def intermittent_check():
            nonlocal failure_count
            failure_count += 1
            return failure_count > 3

        check = HealthCheck(
            name="intermittent",
            check_func=intermittent_check,
            interval=0.1,
            timeout=5,
            failure_threshold=3,
        )

        await health_checker.start()
        health_checker.add_check(check)

        # Wait for multiple checks
        await asyncio.sleep(0.5)

        report = health_checker.get_report("intermittent")

        # After threshold, should be healthy
        assert report.status == HealthStatus.HEALTHY

        await health_checker.stop()

    @pytest.mark.asyncio
    async def test_get_all_reports(self, health_checker):
        """Test getting all reports"""

        async def check1():
            return True

        async def check2():
            return True

        await health_checker.start()

        health_checker.add_check(
            HealthCheck(name="check1", check_func=check1, interval=60, timeout=5)
        )
        health_checker.add_check(
            HealthCheck(name="check2", check_func=check2, interval=60, timeout=5)
        )

        await asyncio.sleep(0.2)

        reports = health_checker.get_all_reports()

        assert len(reports) == 2
        assert "check1" in reports
        assert "check2" in reports

        await health_checker.stop()

    @pytest.mark.asyncio
    async def test_overall_status_all_healthy(self, health_checker):
        """Test overall status with all healthy checks"""

        async def check1():
            return True

        async def check2():
            return True

        await health_checker.start()

        health_checker.add_check(
            HealthCheck(name="check1", check_func=check1, interval=60, timeout=5)
        )
        health_checker.add_check(
            HealthCheck(name="check2", check_func=check2, interval=60, timeout=5)
        )

        await asyncio.sleep(0.2)

        status = health_checker.get_overall_status()
        assert status == HealthStatus.HEALTHY

        await health_checker.stop()

    @pytest.mark.asyncio
    async def test_overall_status_one_unhealthy(self, health_checker):
        """Test overall status with one unhealthy check"""

        async def healthy_check():
            return True

        async def unhealthy_check():
            return False

        await health_checker.start()

        health_checker.add_check(
            HealthCheck(
                name="healthy", check_func=healthy_check, interval=60, timeout=5
            )
        )
        health_checker.add_check(
            HealthCheck(
                name="unhealthy", check_func=unhealthy_check, interval=60, timeout=5
            )
        )

        await asyncio.sleep(0.2)

        status = health_checker.get_overall_status()
        assert status == HealthStatus.UNHEALTHY

        await health_checker.stop()


class TestHealthStats:
    """Test statistics and monitoring"""

    @pytest.mark.asyncio
    async def test_get_stats(self, health_checker):
        """Test getting health checker statistics"""

        async def check1():
            return True

        async def check2():
            return False

        await health_checker.start()

        health_checker.add_check(
            HealthCheck(name="check1", check_func=check1, interval=60, timeout=5)
        )
        health_checker.add_check(
            HealthCheck(name="check2", check_func=check2, interval=60, timeout=5)
        )

        await asyncio.sleep(0.2)

        stats = health_checker.get_stats()

        assert stats["total_checks"] == 2
        assert stats["overall_status"] == HealthStatus.UNHEALTHY.value
        assert "status_counts" in stats
        assert stats["status_counts"]["healthy"] == 1
        assert stats["status_counts"]["unhealthy"] == 1

        await health_checker.stop()


class TestHealthEdgeCases:
    """Test edge cases"""

    @pytest.mark.asyncio
    async def test_get_report_nonexistent(self, health_checker):
        """Test getting report for nonexistent check"""
        await health_checker.start()

        report = health_checker.get_report("nonexistent")
        assert report is None

        await health_checker.stop()

    @pytest.mark.asyncio
    async def test_remove_nonexistent_check(self, health_checker):
        """Test removing nonexistent check"""
        await health_checker.start()

        health_checker.remove_check("nonexistent")  # Should not error

        await health_checker.stop()

    @pytest.mark.asyncio
    async def test_overall_status_no_checks(self, health_checker):
        """Test overall status with no checks"""
        await health_checker.start()

        status = health_checker.get_overall_status()
        assert status == HealthStatus.UNKNOWN

        await health_checker.stop()

    @pytest.mark.asyncio
    async def test_check_interval(self, health_checker):
        """Test check execution interval"""
        check_count = 0

        async def counting_check():
            nonlocal check_count
            check_count += 1
            return True

        check = HealthCheck(
            name="counting", check_func=counting_check, interval=0.1, timeout=5
        )

        await health_checker.start()
        health_checker.add_check(check)

        # Wait for multiple intervals
        await asyncio.sleep(0.35)

        # Should have run ~3 times
        assert check_count >= 2

        await health_checker.stop()


class TestHealthDataClasses:
    """Test data classes"""

    def test_health_check_creation(self):
        """Test HealthCheck creation"""

        async def check():
            return True

        hc = HealthCheck(
            name="test", check_func=check, interval=60, timeout=5, failure_threshold=3
        )

        assert hc.name == "test"
        assert hc.interval == 60
        assert hc.timeout == 5
        assert hc.failure_threshold == 3

    def test_health_report_creation(self):
        """Test HealthReport creation"""
        now = datetime.now()
        report = HealthReport(
            status=HealthStatus.HEALTHY,
            last_check_at=now,
            last_success_at=now,
            failure_count=0,
            message="OK",
        )

        assert report.status == HealthStatus.HEALTHY
        assert report.failure_count == 0
        assert report.message == "OK"

    def test_health_status_enum(self):
        """Test HealthStatus enum"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"
