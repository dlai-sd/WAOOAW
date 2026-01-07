"""
Circuit Breaker for Agent Discovery

Implements circuit breaker pattern for fault isolation and automatic recovery.
Prevents cascading failures by stopping requests to failing agents.

States:
- CLOSED: Normal operation, requests flow through
- OPEN: Circuit tripped, requests blocked
- HALF_OPEN: Testing recovery, limited requests allowed

Features:
- Failure rate threshold monitoring
- Automatic state transitions
- Configurable recovery timeout
- Success threshold for recovery
- Per-agent circuit breakers
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

from waooaw.discovery.health_monitor import HealthMonitor


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit tripped, blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors"""

    pass


class CircuitOpenError(CircuitBreakerError):
    """Raised when circuit is open and request is blocked"""

    pass


@dataclass
class CircuitMetrics:
    """Metrics for circuit breaker operations"""

    agent_id: str
    state: CircuitState = CircuitState.CLOSED
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changed_at: float = field(default_factory=time.time)
    trip_count: int = 0

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests


class CircuitBreaker:
    """
    Circuit breaker for fault isolation
    
    Monitors request failures and opens circuit when threshold exceeded.
    Automatically attempts recovery after timeout period.
    """

    def __init__(
        self,
        failure_threshold: float = 0.5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        minimum_requests: int = 5,
        health_monitor: Optional[HealthMonitor] = None,
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Failure rate to trip circuit (0.0-1.0)
            success_threshold: Consecutive successes needed to close from half-open
            timeout: Seconds before attempting recovery
            minimum_requests: Minimum requests before checking failure rate
            health_monitor: Optional health monitor for integration
        """
        if not 0.0 <= failure_threshold <= 1.0:
            raise ValueError("failure_threshold must be between 0.0 and 1.0")
        if success_threshold < 1:
            raise ValueError("success_threshold must be at least 1")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if minimum_requests < 1:
            raise ValueError("minimum_requests must be at least 1")

        self._failure_threshold = failure_threshold
        self._success_threshold = success_threshold
        self._timeout = timeout
        self._minimum_requests = minimum_requests
        self._health_monitor = health_monitor

        # Per-agent circuit breakers
        self._circuits: Dict[str, CircuitMetrics] = {}

        self._logger = logging.getLogger(__name__)
        self._logger.info(
            f"Circuit breaker initialized: failure_threshold={failure_threshold}, "
            f"success_threshold={success_threshold}, timeout={timeout}, "
            f"minimum_requests={minimum_requests}"
        )

    def get_state(self, agent_id: str) -> CircuitState:
        """
        Get current circuit state for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Current circuit state
        """
        circuit = self._get_or_create_circuit(agent_id)
        self._check_state_transition(circuit)
        return circuit.state

    async def call(self, agent_id: str, func, *args, **kwargs):
        """
        Execute function through circuit breaker
        
        Args:
            agent_id: Agent identifier
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            CircuitOpenError: Circuit is open
        """
        circuit = self._get_or_create_circuit(agent_id)
        self._check_state_transition(circuit)

        if circuit.state == CircuitState.OPEN:
            self._logger.warning(f"Circuit open, blocking request: agent_id={agent_id}")
            raise CircuitOpenError(f"Circuit breaker is open for agent {agent_id}")

        # Execute function
        try:
            result = await func(*args, **kwargs) if hasattr(func, '__call__') else func
            await self.record_success(agent_id)
            return result
        except Exception as e:
            await self.record_failure(agent_id)
            raise

    async def record_success(self, agent_id: str):
        """
        Record successful request
        
        Args:
            agent_id: Agent identifier
        """
        circuit = self._get_or_create_circuit(agent_id)
        circuit.total_requests += 1
        circuit.successful_requests += 1
        circuit.consecutive_successes += 1
        circuit.consecutive_failures = 0
        circuit.last_success_time = time.time()

        # Check if we should close from half-open
        if circuit.state == CircuitState.HALF_OPEN:
            if circuit.consecutive_successes >= self._success_threshold:
                self._transition_to_closed(circuit)

        self._logger.debug(
            f"Success recorded: agent_id={agent_id}, state={circuit.state.value}, "
            f"consecutive={circuit.consecutive_successes}"
        )

    async def record_failure(self, agent_id: str):
        """
        Record failed request
        
        Args:
            agent_id: Agent identifier
        """
        circuit = self._get_or_create_circuit(agent_id)
        circuit.total_requests += 1
        circuit.failed_requests += 1
        circuit.consecutive_failures += 1
        circuit.consecutive_successes = 0
        circuit.last_failure_time = time.time()

        # Check if we should open circuit
        if circuit.state == CircuitState.CLOSED:
            if (
                circuit.total_requests >= self._minimum_requests
                and circuit.failure_rate >= self._failure_threshold
            ):
                self._transition_to_open(circuit)
        elif circuit.state == CircuitState.HALF_OPEN:
            # Any failure in half-open immediately reopens circuit
            self._transition_to_open(circuit)

        self._logger.debug(
            f"Failure recorded: agent_id={agent_id}, state={circuit.state.value}, "
            f"consecutive={circuit.consecutive_failures}, "
            f"failure_rate={circuit.failure_rate:.2f}"
        )

    async def reset(self, agent_id: str):
        """
        Reset circuit to closed state
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id in self._circuits:
            circuit = self._circuits[agent_id]
            old_state = circuit.state
            circuit.state = CircuitState.CLOSED
            circuit.consecutive_successes = 0
            circuit.consecutive_failures = 0
            circuit.state_changed_at = time.time()

            self._logger.info(
                f"Circuit reset: agent_id={agent_id}, old_state={old_state.value}"
            )

    async def get_metrics(self, agent_id: str) -> Optional[CircuitMetrics]:
        """
        Get metrics for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            CircuitMetrics or None if not found
        """
        return self._circuits.get(agent_id)

    async def get_all_metrics(self) -> Dict[str, CircuitMetrics]:
        """
        Get metrics for all agents
        
        Returns:
            Dictionary mapping agent_id to metrics
        """
        # Update all states before returning
        for circuit in self._circuits.values():
            self._check_state_transition(circuit)
        return self._circuits.copy()

    async def get_open_circuits(self) -> list[str]:
        """
        Get list of agent IDs with open circuits
        
        Returns:
            List of agent IDs
        """
        open_circuits = []
        for agent_id, circuit in self._circuits.items():
            self._check_state_transition(circuit)
            if circuit.state == CircuitState.OPEN:
                open_circuits.append(agent_id)
        return open_circuits

    async def get_half_open_circuits(self) -> list[str]:
        """
        Get list of agent IDs with half-open circuits
        
        Returns:
            List of agent IDs
        """
        half_open = []
        for agent_id, circuit in self._circuits.items():
            self._check_state_transition(circuit)
            if circuit.state == CircuitState.HALF_OPEN:
                half_open.append(agent_id)
        return half_open

    def _get_or_create_circuit(self, agent_id: str) -> CircuitMetrics:
        """Get or create circuit metrics for an agent"""
        if agent_id not in self._circuits:
            self._circuits[agent_id] = CircuitMetrics(agent_id=agent_id)
        return self._circuits[agent_id]

    def _check_state_transition(self, circuit: CircuitMetrics):
        """Check if circuit should transition to half-open"""
        if circuit.state == CircuitState.OPEN:
            elapsed = time.time() - circuit.state_changed_at
            if elapsed >= self._timeout:
                self._transition_to_half_open(circuit)

    def _transition_to_open(self, circuit: CircuitMetrics):
        """Transition circuit to open state"""
        circuit.state = CircuitState.OPEN
        circuit.state_changed_at = time.time()
        circuit.trip_count += 1

        self._logger.warning(
            f"Circuit opened: agent_id={circuit.agent_id}, "
            f"failure_rate={circuit.failure_rate:.2f}, "
            f"trip_count={circuit.trip_count}"
        )

    def _transition_to_half_open(self, circuit: CircuitMetrics):
        """Transition circuit to half-open state"""
        circuit.state = CircuitState.HALF_OPEN
        circuit.state_changed_at = time.time()
        circuit.consecutive_successes = 0
        circuit.consecutive_failures = 0

        self._logger.info(
            f"Circuit half-open: agent_id={circuit.agent_id}, attempting recovery"
        )

    def _transition_to_closed(self, circuit: CircuitMetrics):
        """Transition circuit to closed state"""
        circuit.state = CircuitState.CLOSED
        circuit.state_changed_at = time.time()
        circuit.consecutive_successes = 0
        circuit.consecutive_failures = 0

        self._logger.info(
            f"Circuit closed: agent_id={circuit.agent_id}, recovery successful"
        )
