"""
Service Registry for Agent Discovery

Provides agent registration, deregistration, and lookup capabilities.
Maintains registry of available agents with their metadata, capabilities,
and connection information.

Features:
- Agent registration with metadata
- Capability-based lookup
- Tag-based filtering
- TTL-based expiration
- Health status tracking
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4

from waooaw.common.logging_framework import get_logger


class AgentStatus(str, Enum):
    """Agent availability status"""

    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    MAINTENANCE = "maintenance"


class RegistrationError(Exception):
    """Raised when agent registration fails"""

    pass


class AgentNotFoundError(Exception):
    """Raised when agent is not found in registry"""

    pass


@dataclass
class AgentCapability:
    """Agent capability definition"""

    name: str
    version: str
    description: str = ""
    parameters: Dict[str, str] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.name, self.version))

    def __eq__(self, other):
        if not isinstance(other, AgentCapability):
            return False
        return self.name == other.name and self.version == other.version


@dataclass
class AgentRegistration:
    """Agent registration information"""

    agent_id: str
    name: str
    host: str
    port: int
    capabilities: Set[AgentCapability]
    status: AgentStatus = AgentStatus.ONLINE
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: int = 60  # Time-to-live for registration

    def is_expired(self) -> bool:
        """Check if registration has expired based on TTL"""
        expiration = self.last_heartbeat + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiration

    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow()

    def matches_capability(self, capability_name: str) -> bool:
        """Check if agent has a specific capability"""
        return any(cap.name == capability_name for cap in self.capabilities)

    def matches_tags(self, tags: Set[str]) -> bool:
        """Check if agent has all specified tags"""
        return tags.issubset(self.tags)


class ServiceRegistry:
    """
    Service registry for agent discovery
    
    Maintains registry of available agents with their capabilities,
    connection information, and health status. Supports registration,
    deregistration, lookup, and automatic expiration.
    
    Example:
        >>> registry = ServiceRegistry()
        >>> await registry.register(
        ...     agent_id="agent-1",
        ...     name="Data Processor",
        ...     host="localhost",
        ...     port=8001,
        ...     capabilities={AgentCapability("process_data", "1.0")},
        ...     tags={"ml", "python"}
        ... )
        >>> agents = await registry.find_by_capability("process_data")
    """

    def __init__(self, cleanup_interval: int = 30):
        """
        Initialize service registry
        
        Args:
            cleanup_interval: Seconds between cleanup of expired registrations
        """
        self._registry: Dict[str, AgentRegistration] = {}
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._logger = get_logger("service-registry")

    async def start(self):
        """Start registry cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._logger.info("registry_started", extra={"cleanup_interval": self._cleanup_interval})

    async def stop(self):
        """Stop registry cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            self._logger.info("registry_stopped")

    async def register(
        self,
        agent_id: str,
        name: str,
        host: str,
        port: int,
        capabilities: Set[AgentCapability],
        status: AgentStatus = AgentStatus.ONLINE,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, any]] = None,
        ttl_seconds: int = 60,
    ) -> AgentRegistration:
        """
        Register an agent with the registry
        
        Args:
            agent_id: Unique agent identifier
            name: Human-readable agent name
            host: Agent host address
            port: Agent port number
            capabilities: Set of agent capabilities
            status: Initial agent status
            tags: Optional tags for filtering
            metadata: Optional metadata
            ttl_seconds: Time-to-live for registration
            
        Returns:
            AgentRegistration object
            
        Raises:
            RegistrationError: If registration fails validation
        """
        # Validate inputs
        if not agent_id:
            raise RegistrationError("agent_id is required")
        if not name:
            raise RegistrationError("name is required")
        if not host:
            raise RegistrationError("host is required")
        if port <= 0 or port > 65535:
            raise RegistrationError(f"Invalid port: {port}")
        if not capabilities:
            raise RegistrationError("At least one capability is required")

        # Create registration
        registration = AgentRegistration(
            agent_id=agent_id,
            name=name,
            host=host,
            port=port,
            capabilities=capabilities,
            status=status,
            tags=tags or set(),
            metadata=metadata or {},
            ttl_seconds=ttl_seconds,
        )

        # Store in registry
        self._registry[agent_id] = registration

        self._logger.info(
            "agent_registered",
            extra={
                "agent_id": agent_id,
                "name": name,
                "host": host,
                "port": port,
                "capabilities": len(capabilities),
                "tags": list(tags or []),
                "ttl": ttl_seconds,
            },
        )

        return registration

    async def deregister(self, agent_id: str) -> bool:
        """
        Deregister an agent from the registry
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if agent was deregistered, False if not found
        """
        if agent_id in self._registry:
            del self._registry[agent_id]
            self._logger.info("agent_deregistered", extra={"agent_id": agent_id})
            return True
        return False

    async def heartbeat(self, agent_id: str) -> bool:
        """
        Update agent heartbeat to keep registration alive
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if heartbeat updated, False if agent not found
        """
        if agent_id in self._registry:
            self._registry[agent_id].update_heartbeat()
            self._logger.debug(
                "agent_heartbeat",
                extra={
                    "agent_id": agent_id,
                    "last_heartbeat": self._registry[agent_id].last_heartbeat.isoformat(),
                },
            )
            return True
        return False

    async def update_status(self, agent_id: str, status: AgentStatus) -> bool:
        """
        Update agent status
        
        Args:
            agent_id: Agent identifier
            status: New agent status
            
        Returns:
            True if status updated, False if agent not found
        """
        if agent_id in self._registry:
            old_status = self._registry[agent_id].status
            self._registry[agent_id].status = status
            self._logger.info(
                "agent_status_updated",
                extra={"agent_id": agent_id, "old_status": old_status.value, "new_status": status.value},
            )
            return True
        return False

    async def get(self, agent_id: str) -> Optional[AgentRegistration]:
        """
        Get agent registration by ID
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            AgentRegistration if found, None otherwise
        """
        return self._registry.get(agent_id)

    async def find_by_capability(
        self, capability_name: str, status: Optional[AgentStatus] = None
    ) -> List[AgentRegistration]:
        """
        Find agents by capability name
        
        Args:
            capability_name: Capability to search for
            status: Optional status filter
            
        Returns:
            List of matching agent registrations
        """
        results = []
        for registration in self._registry.values():
            # Skip expired registrations
            if registration.is_expired():
                continue

            # Check status filter
            if status and registration.status != status:
                continue

            # Check capability
            if registration.matches_capability(capability_name):
                results.append(registration)

        return results

    async def find_by_tags(
        self, tags: Set[str], status: Optional[AgentStatus] = None
    ) -> List[AgentRegistration]:
        """
        Find agents by tags (agent must have ALL specified tags)
        
        Args:
            tags: Tags to search for
            status: Optional status filter
            
        Returns:
            List of matching agent registrations
        """
        results = []
        for registration in self._registry.values():
            # Skip expired registrations
            if registration.is_expired():
                continue

            # Check status filter
            if status and registration.status != status:
                continue

            # Check tags
            if registration.matches_tags(tags):
                results.append(registration)

        return results

    async def list_all(
        self, status: Optional[AgentStatus] = None, include_expired: bool = False
    ) -> List[AgentRegistration]:
        """
        List all registered agents
        
        Args:
            status: Optional status filter
            include_expired: Whether to include expired registrations
            
        Returns:
            List of agent registrations
        """
        results = []
        for registration in self._registry.values():
            # Check expiration
            if not include_expired and registration.is_expired():
                continue

            # Check status filter
            if status and registration.status != status:
                continue

            results.append(registration)

        return results

    async def count(self, status: Optional[AgentStatus] = None) -> int:
        """
        Count registered agents
        
        Args:
            status: Optional status filter
            
        Returns:
            Number of matching agents
        """
        agents = await self.list_all(status=status)
        return len(agents)

    async def _cleanup_expired(self) -> int:
        """
        Remove expired registrations from registry
        
        Returns:
            Number of registrations removed
        """
        expired_ids = [
            agent_id for agent_id, reg in self._registry.items() if reg.is_expired()
        ]

        for agent_id in expired_ids:
            del self._registry[agent_id]
            self._logger.info("agent_expired", extra={"agent_id": agent_id})

        if expired_ids:
            self._logger.info(
                "cleanup_completed", extra={"removed_count": len(expired_ids)}
            )

        return len(expired_ids)

    async def _cleanup_loop(self):
        """Background task to cleanup expired registrations"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                removed = await self._cleanup_expired()
                if removed > 0:
                    self._logger.debug(
                        "cleanup_cycle",
                        extra={"removed": removed, "remaining": len(self._registry)},
                    )
            except asyncio.CancelledError:
                break
            except Exception as error:
                self._logger.error(
                    "cleanup_error", extra={"error": str(error), "error_type": type(error).__name__}
                )
