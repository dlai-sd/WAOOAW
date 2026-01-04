"""
Unit tests for ProvisioningEngine service
"""

import pytest
import asyncio
from datetime import datetime
from waooaw_portal.services.provisioning_engine import (
    ProvisioningEngine,
    ProvisioningStatus,
    AgentSpec,
    ProvisioningOperation,
)


@pytest.fixture
def provisioning_engine():
    """Create provisioning engine instance"""
    return ProvisioningEngine(max_concurrent=5)


@pytest.fixture
def agent_spec():
    """Create test agent specification"""
    return AgentSpec(
        agent_id="test-agent-1",
        agent_type="sdk",
        config={"version": "1.0.0"},
        resources={"cpu": "1", "memory": "512Mi"},
        environment={"ENV": "test"},
    )


class TestProvisioningEngine:
    """Test ProvisioningEngine basic functionality"""

    @pytest.mark.asyncio
    async def test_start_stop(self, provisioning_engine):
        """Test provisioning engine start/stop"""
        await provisioning_engine.start()
        assert provisioning_engine._running is True

        await provisioning_engine.stop()
        assert provisioning_engine._running is False

    @pytest.mark.asyncio
    async def test_create_agent(self, provisioning_engine, agent_spec):
        """Test creating an agent"""
        await provisioning_engine.start()

        operation = await provisioning_engine.create_agent(agent_spec, wait=True)

        assert operation.agent_id == agent_spec.agent_id
        assert operation.operation_type == "create"
        assert operation.status == ProvisioningStatus.RUNNING
        assert operation.progress == 100
        assert operation.completed_at is not None

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_create_agent_without_wait(self, provisioning_engine, agent_spec):
        """Test creating agent without waiting"""
        await provisioning_engine.start()

        operation = await provisioning_engine.create_agent(agent_spec, wait=False)

        assert operation.status == ProvisioningStatus.PENDING
        assert operation.progress == 0

        # Wait for completion
        await asyncio.sleep(2)

        operation = provisioning_engine.get_operation(operation.operation_id)
        assert operation.status == ProvisioningStatus.RUNNING

        await provisioning_engine.stop()


class TestAgentLifecycle:
    """Test agent lifecycle operations"""

    @pytest.mark.asyncio
    async def test_start_agent(self, provisioning_engine, agent_spec):
        """Test starting an agent"""
        await provisioning_engine.start()

        # Create first
        await provisioning_engine.create_agent(agent_spec, wait=True)

        # Then start
        operation = await provisioning_engine.start_agent(
            agent_spec.agent_id, wait=True
        )

        assert operation.operation_type == "start"
        assert operation.status == ProvisioningStatus.RUNNING
        assert operation.completed_at is not None

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_stop_agent_graceful(self, provisioning_engine, agent_spec):
        """Test stopping agent gracefully"""
        await provisioning_engine.start()

        # Create and start
        await provisioning_engine.create_agent(agent_spec, wait=True)

        # Stop gracefully
        operation = await provisioning_engine.stop_agent(
            agent_spec.agent_id, graceful=True, wait=True
        )

        assert operation.operation_type == "stop"
        assert operation.status == ProvisioningStatus.STOPPED
        assert operation.metadata["graceful"] is True
        assert operation.completed_at is not None

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_stop_agent_forced(self, provisioning_engine, agent_spec):
        """Test force stopping agent"""
        await provisioning_engine.start()

        await provisioning_engine.create_agent(agent_spec, wait=True)

        # Force stop
        operation = await provisioning_engine.stop_agent(
            agent_spec.agent_id, graceful=False, wait=True
        )

        assert operation.status == ProvisioningStatus.STOPPED
        assert operation.metadata["graceful"] is False

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_upgrade_agent(self, provisioning_engine, agent_spec):
        """Test upgrading agent"""
        await provisioning_engine.start()

        await provisioning_engine.create_agent(agent_spec, wait=True)

        # Upgrade
        operation = await provisioning_engine.upgrade_agent(
            agent_spec.agent_id, new_version="2.0.0", zero_downtime=True, wait=True
        )

        assert operation.operation_type == "upgrade"
        assert operation.status == ProvisioningStatus.RUNNING
        assert operation.metadata["new_version"] == "2.0.0"
        assert operation.metadata["zero_downtime"] is True
        assert operation.completed_at is not None

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_upgrade_without_zero_downtime(self, provisioning_engine, agent_spec):
        """Test upgrading without zero-downtime"""
        await provisioning_engine.start()

        await provisioning_engine.create_agent(agent_spec, wait=True)

        operation = await provisioning_engine.upgrade_agent(
            agent_spec.agent_id, new_version="2.0.0", zero_downtime=False, wait=True
        )

        assert operation.status == ProvisioningStatus.RUNNING
        assert operation.metadata["zero_downtime"] is False

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_delete_agent(self, provisioning_engine, agent_spec):
        """Test deleting agent"""
        await provisioning_engine.start()

        await provisioning_engine.create_agent(agent_spec, wait=True)

        # Delete
        operation = await provisioning_engine.delete_agent(
            agent_spec.agent_id, wait=True
        )

        assert operation.operation_type == "delete"
        assert operation.status == ProvisioningStatus.DELETED
        assert operation.completed_at is not None

        # Agent should be removed
        assert agent_spec.agent_id not in provisioning_engine.agents

        await provisioning_engine.stop()


class TestProvisioningOperations:
    """Test provisioning operation tracking"""

    @pytest.mark.asyncio
    async def test_get_operation(self, provisioning_engine, agent_spec):
        """Test getting operation by ID"""
        await provisioning_engine.start()

        operation = await provisioning_engine.create_agent(agent_spec, wait=True)

        retrieved = provisioning_engine.get_operation(operation.operation_id)

        assert retrieved is not None
        assert retrieved.operation_id == operation.operation_id
        assert retrieved.agent_id == agent_spec.agent_id

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_get_agent_status(self, provisioning_engine, agent_spec):
        """Test getting agent status"""
        await provisioning_engine.start()

        await provisioning_engine.create_agent(agent_spec, wait=True)

        status = provisioning_engine.get_agent_status(agent_spec.agent_id)

        assert status == ProvisioningStatus.RUNNING

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_get_active_operations(self, provisioning_engine):
        """Test getting active operations"""
        await provisioning_engine.start()

        # Create multiple agents
        spec1 = AgentSpec(agent_id="agent-1", agent_type="sdk")
        spec2 = AgentSpec(agent_id="agent-2", agent_type="sdk")

        await provisioning_engine.create_agent(spec1, wait=False)
        await provisioning_engine.create_agent(spec2, wait=False)

        active = provisioning_engine.get_active_operations()

        # Should have at least the pending operations
        assert len(active) >= 2

        await provisioning_engine.stop()


class TestProvisioningConcurrency:
    """Test concurrent provisioning"""

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, provisioning_engine):
        """Test concurrent agent creation"""
        await provisioning_engine.start()

        # Create multiple agents concurrently
        specs = [AgentSpec(agent_id=f"agent-{i}", agent_type="sdk") for i in range(5)]

        operations = await asyncio.gather(
            *[provisioning_engine.create_agent(spec, wait=True) for spec in specs]
        )

        # All should complete successfully
        assert len(operations) == 5
        assert all(op.status == ProvisioningStatus.RUNNING for op in operations)

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_max_concurrent_limit(self, provisioning_engine):
        """Test max concurrent operations limit"""
        provisioning_engine.max_concurrent = 2
        provisioning_engine.semaphore = asyncio.Semaphore(2)

        await provisioning_engine.start()

        # Launch more than max
        specs = [AgentSpec(agent_id=f"agent-{i}", agent_type="sdk") for i in range(5)]

        start_time = datetime.now()

        await asyncio.gather(
            *[provisioning_engine.create_agent(spec, wait=True) for spec in specs]
        )

        # Should take longer due to queueing
        duration = (datetime.now() - start_time).total_seconds()
        assert duration > 1  # With 2 concurrent, 5 ops should take >1s

        await provisioning_engine.stop()


class TestProvisioningStats:
    """Test statistics and monitoring"""

    @pytest.mark.asyncio
    async def test_get_stats(self, provisioning_engine):
        """Test getting provisioning statistics"""
        await provisioning_engine.start()

        spec1 = AgentSpec(agent_id="agent-1", agent_type="sdk")
        spec2 = AgentSpec(agent_id="agent-2", agent_type="sdk")

        await provisioning_engine.create_agent(spec1, wait=True)
        await provisioning_engine.create_agent(spec2, wait=True)

        stats = provisioning_engine.get_stats()

        assert stats["total_agents"] == 2
        assert stats["total_operations"] >= 2
        assert stats["max_concurrent"] == 5
        assert "status_counts" in stats
        assert stats["status_counts"]["running"] == 2

        await provisioning_engine.stop()


class TestProvisioningEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_start_nonexistent_agent(self, provisioning_engine):
        """Test starting nonexistent agent"""
        await provisioning_engine.start()

        with pytest.raises(ValueError, match="not found"):
            await provisioning_engine.start_agent("nonexistent", wait=True)

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_stop_nonexistent_agent(self, provisioning_engine):
        """Test stopping nonexistent agent"""
        await provisioning_engine.start()

        with pytest.raises(ValueError, match="not found"):
            await provisioning_engine.stop_agent("nonexistent", wait=True)

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_upgrade_nonexistent_agent(self, provisioning_engine):
        """Test upgrading nonexistent agent"""
        await provisioning_engine.start()

        with pytest.raises(ValueError, match="not found"):
            await provisioning_engine.upgrade_agent("nonexistent", "2.0.0", wait=True)

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_agent(self, provisioning_engine):
        """Test deleting nonexistent agent"""
        await provisioning_engine.start()

        with pytest.raises(ValueError, match="not found"):
            await provisioning_engine.delete_agent("nonexistent", wait=True)

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_get_nonexistent_operation(self, provisioning_engine):
        """Test getting nonexistent operation"""
        await provisioning_engine.start()

        operation = provisioning_engine.get_operation("nonexistent")
        assert operation is None

        await provisioning_engine.stop()

    @pytest.mark.asyncio
    async def test_get_status_nonexistent_agent(self, provisioning_engine):
        """Test getting status of nonexistent agent"""
        await provisioning_engine.start()

        status = provisioning_engine.get_agent_status("nonexistent")
        assert status is None

        await provisioning_engine.stop()


class TestProvisioningDataClasses:
    """Test data classes"""

    def test_agent_spec_creation(self):
        """Test AgentSpec creation"""
        spec = AgentSpec(
            agent_id="test-agent",
            agent_type="sdk",
            config={"key": "value"},
            resources={"cpu": "1"},
            environment={"VAR": "value"},
        )

        assert spec.agent_id == "test-agent"
        assert spec.agent_type == "sdk"
        assert spec.config["key"] == "value"
        assert spec.resources["cpu"] == "1"
        assert spec.environment["VAR"] == "value"

    def test_provisioning_operation_creation(self):
        """Test ProvisioningOperation creation"""
        now = datetime.now()
        operation = ProvisioningOperation(
            operation_id="op-123",
            agent_id="agent-1",
            operation_type="create",
            status=ProvisioningStatus.RUNNING,
            started_at=now,
            progress=50,
        )

        assert operation.operation_id == "op-123"
        assert operation.agent_id == "agent-1"
        assert operation.operation_type == "create"
        assert operation.status == ProvisioningStatus.RUNNING
        assert operation.progress == 50

    def test_provisioning_status_enum(self):
        """Test ProvisioningStatus enum"""
        assert ProvisioningStatus.PENDING.value == "pending"
        assert ProvisioningStatus.CREATING.value == "creating"
        assert ProvisioningStatus.RUNNING.value == "running"
        assert ProvisioningStatus.STOPPED.value == "stopped"
        assert ProvisioningStatus.FAILED.value == "failed"
        assert ProvisioningStatus.DELETED.value == "deleted"
