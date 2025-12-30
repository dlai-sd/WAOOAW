"""
Tests for Service Registry

Tests agent registration, deregistration, lookup, heartbeat,
and automatic expiration.
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from waooaw.discovery.service_registry import (
    AgentCapability,
    AgentNotFoundError,
    AgentRegistration,
    AgentStatus,
    RegistrationError,
    ServiceRegistry,
)


@pytest.mark.asyncio
class TestAgentCapability:
    """Test AgentCapability dataclass"""

    def test_create_capability(self):
        """Should create capability with name and version"""
        cap = AgentCapability(name="process_data", version="1.0", description="Data processor")

        assert cap.name == "process_data"
        assert cap.version == "1.0"
        assert cap.description == "Data processor"
        assert cap.parameters == {}

    def test_capability_equality(self):
        """Should compare capabilities by name and version"""
        cap1 = AgentCapability("process", "1.0")
        cap2 = AgentCapability("process", "1.0")
        cap3 = AgentCapability("process", "2.0")

        assert cap1 == cap2
        assert cap1 != cap3

    def test_capability_hash(self):
        """Should support use in sets"""
        cap1 = AgentCapability("process", "1.0")
        cap2 = AgentCapability("process", "1.0")
        cap3 = AgentCapability("analyze", "1.0")

        capabilities = {cap1, cap2, cap3}
        assert len(capabilities) == 2  # cap1 and cap2 are same


@pytest.mark.asyncio
class TestAgentRegistration:
    """Test AgentRegistration dataclass"""

    def test_create_registration(self):
        """Should create registration with required fields"""
        caps = {AgentCapability("test", "1.0")}
        reg = AgentRegistration(
            agent_id="agent-1",
            name="Test Agent",
            host="localhost",
            port=8001,
            capabilities=caps,
        )

        assert reg.agent_id == "agent-1"
        assert reg.name == "Test Agent"
        assert reg.host == "localhost"
        assert reg.port == 8001
        assert reg.capabilities == caps
        assert reg.status == AgentStatus.ONLINE
        assert reg.ttl_seconds == 60

    def test_is_expired(self):
        """Should detect expired registrations"""
        reg = AgentRegistration(
            agent_id="agent-1",
            name="Test",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
            ttl_seconds=1,
        )

        # Initially not expired
        assert not reg.is_expired()

        # Set heartbeat to past
        reg.last_heartbeat = datetime.utcnow() - timedelta(seconds=2)
        assert reg.is_expired()

    async def test_update_heartbeat(self):
        """Should update heartbeat timestamp"""
        reg = AgentRegistration(
            agent_id="agent-1",
            name="Test",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
        )

        old_heartbeat = reg.last_heartbeat
        await asyncio.sleep(0.01)
        reg.update_heartbeat()

        assert reg.last_heartbeat > old_heartbeat

    def test_matches_capability(self):
        """Should match capability by name"""
        caps = {
            AgentCapability("process", "1.0"),
            AgentCapability("analyze", "1.0"),
        }
        reg = AgentRegistration(
            agent_id="agent-1",
            name="Test",
            host="localhost",
            port=8001,
            capabilities=caps,
        )

        assert reg.matches_capability("process")
        assert reg.matches_capability("analyze")
        assert not reg.matches_capability("unknown")

    def test_matches_tags(self):
        """Should match all required tags"""
        reg = AgentRegistration(
            agent_id="agent-1",
            name="Test",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
            tags={"ml", "python", "data"},
        )

        assert reg.matches_tags({"ml"})
        assert reg.matches_tags({"ml", "python"})
        assert reg.matches_tags({"ml", "python", "data"})
        assert not reg.matches_tags({"ml", "java"})  # java not in tags


@pytest.mark.asyncio
class TestServiceRegistry:
    """Test ServiceRegistry functionality"""

    async def test_create_registry(self):
        """Should create registry with cleanup interval"""
        registry = ServiceRegistry(cleanup_interval=30)
        assert registry._cleanup_interval == 30
        assert len(registry._registry) == 0

    async def test_register_agent(self):
        """Should register agent with all fields"""
        registry = ServiceRegistry()

        caps = {AgentCapability("process", "1.0")}
        tags = {"ml", "python"}
        metadata = {"version": "1.0.0"}

        reg = await registry.register(
            agent_id="agent-1",
            name="Test Agent",
            host="localhost",
            port=8001,
            capabilities=caps,
            status=AgentStatus.ONLINE,
            tags=tags,
            metadata=metadata,
            ttl_seconds=120,
        )

        assert reg.agent_id == "agent-1"
        assert reg.name == "Test Agent"
        assert reg.capabilities == caps
        assert reg.tags == tags
        assert reg.metadata == metadata
        assert reg.ttl_seconds == 120

    async def test_register_validation(self):
        """Should validate registration inputs"""
        registry = ServiceRegistry()
        caps = {AgentCapability("test", "1.0")}

        # Missing agent_id
        with pytest.raises(RegistrationError, match="agent_id is required"):
            await registry.register(
                agent_id="",
                name="Test",
                host="localhost",
                port=8001,
                capabilities=caps,
            )

        # Missing name
        with pytest.raises(RegistrationError, match="name is required"):
            await registry.register(
                agent_id="agent-1",
                name="",
                host="localhost",
                port=8001,
                capabilities=caps,
            )

        # Invalid port
        with pytest.raises(RegistrationError, match="Invalid port"):
            await registry.register(
                agent_id="agent-1",
                name="Test",
                host="localhost",
                port=0,
                capabilities=caps,
            )

        # No capabilities
        with pytest.raises(RegistrationError, match="At least one capability"):
            await registry.register(
                agent_id="agent-1",
                name="Test",
                host="localhost",
                port=8001,
                capabilities=set(),
            )

    async def test_deregister_agent(self):
        """Should deregister agent"""
        registry = ServiceRegistry()

        await registry.register(
            agent_id="agent-1",
            name="Test",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
        )

        # Deregister existing agent
        assert await registry.deregister("agent-1")
        assert await registry.get("agent-1") is None

        # Deregister non-existent agent
        assert not await registry.deregister("agent-2")

    async def test_heartbeat(self):
        """Should update agent heartbeat"""
        registry = ServiceRegistry()

        await registry.register(
            agent_id="agent-1",
            name="Test",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
        )

        old_heartbeat = registry._registry["agent-1"].last_heartbeat
        await asyncio.sleep(0.01)

        assert await registry.heartbeat("agent-1")
        new_heartbeat = registry._registry["agent-1"].last_heartbeat
        assert new_heartbeat > old_heartbeat

        # Heartbeat for non-existent agent
        assert not await registry.heartbeat("agent-2")

    async def test_update_status(self):
        """Should update agent status"""
        registry = ServiceRegistry()

        await registry.register(
            agent_id="agent-1",
            name="Test",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
            status=AgentStatus.ONLINE,
        )

        assert await registry.update_status("agent-1", AgentStatus.BUSY)
        reg = await registry.get("agent-1")
        assert reg.status == AgentStatus.BUSY

        # Update non-existent agent
        assert not await registry.update_status("agent-2", AgentStatus.OFFLINE)

    async def test_get_agent(self):
        """Should retrieve agent by ID"""
        registry = ServiceRegistry()

        await registry.register(
            agent_id="agent-1",
            name="Test",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
        )

        reg = await registry.get("agent-1")
        assert reg is not None
        assert reg.agent_id == "agent-1"

        # Get non-existent agent
        assert await registry.get("agent-2") is None

    async def test_find_by_capability(self):
        """Should find agents by capability"""
        registry = ServiceRegistry()

        await registry.register(
            agent_id="agent-1",
            name="Processor",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("process", "1.0")},
        )

        await registry.register(
            agent_id="agent-2",
            name="Analyzer",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("analyze", "1.0")},
        )

        await registry.register(
            agent_id="agent-3",
            name="Multi",
            host="localhost",
            port=8003,
            capabilities={
                AgentCapability("process", "1.0"),
                AgentCapability("analyze", "1.0"),
            },
        )

        # Find by capability
        processors = await registry.find_by_capability("process")
        assert len(processors) == 2
        assert any(a.agent_id == "agent-1" for a in processors)
        assert any(a.agent_id == "agent-3" for a in processors)

        analyzers = await registry.find_by_capability("analyze")
        assert len(analyzers) == 2

    async def test_find_by_capability_with_status(self):
        """Should filter by capability and status"""
        registry = ServiceRegistry()

        await registry.register(
            agent_id="agent-1",
            name="Online",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("process", "1.0")},
            status=AgentStatus.ONLINE,
        )

        await registry.register(
            agent_id="agent-2",
            name="Busy",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("process", "1.0")},
            status=AgentStatus.BUSY,
        )

        # Find online only
        online = await registry.find_by_capability("process", status=AgentStatus.ONLINE)
        assert len(online) == 1
        assert online[0].agent_id == "agent-1"

        # Find busy only
        busy = await registry.find_by_capability("process", status=AgentStatus.BUSY)
        assert len(busy) == 1
        assert busy[0].agent_id == "agent-2"

    async def test_find_by_tags(self):
        """Should find agents by tags"""
        registry = ServiceRegistry()

        await registry.register(
            agent_id="agent-1",
            name="ML Agent",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
            tags={"ml", "python"},
        )

        await registry.register(
            agent_id="agent-2",
            name="Data Agent",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("test", "1.0")},
            tags={"data", "python"},
        )

        # Find by single tag
        ml_agents = await registry.find_by_tags({"ml"})
        assert len(ml_agents) == 1
        assert ml_agents[0].agent_id == "agent-1"

        # Find by multiple tags (AND logic)
        python_agents = await registry.find_by_tags({"python"})
        assert len(python_agents) == 2

        ml_python = await registry.find_by_tags({"ml", "python"})
        assert len(ml_python) == 1
        assert ml_python[0].agent_id == "agent-1"

    async def test_list_all(self):
        """Should list all registered agents"""
        registry = ServiceRegistry()

        await registry.register(
            agent_id="agent-1",
            name="A",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
            status=AgentStatus.ONLINE,
        )

        await registry.register(
            agent_id="agent-2",
            name="B",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("test", "1.0")},
            status=AgentStatus.BUSY,
        )

        # List all
        all_agents = await registry.list_all()
        assert len(all_agents) == 2

        # List by status
        online = await registry.list_all(status=AgentStatus.ONLINE)
        assert len(online) == 1
        assert online[0].agent_id == "agent-1"

    async def test_count(self):
        """Should count registered agents"""
        registry = ServiceRegistry()

        assert await registry.count() == 0

        await registry.register(
            agent_id="agent-1",
            name="A",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
            status=AgentStatus.ONLINE,
        )

        await registry.register(
            agent_id="agent-2",
            name="B",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("test", "1.0")},
            status=AgentStatus.BUSY,
        )

        assert await registry.count() == 2
        assert await registry.count(status=AgentStatus.ONLINE) == 1
        assert await registry.count(status=AgentStatus.BUSY) == 1

    async def test_cleanup_expired(self):
        """Should remove expired registrations"""
        registry = ServiceRegistry()

        # Register with short TTL
        await registry.register(
            agent_id="agent-1",
            name="Short TTL",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
            ttl_seconds=1,
        )

        # Register with long TTL
        await registry.register(
            agent_id="agent-2",
            name="Long TTL",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("test", "1.0")},
            ttl_seconds=3600,
        )

        assert await registry.count() == 2

        # Wait for first to expire
        await asyncio.sleep(1.5)

        # Run cleanup
        removed = await registry._cleanup_expired()
        assert removed == 1
        assert await registry.count() == 1

        # Verify correct agent removed
        assert await registry.get("agent-1") is None
        assert await registry.get("agent-2") is not None

    async def test_find_excludes_expired(self):
        """Should exclude expired agents from find operations"""
        registry = ServiceRegistry()

        await registry.register(
            agent_id="agent-1",
            name="Expired",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("process", "1.0")},
            ttl_seconds=1,
        )

        await registry.register(
            agent_id="agent-2",
            name="Active",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("process", "1.0")},
            ttl_seconds=3600,
        )

        # Initially both found
        agents = await registry.find_by_capability("process")
        assert len(agents) == 2

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Only active agent found
        agents = await registry.find_by_capability("process")
        assert len(agents) == 1
        assert agents[0].agent_id == "agent-2"

    async def test_start_stop(self):
        """Should start and stop cleanup task"""
        registry = ServiceRegistry(cleanup_interval=1)

        await registry.start()
        assert registry._cleanup_task is not None
        assert not registry._cleanup_task.done()

        await registry.stop()
        # Task is set to None after stop
        assert registry._cleanup_task is None

    async def test_cleanup_loop(self):
        """Should automatically cleanup expired registrations"""
        registry = ServiceRegistry(cleanup_interval=1)
        await registry.start()

        # Register with short TTL
        await registry.register(
            agent_id="agent-1",
            name="Test",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
            ttl_seconds=1,
        )

        assert await registry.count() == 1

        # Wait for cleanup cycle
        await asyncio.sleep(2.5)

        # Agent should be removed
        assert await registry.count() == 0

        await registry.stop()
