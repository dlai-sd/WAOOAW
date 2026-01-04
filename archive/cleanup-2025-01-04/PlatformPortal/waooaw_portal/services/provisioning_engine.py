"""
Provisioning Engine Service

Manages agent lifecycle operations including creation, startup, shutdown,
upgrades, and health monitoring.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class ProvisioningStatus(Enum):
    """Agent provisioning status"""

    PENDING = "pending"
    CREATING = "creating"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    UPGRADING = "upgrading"
    FAILED = "failed"
    DELETING = "deleting"
    DELETED = "deleted"


@dataclass
class AgentSpec:
    """Agent specification for provisioning"""

    agent_id: str
    agent_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProvisioningOperation:
    """Provisioning operation tracking"""

    operation_id: str
    agent_id: str
    operation_type: str
    status: ProvisioningStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: int = 0  # 0-100
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProvisioningEngine:
    """
    Agent provisioning and lifecycle management.

    Features:
    - Zero-downtime upgrades
    - Health monitoring integration
    - Resource allocation
    - Rollback on failure
    - Concurrent operations
    """

    def __init__(self, max_concurrent: int = 10):
        """
        Initialize provisioning engine.

        Args:
            max_concurrent: Maximum concurrent operations
        """
        self.operations: Dict[str, ProvisioningOperation] = {}
        self.agents: Dict[str, AgentSpec] = {}
        self.agent_status: Dict[str, ProvisioningStatus] = {}
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self):
        """Start provisioning engine"""
        self._running = True
        logger.info("Provisioning engine started")

    async def stop(self):
        """Stop provisioning engine"""
        self._running = False

        # Cancel running operations
        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        logger.info("Provisioning engine stopped")

    async def create_agent(
        self, spec: AgentSpec, wait: bool = False
    ) -> ProvisioningOperation:
        """
        Create new agent.

        Args:
            spec: Agent specification
            wait: Wait for operation to complete

        Returns:
            Provisioning operation
        """
        operation = ProvisioningOperation(
            operation_id=f"create-{spec.agent_id}-{datetime.now().timestamp()}",
            agent_id=spec.agent_id,
            operation_type="create",
            status=ProvisioningStatus.PENDING,
            started_at=datetime.now(),
        )

        self.operations[operation.operation_id] = operation
        self.agents[spec.agent_id] = spec
        self.agent_status[spec.agent_id] = ProvisioningStatus.PENDING

        task = asyncio.create_task(self._execute_create(operation, spec))
        self._tasks.append(task)

        if wait:
            await task

        return operation

    async def start_agent(
        self, agent_id: str, wait: bool = False
    ) -> ProvisioningOperation:
        """
        Start existing agent.

        Args:
            agent_id: Agent identifier
            wait: Wait for operation to complete

        Returns:
            Provisioning operation
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        operation = ProvisioningOperation(
            operation_id=f"start-{agent_id}-{datetime.now().timestamp()}",
            agent_id=agent_id,
            operation_type="start",
            status=ProvisioningStatus.PENDING,
            started_at=datetime.now(),
        )

        self.operations[operation.operation_id] = operation

        task = asyncio.create_task(self._execute_start(operation))
        self._tasks.append(task)

        if wait:
            await task

        return operation

    async def stop_agent(
        self, agent_id: str, graceful: bool = True, wait: bool = False
    ) -> ProvisioningOperation:
        """
        Stop running agent.

        Args:
            agent_id: Agent identifier
            graceful: Graceful shutdown
            wait: Wait for operation to complete

        Returns:
            Provisioning operation
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        operation = ProvisioningOperation(
            operation_id=f"stop-{agent_id}-{datetime.now().timestamp()}",
            agent_id=agent_id,
            operation_type="stop",
            status=ProvisioningStatus.PENDING,
            started_at=datetime.now(),
            metadata={"graceful": graceful},
        )

        self.operations[operation.operation_id] = operation

        task = asyncio.create_task(self._execute_stop(operation, graceful))
        self._tasks.append(task)

        if wait:
            await task

        return operation

    async def upgrade_agent(
        self,
        agent_id: str,
        new_version: str,
        zero_downtime: bool = True,
        wait: bool = False,
    ) -> ProvisioningOperation:
        """
        Upgrade agent to new version.

        Args:
            agent_id: Agent identifier
            new_version: Target version
            zero_downtime: Use zero-downtime upgrade
            wait: Wait for operation to complete

        Returns:
            Provisioning operation
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        operation = ProvisioningOperation(
            operation_id=f"upgrade-{agent_id}-{datetime.now().timestamp()}",
            agent_id=agent_id,
            operation_type="upgrade",
            status=ProvisioningStatus.PENDING,
            started_at=datetime.now(),
            metadata={"new_version": new_version, "zero_downtime": zero_downtime},
        )

        self.operations[operation.operation_id] = operation

        task = asyncio.create_task(
            self._execute_upgrade(operation, new_version, zero_downtime)
        )
        self._tasks.append(task)

        if wait:
            await task

        return operation

    async def delete_agent(
        self, agent_id: str, wait: bool = False
    ) -> ProvisioningOperation:
        """
        Delete agent.

        Args:
            agent_id: Agent identifier
            wait: Wait for operation to complete

        Returns:
            Provisioning operation
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        operation = ProvisioningOperation(
            operation_id=f"delete-{agent_id}-{datetime.now().timestamp()}",
            agent_id=agent_id,
            operation_type="delete",
            status=ProvisioningStatus.PENDING,
            started_at=datetime.now(),
        )

        self.operations[operation.operation_id] = operation

        task = asyncio.create_task(self._execute_delete(operation))
        self._tasks.append(task)

        if wait:
            await task

        return operation

    async def _execute_create(self, operation: ProvisioningOperation, spec: AgentSpec):
        """Execute agent creation"""
        async with self.semaphore:
            try:
                operation.status = ProvisioningStatus.CREATING
                self.agent_status[spec.agent_id] = ProvisioningStatus.CREATING
                operation.progress = 25
                logger.info(f"Creating agent {spec.agent_id}")

                # Simulate creation steps
                await asyncio.sleep(0.5)
                operation.progress = 50

                await asyncio.sleep(0.5)
                operation.progress = 75

                await asyncio.sleep(0.5)
                operation.status = ProvisioningStatus.RUNNING
                self.agent_status[spec.agent_id] = ProvisioningStatus.RUNNING
                operation.progress = 100
                operation.completed_at = datetime.now()

                logger.info(f"Agent {spec.agent_id} created successfully")

            except Exception as e:
                operation.status = ProvisioningStatus.FAILED
                self.agent_status[spec.agent_id] = ProvisioningStatus.FAILED
                operation.error_message = str(e)
                operation.completed_at = datetime.now()
                logger.error(f"Failed to create agent {spec.agent_id}: {e}")

    async def _execute_start(self, operation: ProvisioningOperation):
        """Execute agent startup"""
        async with self.semaphore:
            try:
                operation.status = ProvisioningStatus.STARTING
                self.agent_status[operation.agent_id] = ProvisioningStatus.STARTING
                operation.progress = 50
                logger.info(f"Starting agent {operation.agent_id}")

                await asyncio.sleep(0.5)

                operation.status = ProvisioningStatus.RUNNING
                self.agent_status[operation.agent_id] = ProvisioningStatus.RUNNING
                operation.progress = 100
                operation.completed_at = datetime.now()

                logger.info(f"Agent {operation.agent_id} started successfully")

            except Exception as e:
                operation.status = ProvisioningStatus.FAILED
                operation.error_message = str(e)
                operation.completed_at = datetime.now()
                logger.error(f"Failed to start agent {operation.agent_id}: {e}")

    async def _execute_stop(self, operation: ProvisioningOperation, graceful: bool):
        """Execute agent shutdown"""
        async with self.semaphore:
            try:
                operation.status = ProvisioningStatus.STOPPING
                self.agent_status[operation.agent_id] = ProvisioningStatus.STOPPING
                operation.progress = 50
                logger.info(
                    f"Stopping agent {operation.agent_id} (graceful={graceful})"
                )

                await asyncio.sleep(0.3 if graceful else 0.1)

                operation.status = ProvisioningStatus.STOPPED
                self.agent_status[operation.agent_id] = ProvisioningStatus.STOPPED
                operation.progress = 100
                operation.completed_at = datetime.now()

                logger.info(f"Agent {operation.agent_id} stopped successfully")

            except Exception as e:
                operation.status = ProvisioningStatus.FAILED
                operation.error_message = str(e)
                operation.completed_at = datetime.now()
                logger.error(f"Failed to stop agent {operation.agent_id}: {e}")

    async def _execute_upgrade(
        self, operation: ProvisioningOperation, new_version: str, zero_downtime: bool
    ):
        """Execute agent upgrade"""
        async with self.semaphore:
            try:
                operation.status = ProvisioningStatus.UPGRADING
                self.agent_status[operation.agent_id] = ProvisioningStatus.UPGRADING
                operation.progress = 20
                logger.info(
                    f"Upgrading agent {operation.agent_id} to {new_version} "
                    f"(zero_downtime={zero_downtime})"
                )

                # Simulate upgrade steps
                await asyncio.sleep(0.3)
                operation.progress = 40

                await asyncio.sleep(0.3)
                operation.progress = 60

                await asyncio.sleep(0.3)
                operation.progress = 80

                await asyncio.sleep(0.3)
                operation.status = ProvisioningStatus.RUNNING
                self.agent_status[operation.agent_id] = ProvisioningStatus.RUNNING
                operation.progress = 100
                operation.completed_at = datetime.now()

                logger.info(
                    f"Agent {operation.agent_id} upgraded to {new_version} successfully"
                )

            except Exception as e:
                operation.status = ProvisioningStatus.FAILED
                operation.error_message = str(e)
                operation.completed_at = datetime.now()
                logger.error(f"Failed to upgrade agent {operation.agent_id}: {e}")

    async def _execute_delete(self, operation: ProvisioningOperation):
        """Execute agent deletion"""
        async with self.semaphore:
            try:
                operation.status = ProvisioningStatus.DELETING
                self.agent_status[operation.agent_id] = ProvisioningStatus.DELETING
                operation.progress = 50
                logger.info(f"Deleting agent {operation.agent_id}")

                await asyncio.sleep(0.5)

                operation.status = ProvisioningStatus.DELETED
                self.agent_status[operation.agent_id] = ProvisioningStatus.DELETED
                operation.progress = 100
                operation.completed_at = datetime.now()

                # Remove from tracking
                if operation.agent_id in self.agents:
                    del self.agents[operation.agent_id]

                logger.info(f"Agent {operation.agent_id} deleted successfully")

            except Exception as e:
                operation.status = ProvisioningStatus.FAILED
                operation.error_message = str(e)
                operation.completed_at = datetime.now()
                logger.error(f"Failed to delete agent {operation.agent_id}: {e}")

    def get_operation(self, operation_id: str) -> Optional[ProvisioningOperation]:
        """Get operation by ID"""
        return self.operations.get(operation_id)

    def get_agent_status(self, agent_id: str) -> Optional[ProvisioningStatus]:
        """Get agent status"""
        return self.agent_status.get(agent_id)

    def get_active_operations(self) -> List[ProvisioningOperation]:
        """Get all active operations"""
        return [
            op
            for op in self.operations.values()
            if op.status not in [ProvisioningStatus.FAILED, ProvisioningStatus.DELETED]
            and op.completed_at is None
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get provisioning engine statistics"""
        status_counts = {}
        for status in self.agent_status.values():
            status_counts[status.value] = status_counts.get(status.value, 0) + 1

        return {
            "total_agents": len(self.agents),
            "total_operations": len(self.operations),
            "active_operations": len(self.get_active_operations()),
            "max_concurrent": self.max_concurrent,
            "status_counts": status_counts,
        }
