"""
Test Base CoE Template

Story: #80 Tests & Docs (2 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE
"""

import pytest
import asyncio
from datetime import datetime

from waooaw.factory.templates.base_coe_template import BasePlatformCoE
from waooaw.factory.interfaces.coe_interface import (
    WakeEvent,
    DecisionRequest,
    ActionContext,
    TaskDefinition,
    EventType,
    ActionStatus
)


class TestAgent(BasePlatformCoE):
    """Test agent for unit tests"""
    
    def __init__(self):
        super().__init__(
            agent_id="TestAgent",
            did="did:waooaw:test",
            capabilities={"test": ["can:test"]},
            constraints=[]
        )
    
    async def should_wake(self, event: WakeEvent) -> bool:
        return event.pattern_matches("test.*")
    
    async def make_decision(self, request: DecisionRequest) -> dict:
        return {"decision": "approve", "reason": "test"}
    
    async def act(self, context: ActionContext) -> dict:
        return {"status": ActionStatus.COMPLETED, "result": "test"}
    
    async def execute_task(self, task: TaskDefinition) -> dict:
        return {"task_id": task.task_id, "status": "completed"}


@pytest.fixture
def test_agent():
    """Create test agent"""
    return TestAgent()


@pytest.fixture
def wake_event():
    """Create test wake event"""
    return WakeEvent(
        event_id="test_001",
        event_type=EventType.CUSTOM,
        source="test",
        timestamp=datetime.now(),
        data={},
        pattern="test.event"
    )


@pytest.fixture
def decision_request():
    """Create test decision request"""
    return DecisionRequest(
        decision_type="test_decision",
        context={"test": True},
        constraints=[],
        similar_cases=[]
    )


@pytest.fixture
def action_context():
    """Create test action context"""
    return ActionContext(
        action_type="test_action",
        parameters={"test": True},
        timeout=30
    )


@pytest.fixture
def task_definition():
    """Create test task"""
    return TaskDefinition(
        task_id="task_001",
        task_type="test_task",
        description="Test task",
        parameters={"test": True},
        priority=1
    )


class TestBasePlatformCoE:
    """Test BasePlatformCoE template"""
    
    def test_initialization(self, test_agent):
        """Test agent initialization"""
        assert test_agent.agent_id == "TestAgent"
        assert test_agent.did == "did:waooaw:test"
        assert "test" in test_agent.capabilities
        assert test_agent.state == "active"
    
    @pytest.mark.asyncio
    async def test_should_wake(self, test_agent, wake_event):
        """Test wake protocol"""
        result = await test_agent.should_wake(wake_event)
        assert result is True
        
        # Test non-matching pattern
        wake_event.pattern = "other.event"
        result = await test_agent.should_wake(wake_event)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_make_decision(self, test_agent, decision_request):
        """Test decision framework"""
        result = await test_agent.make_decision(decision_request)
        assert "decision" in result
        assert result["decision"] == "approve"
    
    @pytest.mark.asyncio
    async def test_act(self, test_agent, action_context):
        """Test action execution"""
        result = await test_agent.act(action_context)
        assert "status" in result
        assert result["status"] == ActionStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_execute_task(self, test_agent, task_definition):
        """Test task execution"""
        result = await test_agent.execute_task(task_definition)
        assert result["task_id"] == "task_001"
        assert result["status"] == "completed"
    
    def test_capabilities(self, test_agent):
        """Test capability checks"""
        assert test_agent.has_capability("can:test")
        assert not test_agent.has_capability("can:other")
    
    def test_state_management(self, test_agent):
        """Test state transitions"""
        assert test_agent.state == "active"
        
        test_agent.set_state("suspended")
        assert test_agent.state == "suspended"
        
        test_agent.set_state("active")
        assert test_agent.state == "active"
