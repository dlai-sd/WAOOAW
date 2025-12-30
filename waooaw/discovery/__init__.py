"""
Agent Discovery Module

Provides service registry, health monitoring, load balancing,
and circuit breaker patterns for agent discovery and selection.

Components:
- ServiceRegistry: Agent registration and lookup
- HealthMonitor: Health check system
- LoadBalancer: Agent selection strategies
- CircuitBreaker: Fault isolation
"""

from waooaw.discovery.service_registry import (
    ServiceRegistry,
    AgentRegistration,
    AgentCapability,
    AgentStatus,
    RegistrationError,
    AgentNotFoundError,
)
from waooaw.discovery.health_monitor import (
    HealthMonitor,
    HealthStatus,
    HealthCheckResult,
    HealthMetrics,
)
from waooaw.discovery.load_balancer import (
    LoadBalancer,
    LoadBalancingStrategy,
    LoadBalancerMetrics,
    SelectionResult,
    NoAvailableAgentsError,
)
from waooaw.discovery.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitMetrics,
    CircuitOpenError,
)

__all__ = [
    # Service Registry
    "ServiceRegistry",
    "AgentRegistration",
    "AgentCapability",
    "AgentStatus",
    "RegistrationError",
    "AgentNotFoundError",
    # Health Monitoring
    "HealthMonitor",
    "HealthStatus",
    "HealthCheckResult",
    "HealthMetrics",
    # Load Balancing
    "LoadBalancer",
    "LoadBalancingStrategy",
    "LoadBalancerMetrics",
    "SelectionResult",
    "NoAvailableAgentsError",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitState",
    "CircuitMetrics",
    "CircuitOpenError",
]

__version__ = "0.1.0"
