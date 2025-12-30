"""
CoE Interface - Type definitions and protocols for Platform CoE agents

This module defines the standard interface that all Platform CoE agents
must implement. It provides type hints, data classes, and protocols for:
- Wake events and triggers
- Decision requests and responses
- Action execution contexts
- Task definitions

Story: #75 CoE Interface (2 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE
"""

from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class EventType(Enum):
    """Event types for wake triggers"""
    DOMAIN_EVENT = "domain"
    AGENT_EVENT = "agent"
    SYSTEM_EVENT = "system"
    CUSTOMER_EVENT = "customer"
    PLATFORM_BROADCAST = "platform.broadcast"
    CRON_TRIGGER = "cron"
    API_TRIGGER = "api"
    MANUAL_TRIGGER = "manual"


class DecisionMethod(Enum):
    """Methods used for decision making"""
    DETERMINISTIC_RULE = "deterministic_rule"
    DECISION_CACHE = "decision_cache"
    VECTOR_MEMORY = "vector_memory"
    LLM_REASONING = "llm_reasoning"
    HUMAN_OVERRIDE = "human_override"


class ActionStatus(Enum):
    """Status of action execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class WakeEvent:
    """
    Event that triggers agent wake-up.
    
    Attributes:
        topic: Event topic (e.g., "domain.model.created")
        event_type: Type of event
        data: Event payload
        timestamp: Event creation time
        source: Agent or system that created the event
        correlation_id: ID to correlate related events
        priority: Event priority (0-10, 10 highest)
    """
    topic: str
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    priority: int = 5
    
    def matches_pattern(self, pattern: str) -> bool:
        """
        Check if event topic matches a pattern.
        
        Supports wildcards:
        - * matches single segment (domain.*.created)
        - ** matches multiple segments (domain.**)
        
        Args:
            pattern: Topic pattern with wildcards
        
        Returns:
            bool: True if topic matches pattern
        """
        import re
        # Convert wildcard pattern to regex
        regex_pattern = pattern.replace(".", r"\.").replace("*", r"[^.]+")
        return bool(re.match(f"^{regex_pattern}$", self.topic))


@dataclass
class DecisionRequest:
    """
    Request for agent to make a decision.
    
    Attributes:
        request_type: Type of decision needed
        context: Decision context and input data
        requester: Agent or system requesting decision
        deadline: When decision is needed by
        constraints: Constraints on decision
        similar_cases: Past similar decisions (optional)
    """
    request_type: str
    context: Dict[str, Any]
    requester: Optional[str] = None
    deadline: Optional[datetime] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    similar_cases: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ActionContext:
    """
    Context for action execution.
    
    Attributes:
        action_type: Type of action to execute
        parameters: Action parameters
        decision: Decision that triggered this action
        environment: Execution environment details
        timeout_seconds: Maximum execution time
        retry_policy: Retry configuration
    """
    action_type: str
    parameters: Dict[str, Any]
    decision: Optional[Any] = None  # Decision from make_decision()
    environment: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 300
    retry_policy: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDefinition:
    """
    Definition of a task for agent to execute.
    
    Attributes:
        task_id: Unique task identifier
        task_type: Type of task
        data: Task data and parameters
        priority: Task priority (0-10, 10 highest)
        dependencies: Task IDs this task depends on
        deadline: When task must complete by
        created_at: Task creation time
        assigned_to: Agent assigned to task
    """
    task_id: str
    task_type: str
    data: Dict[str, Any]
    priority: int = 5
    dependencies: List[str] = field(default_factory=list)
    deadline: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None


# =============================================================================
# PROTOCOLS
# =============================================================================

class CoEInterface(Protocol):
    """
    Protocol defining the standard interface for Platform CoE agents.
    
    All Platform CoE agents must implement these methods:
    - should_wake(): Determine if agent should activate for an event
    - make_decision(): Make decision using hybrid framework
    - act(): Execute action based on decision
    - execute_task(): Execute agent-specific task
    
    This is a Protocol (not abstract class) so agents can use duck typing
    or explicit inheritance.
    """
    
    def should_wake(self, event: WakeEvent) -> bool:
        """
        Determine if agent should wake up for this event.
        
        Args:
            event: Wake event with topic, type, data
        
        Returns:
            bool: True if agent should wake and process event
        
        Examples:
            # WowDomain wakes on domain events
            event = WakeEvent(topic="domain.model.created", event_type=EventType.DOMAIN_EVENT, data={})
            should_wake(event) -> True
            
            # WowEvent wakes on all events (message bus)
            event = WakeEvent(topic="*.*.created", event_type=EventType.AGENT_EVENT, data={})
            should_wake(event) -> True
        """
        ...
    
    def make_decision(self, request: DecisionRequest) -> Any:
        """
        Make decision using hybrid framework.
        
        Decision flow:
        1. Try deterministic rules
        2. Check decision cache
        3. Search vector memory for similar decisions
        4. Use LLM for complex reasoning
        
        Args:
            request: Decision request with context
        
        Returns:
            Decision: Decision with approved, reason, confidence, method, cost
        """
        ...
    
    def act(self, context: ActionContext) -> Dict[str, Any]:
        """
        Execute action based on decision.
        
        Args:
            context: Action context with type, parameters, decision
        
        Returns:
            dict: Action result with status and details
        """
        ...
    
    def execute_task(self, task: TaskDefinition) -> None:
        """
        Execute agent-specific task.
        
        Args:
            task: Task definition with type and data
        """
        ...


# =============================================================================
# HELPER TYPES
# =============================================================================

# Type alias for agent capabilities
AgentCapabilities = Dict[str, List[str]]

# Type alias for agent constraints
AgentConstraints = List[Dict[str, str]]

# Type alias for wake patterns
WakePatterns = List[str]

# Type alias for decision history
DecisionHistory = List[Dict[str, Any]]


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_wake_event(event: Dict[str, Any]) -> WakeEvent:
    """
    Validate and convert dict to WakeEvent.
    
    Args:
        event: Event dict
    
    Returns:
        WakeEvent: Validated event object
    
    Raises:
        ValueError: If event is invalid
    """
    required_fields = ["topic", "event_type", "data"]
    for field in required_fields:
        if field not in event:
            raise ValueError(f"Missing required field: {field}")
    
    # Convert event_type string to enum
    event_type = event["event_type"]
    if isinstance(event_type, str):
        event_type = EventType(event_type)
    
    return WakeEvent(
        topic=event["topic"],
        event_type=event_type,
        data=event["data"],
        timestamp=event.get("timestamp", datetime.now()),
        source=event.get("source"),
        correlation_id=event.get("correlation_id"),
        priority=event.get("priority", 5)
    )


def validate_decision_request(request: Dict[str, Any]) -> DecisionRequest:
    """
    Validate and convert dict to DecisionRequest.
    
    Args:
        request: Request dict
    
    Returns:
        DecisionRequest: Validated request object
    
    Raises:
        ValueError: If request is invalid
    """
    required_fields = ["request_type", "context"]
    for field in required_fields:
        if field not in request:
            raise ValueError(f"Missing required field: {field}")
    
    return DecisionRequest(
        request_type=request["request_type"],
        context=request["context"],
        requester=request.get("requester"),
        deadline=request.get("deadline"),
        constraints=request.get("constraints", {}),
        similar_cases=request.get("similar_cases", [])
    )


def validate_task_definition(task: Dict[str, Any]) -> TaskDefinition:
    """
    Validate and convert dict to TaskDefinition.
    
    Args:
        task: Task dict
    
    Returns:
        TaskDefinition: Validated task object
    
    Raises:
        ValueError: If task is invalid
    """
    required_fields = ["task_id", "task_type", "data"]
    for field in required_fields:
        if field not in task:
            raise ValueError(f"Missing required field: {field}")
    
    return TaskDefinition(
        task_id=task["task_id"],
        task_type=task["task_type"],
        data=task["data"],
        priority=task.get("priority", 5),
        dependencies=task.get("dependencies", []),
        deadline=task.get("deadline"),
        created_at=task.get("created_at", datetime.now()),
        assigned_to=task.get("assigned_to")
    )


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
Example: Using CoEInterface types

```python
from waooaw.factory.interfaces import (
    CoEInterface, WakeEvent, DecisionRequest, ActionContext,
    EventType, DecisionMethod, ActionStatus
)
from waooaw.agents.base_agent import Decision

class WowDomain(CoEInterface):
    '''WowDomain implements CoEInterface'''
    
    def should_wake(self, event: WakeEvent) -> bool:
        # Wake on domain events
        return event.topic.startswith("domain.") or event.matches_pattern("wowdomain.*")
    
    def make_decision(self, request: DecisionRequest) -> Decision:
        # Use hybrid decision framework
        if request.request_type == "validate_aggregate":
            # Deterministic rule
            fields = request.context.get("fields", [])
            if "id" not in fields:
                return Decision(
                    approved=False,
                    reason="Aggregate must have ID field",
                    confidence=1.0,
                    method=DecisionMethod.DETERMINISTIC_RULE.value,
                    cost=0.0
                )
        
        # Defer to LLM
        return self._call_llm(request)
    
    def act(self, context: ActionContext) -> dict:
        if context.action_type == "create_domain_model":
            model = self._create_model(context.parameters)
            return {
                "status": ActionStatus.COMPLETED.value,
                "model_id": model.id
            }
    
    def execute_task(self, task: TaskDefinition):
        if task.task_type == "model_domain":
            self._model_domain(task.data)

# Usage
domain = WowDomain("WowDomain", config)

# Wake check
event = WakeEvent(
    topic="domain.model.created",
    event_type=EventType.DOMAIN_EVENT,
    data={"entity": "User"}
)
if domain.should_wake(event):
    domain.process_event(event)

# Decision
request = DecisionRequest(
    request_type="validate_aggregate",
    context={"fields": ["id", "name", "email"]}
)
decision = domain.make_decision(request)

# Action
context = ActionContext(
    action_type="create_domain_model",
    parameters={"name": "User", "fields": [...]}
)
result = domain.act(context)
```
"""
