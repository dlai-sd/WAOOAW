"""
Health Checks - Story 5.5

System health monitoring and readiness probes.
Part of Epic 5: Common Components.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class HealthCheck:
    """Base health check."""
    
    def __init__(self, name: str, critical: bool = True):
        """
        Initialize health check.
        
        Args:
            name: Check name
            critical: Whether failure is critical
        """
        self.name = name
        self.critical = critical
    
    def check(self) -> HealthCheckResult:
        """
        Perform health check.
        
        Returns:
            Health check result
        """
        raise NotImplementedError


class FunctionHealthCheck(HealthCheck):
    """Health check from a function."""
    
    def __init__(
        self,
        name: str,
        check_func: Callable[[], bool],
        critical: bool = True
    ):
        """
        Initialize function-based health check.
        
        Args:
            name: Check name
            check_func: Function returning bool (True = healthy)
            critical: Whether failure is critical
        """
        super().__init__(name, critical)
        self.check_func = check_func
    
    def check(self) -> HealthCheckResult:
        """Perform check."""
        start = time.time()
        
        try:
            is_healthy = self.check_func()
            duration_ms = (time.time() - start) * 1000
            
            if is_healthy:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    duration_ms=duration_ms
                )
            else:
                status = HealthStatus.UNHEALTHY if self.critical else HealthStatus.DEGRADED
                return HealthCheckResult(
                    name=self.name,
                    status=status,
                    message="Check returned False",
                    duration_ms=duration_ms
                )
        
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            status = HealthStatus.UNHEALTHY if self.critical else HealthStatus.DEGRADED
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=str(e),
                duration_ms=duration_ms
            )


class HealthCheckManager:
    """
    Manages health checks for the application.
    
    Features:
    - Register health checks
    - Run all checks or specific checks
    - Aggregate health status
    - Liveness vs readiness probes
    - Dependency health monitoring
    """
    
    def __init__(self):
        """Initialize health check manager."""
        self.checks: Dict[str, HealthCheck] = {}
        self.last_results: Dict[str, HealthCheckResult] = {}
        self.check_count = 0
        
        logger.info("HealthCheckManager initialized")
    
    def register_check(self, check: HealthCheck) -> None:
        """
        Register a health check.
        
        Args:
            check: Health check instance
        """
        self.checks[check.name] = check
        logger.debug(f"Registered health check: {check.name}")
    
    def register_function(
        self,
        name: str,
        check_func: Callable[[], bool],
        critical: bool = True
    ) -> None:
        """
        Register a function-based health check.
        
        Args:
            name: Check name
            check_func: Function returning bool
            critical: Whether failure is critical
        """
        check = FunctionHealthCheck(name, check_func, critical)
        self.register_check(check)
    
    def run_check(self, name: str) -> HealthCheckResult:
        """
        Run a specific health check.
        
        Args:
            name: Check name
            
        Returns:
            Health check result
        """
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message="Check not found"
            )
        
        check = self.checks[name]
        result = check.check()
        
        self.last_results[name] = result
        self.check_count += 1
        
        return result
    
    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """
        Run all health checks.
        
        Returns:
            Dict mapping check name to result
        """
        results = {}
        
        for name in self.checks.keys():
            results[name] = self.run_check(name)
        
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """
        Get overall system health status.
        
        Returns:
            Aggregated health status
        """
        if not self.last_results:
            # No checks run yet
            return HealthStatus.UNHEALTHY
        
        # Check for any unhealthy critical checks
        for name, result in self.last_results.items():
            check = self.checks[name]
            
            if check.critical and result.status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY
        
        # Check for degraded
        has_degraded = any(
            r.status == HealthStatus.DEGRADED
            for r in self.last_results.values()
        )
        
        if has_degraded:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def liveness_probe(self) -> bool:
        """
        Liveness probe (is application running?).
        
        Returns:
            True if alive
        """
        # Simple check - if manager is initialized, we're alive
        return True
    
    def readiness_probe(self) -> bool:
        """
        Readiness probe (is application ready to serve traffic?).
        
        Returns:
            True if ready
        """
        # Run all checks
        self.run_all_checks()
        
        # Ready if overall status is healthy or degraded (not unhealthy)
        status = self.get_overall_status()
        return status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report.
        
        Returns:
            Health report
        """
        # Run all checks
        results = self.run_all_checks()
        
        # Aggregate
        overall_status = self.get_overall_status()
        
        # Build report
        checks_report = []
        for name, result in results.items():
            checks_report.append({
                "name": result.name,
                "status": result.status.value,
                "message": result.message,
                "duration_ms": round(result.duration_ms, 2),
                "critical": self.checks[name].critical
            })
        
        return {
            "status": overall_status.value,
            "checks": checks_report,
            "timestamp": time.time()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics."""
        return {
            "total_checks": len(self.checks),
            "checks_run": self.check_count,
            "last_status": self.get_overall_status().value if self.last_results else "unknown"
        }


# Global health check manager
_global_health: Optional[HealthCheckManager] = None


def init_health() -> HealthCheckManager:
    """
    Initialize global health check manager.
    
    Returns:
        HealthCheckManager instance
    """
    global _global_health
    _global_health = HealthCheckManager()
    return _global_health


def get_health() -> HealthCheckManager:
    """Get global health check manager."""
    if _global_health is None:
        return init_health()
    return _global_health


def register_health_check(
    name: str,
    check_func: Callable[[], bool],
    critical: bool = True
) -> None:
    """
    Convenience function to register health check.
    
    Args:
        name: Check name
        check_func: Check function
        critical: Whether critical
    """
    get_health().register_function(name, check_func, critical)
