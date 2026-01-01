"""
Health Checker Service

Monitors health status of agents, services, and system components.
Performs periodic health checks and generates health reports.
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check configuration"""

    name: str
    check_func: Callable[[], bool]
    interval_seconds: int = 60
    timeout_seconds: int = 5
    failure_threshold: int = 3


@dataclass
class HealthReport:
    """Health check result"""

    name: str
    status: HealthStatus
    last_check: datetime
    consecutive_failures: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """
    Monitors system health with periodic checks.

    Features:
    - Configurable health checks
    - Failure threshold tracking
    - Async health check execution
    - Health status aggregation
    - Historical health data
    """

    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.reports: Dict[str, HealthReport] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._running = False

    async def start(self):
        """Start all health check tasks"""
        self._running = True
        for name in self.checks:
            self._tasks[name] = asyncio.create_task(self._run_check_loop(name))
        logger.info(f"Health checker started with {len(self.checks)} checks")

    async def stop(self):
        """Stop all health check tasks"""
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()
        logger.info("Health checker stopped")

    def add_check(self, check: HealthCheck):
        """
        Add a health check.

        Args:
            check: HealthCheck configuration
        """
        self.checks[check.name] = check
        self.reports[check.name] = HealthReport(
            name=check.name, status=HealthStatus.UNKNOWN, last_check=datetime.now()
        )

        # Start check if already running
        if self._running and check.name not in self._tasks:
            self._tasks[check.name] = asyncio.create_task(
                self._run_check_loop(check.name)
            )

        logger.info(f"Added health check: {check.name}")

    def remove_check(self, name: str):
        """Remove a health check"""
        if name in self.checks:
            del self.checks[name]

        if name in self.reports:
            del self.reports[name]

        if name in self._tasks:
            self._tasks[name].cancel()
            del self._tasks[name]

        logger.info(f"Removed health check: {name}")

    async def _run_check_loop(self, name: str):
        """Run health check loop for a specific check"""
        check = self.checks[name]

        while self._running:
            try:
                await self._execute_check(name)
                await asyncio.sleep(check.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop {name}: {e}")
                await asyncio.sleep(check.interval_seconds)

    async def _execute_check(self, name: str):
        """Execute a single health check"""
        check = self.checks[name]
        report = self.reports[name]

        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(check.check_func),
                timeout=check.timeout_seconds,
            )

            now = datetime.now()
            report.last_check = now

            if result:
                # Health check passed
                report.status = HealthStatus.HEALTHY
                report.consecutive_failures = 0
                report.last_success = now
                report.message = "Check passed"
            else:
                # Health check failed
                report.consecutive_failures += 1

                if report.consecutive_failures >= check.failure_threshold:
                    report.status = HealthStatus.UNHEALTHY
                else:
                    report.status = HealthStatus.DEGRADED

                report.last_failure = now
                report.message = (
                    f"Check failed ({report.consecutive_failures} consecutive)"
                )

            logger.debug(f"Health check {name}: {report.status.value}")

        except asyncio.TimeoutError:
            report.consecutive_failures += 1
            report.status = HealthStatus.UNHEALTHY
            report.last_check = datetime.now()
            report.last_failure = datetime.now()
            report.message = f"Check timed out after {check.timeout_seconds}s"
            logger.warning(f"Health check {name} timed out")

        except Exception as e:
            report.consecutive_failures += 1
            report.status = HealthStatus.UNHEALTHY
            report.last_check = datetime.now()
            report.last_failure = datetime.now()
            report.message = f"Check error: {str(e)}"
            logger.error(f"Health check {name} failed: {e}")

    def get_report(self, name: str) -> Optional[HealthReport]:
        """Get health report for a specific check"""
        return self.reports.get(name)

    def get_all_reports(self) -> Dict[str, HealthReport]:
        """Get all health reports"""
        return self.reports.copy()

    def get_overall_status(self) -> HealthStatus:
        """
        Get overall system health status.

        Returns worst status across all checks.
        """
        if not self.reports:
            return HealthStatus.UNKNOWN

        statuses = [r.status for r in self.reports.values()]

        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

    def get_stats(self) -> Dict[str, Any]:
        """Get health checker statistics"""
        status_counts = {status: 0 for status in HealthStatus}
        for report in self.reports.values():
            status_counts[report.status] += 1

        return {
            "total_checks": len(self.checks),
            "running": self._running,
            "overall_status": self.get_overall_status().value,
            "status_counts": {k.value: v for k, v in status_counts.items()},
        }
