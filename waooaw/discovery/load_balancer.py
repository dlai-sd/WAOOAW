"""
Load Balancing for Agent Discovery

Provides intelligent agent selection using various load balancing strategies.
Integrates with health monitoring to ensure requests go to healthy agents.

Strategies:
- Round-robin: Distribute evenly across agents
- Least-connections: Route to agent with fewest active connections
- Weighted: Priority-based selection
- Random: Random distribution

Features:
- Health-aware selection (only healthy agents)
- Capability-based filtering
- Connection tracking
- Performance metrics
"""

import logging
import random
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from waooaw.discovery.health_monitor import HealthMonitor, HealthStatus
from waooaw.discovery.service_registry import AgentRegistration, ServiceRegistry


class LoadBalancingStrategy(Enum):
    """Load balancing strategy types"""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    RANDOM = "random"


class LoadBalancerError(Exception):
    """Base exception for load balancer errors"""

    pass


class NoAvailableAgentsError(LoadBalancerError):
    """Raised when no agents are available for selection"""

    pass


@dataclass
class LoadBalancerMetrics:
    """Metrics for load balancer operations"""

    agent_id: str
    total_requests: int = 0
    active_connections: int = 0
    total_connections: int = 0
    failed_requests: int = 0
    last_selected: Optional[float] = None

    @property
    def success_rate(self) -> float:
        """Calculate request success rate"""
        if self.total_requests == 0:
            return 1.0
        return (self.total_requests - self.failed_requests) / self.total_requests


@dataclass
class SelectionResult:
    """Result of agent selection"""

    agent: AgentRegistration
    strategy: LoadBalancingStrategy
    metrics: LoadBalancerMetrics
    healthy: bool = True


class LoadBalancer:
    """
    Load balancer for intelligent agent selection
    
    Selects agents based on strategy, health status, and capabilities.
    Tracks connections and metrics for each agent.
    """

    def __init__(
        self,
        registry: ServiceRegistry,
        health_monitor: Optional[HealthMonitor] = None,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN,
        default_weight: int = 1,
    ):
        """
        Initialize load balancer
        
        Args:
            registry: Service registry with agent information
            health_monitor: Optional health monitor for health-aware selection
            strategy: Load balancing strategy to use
            default_weight: Default weight for weighted strategy
        """
        self._registry = registry
        self._health_monitor = health_monitor
        self._strategy = strategy
        self._default_weight = default_weight

        # Metrics tracking
        self._metrics: Dict[str, LoadBalancerMetrics] = {}
        self._weights: Dict[str, int] = {}

        # Round-robin state
        self._round_robin_index = 0

        self._logger = logging.getLogger(__name__)
        self._logger.info(
            f"Load balancer initialized: strategy={strategy.value}, default_weight={default_weight}"
        )

    def set_strategy(self, strategy: LoadBalancingStrategy):
        """
        Change load balancing strategy
        
        Args:
            strategy: New strategy to use
        """
        self._strategy = strategy
        self._logger.info(f"Strategy changed: {strategy.value}")

    def set_weight(self, agent_id: str, weight: int):
        """
        Set weight for an agent (used in weighted strategy)
        
        Args:
            agent_id: Agent identifier
            weight: Weight value (higher = more likely to be selected)
        """
        if weight < 0:
            raise ValueError("Weight must be non-negative")

        self._weights[agent_id] = weight
        self._logger.debug(f"Agent weight set: agent_id={agent_id}, weight={weight}")

    def get_weight(self, agent_id: str) -> int:
        """
        Get weight for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Weight value
        """
        return self._weights.get(agent_id, self._default_weight)

    async def select_agent(
        self,
        capability: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        require_healthy: bool = True,
    ) -> SelectionResult:
        """
        Select an agent using configured strategy
        
        Args:
            capability: Required capability name
            tags: Required tags (agent must have all)
            require_healthy: Only select healthy agents
            
        Returns:
            SelectionResult with selected agent
            
        Raises:
            NoAvailableAgentsError: No agents match criteria
        """
        # Get candidate agents
        candidates = await self._get_candidates(capability, tags, require_healthy)

        if not candidates:
            raise NoAvailableAgentsError(
                f"No available agents for capability={capability}, tags={tags}"
            )

        # Select based on strategy
        if self._strategy == LoadBalancingStrategy.ROUND_ROBIN:
            agent = self._select_round_robin(candidates)
        elif self._strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            agent = self._select_least_connections(candidates)
        elif self._strategy == LoadBalancingStrategy.WEIGHTED:
            agent = self._select_weighted(candidates)
        elif self._strategy == LoadBalancingStrategy.RANDOM:
            agent = self._select_random(candidates)
        else:
            raise ValueError(f"Unknown strategy: {self._strategy}")

        # Get or create metrics
        if agent.agent_id not in self._metrics:
            self._metrics[agent.agent_id] = LoadBalancerMetrics(agent_id=agent.agent_id)

        metrics = self._metrics[agent.agent_id]

        # Check health status
        healthy = True
        if self._health_monitor:
            health_status = await self._health_monitor.get_health_status(agent.agent_id)
            healthy = health_status == HealthStatus.HEALTHY

        self._logger.info(
            f"Agent selected: agent_id={agent.agent_id}, strategy={self._strategy.value}, healthy={healthy}"
        )

        return SelectionResult(
            agent=agent, strategy=self._strategy, metrics=metrics, healthy=healthy
        )

    async def acquire_connection(self, agent_id: str):
        """
        Mark connection as acquired for an agent
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id not in self._metrics:
            self._metrics[agent_id] = LoadBalancerMetrics(agent_id=agent_id)

        metrics = self._metrics[agent_id]
        metrics.active_connections += 1
        metrics.total_connections += 1
        metrics.total_requests += 1

        self._logger.debug(
            f"Connection acquired: agent_id={agent_id}, active={metrics.active_connections}"
        )

    async def release_connection(self, agent_id: str, failed: bool = False):
        """
        Release connection from an agent
        
        Args:
            agent_id: Agent identifier
            failed: Whether the request failed
        """
        if agent_id not in self._metrics:
            return

        metrics = self._metrics[agent_id]
        metrics.active_connections = max(0, metrics.active_connections - 1)

        if failed:
            metrics.failed_requests += 1

        self._logger.debug(
            f"Connection released: agent_id={agent_id}, active={metrics.active_connections}, failed={failed}"
        )

    async def get_metrics(self, agent_id: str) -> Optional[LoadBalancerMetrics]:
        """
        Get metrics for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            LoadBalancerMetrics or None if not found
        """
        return self._metrics.get(agent_id)

    async def get_all_metrics(self) -> Dict[str, LoadBalancerMetrics]:
        """
        Get metrics for all agents
        
        Returns:
            Dictionary mapping agent_id to metrics
        """
        return self._metrics.copy()

    async def reset_metrics(self, agent_id: Optional[str] = None):
        """
        Reset metrics for an agent or all agents
        
        Args:
            agent_id: Optional agent identifier (None = reset all)
        """
        if agent_id:
            if agent_id in self._metrics:
                self._metrics[agent_id] = LoadBalancerMetrics(agent_id=agent_id)
                self._logger.info(f"Metrics reset: agent_id={agent_id}")
        else:
            agent_ids = list(self._metrics.keys())
            self._metrics.clear()
            for aid in agent_ids:
                self._metrics[aid] = LoadBalancerMetrics(agent_id=aid)
            self._logger.info("All metrics reset")

    async def _get_candidates(
        self,
        capability: Optional[str],
        tags: Optional[Set[str]],
        require_healthy: bool,
    ) -> List[AgentRegistration]:
        """
        Get candidate agents matching criteria
        
        Args:
            capability: Required capability
            tags: Required tags
            require_healthy: Filter by health status
            
        Returns:
            List of matching agents
        """
        candidates = []

        # Filter by capability
        if capability:
            candidates = await self._registry.find_by_capability(capability)
        # Filter by tags
        elif tags:
            candidates = await self._registry.find_by_tags(tags)
        # Get all agents
        else:
            candidates = await self._registry.list_all()

        # Filter by health if monitor available
        if require_healthy and self._health_monitor:
            healthy_ids = set(await self._health_monitor.get_healthy_agents())
            candidates = [c for c in candidates if c.agent_id in healthy_ids]

        return candidates

    def _select_round_robin(self, candidates: List[AgentRegistration]) -> AgentRegistration:
        """Select agent using round-robin strategy"""
        if not candidates:
            raise NoAvailableAgentsError("No candidates available")

        agent = candidates[self._round_robin_index % len(candidates)]
        self._round_robin_index = (self._round_robin_index + 1) % len(candidates)
        return agent

    def _select_least_connections(
        self, candidates: List[AgentRegistration]
    ) -> AgentRegistration:
        """Select agent with fewest active connections"""
        if not candidates:
            raise NoAvailableAgentsError("No candidates available")

        # Find agent with minimum active connections
        min_connections = float("inf")
        selected = candidates[0]

        for agent in candidates:
            metrics = self._metrics.get(agent.agent_id)
            connections = metrics.active_connections if metrics else 0

            if connections < min_connections:
                min_connections = connections
                selected = agent

        return selected

    def _select_weighted(self, candidates: List[AgentRegistration]) -> AgentRegistration:
        """Select agent based on weights"""
        if not candidates:
            raise NoAvailableAgentsError("No candidates available")

        # Build weighted list
        weighted_agents = []
        for agent in candidates:
            weight = self.get_weight(agent.agent_id)
            weighted_agents.extend([agent] * weight)

        if not weighted_agents:
            # All weights are 0, fall back to random
            return random.choice(candidates)

        return random.choice(weighted_agents)

    def _select_random(self, candidates: List[AgentRegistration]) -> AgentRegistration:
        """Select agent randomly"""
        if not candidates:
            raise NoAvailableAgentsError("No candidates available")

        return random.choice(candidates)
