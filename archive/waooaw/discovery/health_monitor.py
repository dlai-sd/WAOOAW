"""
Health Monitoring for Agent Discovery

Provides health check system for monitoring agent availability and performance.
Tracks agent health status, response times, and failure rates.

Features:
- Periodic health checks with configurable intervals
- Response time tracking
- Failure threshold monitoring
- Integration with service registry
- Health status updates
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Awaitable, Callable, Dict, List, Optional

from waooaw.common.logging_framework import get_logger
from waooaw.discovery.service_registry import AgentStatus, ServiceRegistry


class HealthStatus(str, Enum):
    """Agent health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""

    agent_id: str
    status: HealthStatus
    response_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        """Check if result indicates healthy status"""
        return self.status == HealthStatus.HEALTHY


@dataclass
class HealthMetrics:
    """Health metrics for an agent"""

    agent_id: str
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    consecutive_failures: int = 0
    average_response_time_ms: float = 0.0
    last_check: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)"""
        if self.total_checks == 0:
            return 0.0
        return self.successful_checks / self.total_checks

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate (0.0 to 1.0)"""
        return 1.0 - self.success_rate

    def update_from_result(self, result: HealthCheckResult):
        """Update metrics from health check result"""
        self.total_checks += 1
        self.last_check = result.timestamp

        if result.is_healthy:
            self.successful_checks += 1
            self.consecutive_failures = 0
            self.last_success = result.timestamp
        else:
            self.failed_checks += 1
            self.consecutive_failures += 1
            self.last_failure = result.timestamp

        # Update average response time (exponential moving average)
        if self.average_response_time_ms == 0.0:
            self.average_response_time_ms = result.response_time_ms
        else:
            alpha = 0.3  # Smoothing factor
            self.average_response_time_ms = (
                alpha * result.response_time_ms + (1 - alpha) * self.average_response_time_ms
            )


class HealthMonitor:
    """
    Health monitor for tracking agent health
    
    Performs periodic health checks on registered agents and tracks
    their health status, response times, and failure rates.
    
    Example:
        >>> monitor = HealthMonitor(registry, check_interval=30)
        >>> await monitor.start()
        >>> 
        >>> # Get health status
        >>> status = await monitor.get_health_status("agent-1")
        >>> if status == HealthStatus.HEALTHY:
        ...     print("Agent is healthy")
    """

    def __init__(
        self,
        registry: ServiceRegistry,
        check_interval: int = 30,
        failure_threshold: int = 3,
        response_timeout: float = 5.0,
        degraded_threshold_ms: float = 1000.0,
    ):
        """
        Initialize health monitor
        
        Args:
            registry: Service registry to monitor
            check_interval: Seconds between health checks
            failure_threshold: Consecutive failures before marking unhealthy
            response_timeout: Timeout for health check requests (seconds)
            degraded_threshold_ms: Response time threshold for degraded status (ms)
        """
        self._registry = registry
        self._check_interval = check_interval
        self._failure_threshold = failure_threshold
        self._response_timeout = response_timeout
        self._degraded_threshold_ms = degraded_threshold_ms

        self._metrics: Dict[str, HealthMetrics] = {}
        self._health_checkers: Dict[str, Callable] = {}
        self._monitor_task: Optional[asyncio.Task] = None
        self._logger = get_logger("health-monitor")

    async def start(self):
        """Start health monitoring"""
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            self._logger.info(
                "health_monitor_started",
                extra={
                    "check_interval": self._check_interval,
                    "failure_threshold": self._failure_threshold,
                    "response_timeout": self._response_timeout,
                },
            )

    async def stop(self):
        """Stop health monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
            self._logger.info("health_monitor_stopped")

    def register_health_checker(
        self, agent_id: str, checker: Callable[[], Awaitable[bool]]
    ):
        """
        Register custom health checker for an agent
        
        Args:
            agent_id: Agent identifier
            checker: Async callable that returns bool (True = healthy)
        """
        self._health_checkers[agent_id] = checker
        self._logger.info("health_checker_registered", extra={"agent_id": agent_id})

    def unregister_health_checker(self, agent_id: str) -> bool:
        """
        Unregister health checker for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if checker was removed, False if not found
        """
        if agent_id in self._health_checkers:
            del self._health_checkers[agent_id]
            self._logger.info("health_checker_unregistered", extra={"agent_id": agent_id})
            return True
        return False

    async def check_health(self, agent_id: str) -> HealthCheckResult:
        """
        Perform health check on a specific agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            HealthCheckResult with status and metrics
        """
        start_time = time.time()

        try:
            # Get custom health checker if registered
            if agent_id in self._health_checkers:
                checker = self._health_checkers[agent_id]
                is_healthy = await asyncio.wait_for(
                    checker(), timeout=self._response_timeout
                )
            else:
                # Default health check (verify agent is registered)
                agent = await self._registry.get(agent_id)
                is_healthy = agent is not None and not agent.is_expired()

            response_time_ms = (time.time() - start_time) * 1000

            # Determine status based on response time and health
            if not is_healthy:
                status = HealthStatus.UNHEALTHY
            elif response_time_ms > self._degraded_threshold_ms:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY

            result = HealthCheckResult(
                agent_id=agent_id,
                status=status,
                response_time_ms=response_time_ms,
            )

        except asyncio.TimeoutError:
            response_time_ms = self._response_timeout * 1000
            result = HealthCheckResult(
                agent_id=agent_id,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                error="Health check timeout",
            )

        except Exception as error:
            response_time_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                agent_id=agent_id,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                error=str(error),
            )

        # Update metrics
        if agent_id not in self._metrics:
            self._metrics[agent_id] = HealthMetrics(agent_id=agent_id)
        self._metrics[agent_id].update_from_result(result)

        # Update registry status if needed
        await self._update_registry_status(agent_id, result)

        # Log result
        self._logger.info(
            "health_check_completed",
            extra={
                "agent_id": agent_id,
                "status": result.status.value,
                "response_time_ms": result.response_time_ms,
                "error": result.error,
            },
        )

        return result

    async def get_health_status(self, agent_id: str) -> HealthStatus:
        """
        Get current health status for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Current health status
        """
        metrics = self._metrics.get(agent_id)
        if metrics is None:
            return HealthStatus.UNKNOWN

        # Check consecutive failures
        if metrics.consecutive_failures >= self._failure_threshold:
            return HealthStatus.UNHEALTHY

        # Check recent checks
        if metrics.last_check is None:
            return HealthStatus.UNKNOWN

        # Check if last check was successful
        if metrics.last_success == metrics.last_check:
            if metrics.average_response_time_ms > self._degraded_threshold_ms:
                return HealthStatus.DEGRADED
            return HealthStatus.HEALTHY

        return HealthStatus.UNHEALTHY

    async def get_metrics(self, agent_id: str) -> Optional[HealthMetrics]:
        """
        Get health metrics for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            HealthMetrics if available, None otherwise
        """
        return self._metrics.get(agent_id)

    async def get_all_metrics(self) -> Dict[str, HealthMetrics]:
        """
        Get health metrics for all monitored agents
        
        Returns:
            Dictionary mapping agent_id to HealthMetrics
        """
        return dict(self._metrics)

    async def get_healthy_agents(self) -> List[str]:
        """
        Get list of healthy agent IDs
        
        Returns:
            List of agent IDs with healthy status
        """
        healthy = []
        for agent_id in self._metrics:
            status = await self.get_health_status(agent_id)
            if status == HealthStatus.HEALTHY:
                healthy.append(agent_id)
        return healthy

    async def get_unhealthy_agents(self) -> List[str]:
        """
        Get list of unhealthy agent IDs
        
        Returns:
            List of agent IDs with unhealthy status
        """
        unhealthy = []
        for agent_id in self._metrics:
            status = await self.get_health_status(agent_id)
            if status == HealthStatus.UNHEALTHY:
                unhealthy.append(agent_id)
        return unhealthy

    async def _update_registry_status(
        self, agent_id: str, result: HealthCheckResult
    ):
        """Update agent status in registry based on health check"""
        metrics = self._metrics.get(agent_id)
        if metrics is None:
            return

        # Determine registry status
        if metrics.consecutive_failures >= self._failure_threshold:
            await self._registry.update_status(agent_id, AgentStatus.OFFLINE)
        elif result.status == HealthStatus.DEGRADED:
            await self._registry.update_status(agent_id, AgentStatus.BUSY)
        elif result.status == HealthStatus.HEALTHY:
            await self._registry.update_status(agent_id, AgentStatus.ONLINE)

    async def _check_all_agents(self):
        """Perform health checks on all registered agents"""
        agents = await self._registry.list_all(include_expired=False)

        if not agents:
            return

        # Check all agents concurrently
        tasks = [self.check_health(agent.agent_id) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count results
        healthy_count = sum(
            1 for r in results if isinstance(r, HealthCheckResult) and r.is_healthy
        )
        total_count = len(results)

        self._logger.info(
            "health_check_cycle_completed",
            extra={
                "total_agents": total_count,
                "healthy_agents": healthy_count,
                "unhealthy_agents": total_count - healthy_count,
            },
        )

    async def _monitor_loop(self):
        """Background task to perform periodic health checks"""
        while True:
            try:
                await asyncio.sleep(self._check_interval)
                await self._check_all_agents()
            except asyncio.CancelledError:
                break
            except Exception as error:
                self._logger.error(
                    "monitor_loop_error",
                    extra={"error": str(error), "error_type": type(error).__name__},
                )
