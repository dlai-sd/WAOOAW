# WAOOAW Orchestration Layer Design

**Version**: 1.0  
**Date**: December 27, 2025  
**Status**: Design Complete → Implementation Ready  
**Inspiration**: jBPM (Java Business Process Management) patterns adapted for Python  
**Related Docs**: MESSAGE_BUS_ARCHITECTURE.md, AGENT_MESSAGE_HANDLER_DESIGN.md, BASE_AGENT_CORE_ARCHITECTURE.md

---

## Executive Summary

The **Orchestration Layer** is the conductor of the WAOOAW agent network, managing complex multi-agent workflows using battle-tested patterns from jBPM (18 years in production, used by banks/insurance/healthcare).

### Why jBPM-Inspired?

| jBPM Pattern | WAOOAW Use Case | Benefit |
|-------------|-----------------|---------|
| **Long-running processes** | 7-day customer trials, multi-day campaigns | Workflows survive restarts, span days/weeks |
| **Human tasks** | Agent escalation to GitHub issues | Seamless agent→human→agent flow |
| **Process variables** | Shared context across agents | Rich handoff context, audit trail |
| **Timer events** | Trial expiry, SLA tracking | Built-in scheduling, timeout handling |
| **Compensation** | Rollback failed workflows | Automatic cleanup, data consistency |
| **Process versioning** | Multiple workflow versions | Zero-downtime updates, A/B testing |
| **BPMN notation** | Visual workflow design | Standard notation, clear communication |

### Architecture Choice

**Hybrid Model**: LangGraph (Python-native) + jBPM Patterns + Temporal Concepts

```
┌─────────────────────────────────────────────────────────────┐
│              WAOOAW Orchestration Layer                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Workflow Engine (Python)                            │  │
│  │  • LangGraph state graphs                            │  │
│  │  • jBPM patterns (tasks, timers, compensation)       │  │
│  │  │  • Temporal durability (event sourcing)            │  │
│  └──────────────────────────────────────────────────────┘  │
│         ↓                    ↓                    ↓          │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐      │
│  │  Agents  │        │  Humans  │        │  Timers  │      │
│  │ (Service │        │  (User   │        │  (Event  │      │
│  │  Tasks)  │        │  Tasks)  │        │  Based)  │      │
│  └──────────┘        └──────────┘        └──────────┘      │
│         ↓                    ↓                    ↓          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Message Bus (Redis Streams)                         │  │
│  └──────────────────────────────────────────────────────┘  │
│         ↓                    ↓                    ↓          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  State Store (PostgreSQL)                            │  │
│  │  • Workflow instances                                │  │
│  │  • Process variables (audit trail)                   │  │
│  │  • Task states                                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Cost**: $0 (all open source)  
**Scalability**: Proven to 1000+ agents (LangGraph) + 18 years production (jBPM patterns)

---

## Table of Contents

1. [jBPM Patterns Catalog](#1-jbpm-patterns-catalog)
2. [Workflow Definition Format](#2-workflow-definition-format)
3. [Process Variables & Context](#3-process-variables--context)
4. [Task Types](#4-task-types)
5. [Gateway Types (Routing)](#5-gateway-types-routing)
6. [Timer Events](#6-timer-events)
7. [Compensation & Rollback](#7-compensation--rollback)
8. [Process Versioning](#8-process-versioning)
9. [Integration Points](#9-integration-points)
10. [Python Implementation](#10-python-implementation)
11. [Example Workflows](#11-example-workflows)
12. [Migration Strategy](#12-migration-strategy)

---

## 1. jBPM Patterns Catalog

### 1.1 Core Patterns Borrowed

| Pattern | jBPM Concept | WAOOAW Implementation |
|---------|--------------|----------------------|
| **Service Task** | Automated work (API call, agent) | Agent execution (WowVision, WowContent, etc.) |
| **User Task** | Human work (approval, review) | GitHub issue creation, wait for human response |
| **Timer Event** | Wait for duration/deadline | 7-day trial, SLA timeouts, scheduled wakes |
| **Exclusive Gateway** | If-then-else routing | Approval decisions, conditional flows |
| **Parallel Gateway** | Fork/join multiple paths | Fan-out to multiple agents, wait for all |
| **Message Event** | Wait for external signal | Wait for webhook, agent response, payment |
| **Compensation** | Undo on failure | Rollback database, delete issues, refund |
| **Process Variables** | Shared context/state | Agent handoff context, decision history |

### 1.2 BPMN 2.0 Visual Notation

We'll use standard BPMN symbols in documentation:

```
EVENTS:
⭕ Start Event        - Workflow begins
⏱️ Timer Event        - Wait for duration
📧 Message Event      - Wait for signal
⛔ End Event          - Workflow completes

TASKS:
□ Service Task       - Agent work (automated)
👤 User Task          - Human work (manual)

GATEWAYS:
◆ Exclusive Gateway  - If-then-else (one path)
✚ Parallel Gateway   - Fork/join (all paths)
◇ Event Gateway      - Wait for first event
```

**Example: PR Review Workflow**
```
⭕ → □(WowVision) → ◆ → □(Deploy) → ⛔
    Start   Validate   Pass?  Execute   End
                        ↓ Fail
                      □(Issue) → ⛔
                      Create    End
```

---

## 2. Workflow Definition Format

### 2.1 Python-Based DSL (LangGraph Style)

```python
from waooaw.orchestration import (
    Workflow, ServiceTask, UserTask, Timer,
    ExclusiveGateway, ParallelGateway, EndEvent
)

# Define workflow
workflow = Workflow(
    id="pr_review",
    version="1.0",
    name="Pull Request Review Workflow"
)

# Add tasks
vision_task = ServiceTask(
    id="wowvision_validate",
    agent=WowVisionPrime,
    input_variables=["pr_number", "files_changed"],
    output_variables=["vision_approved", "violations"],
    compensation=rollback_vision_state
)

# Add gateway (decision point)
approval_gateway = ExclusiveGateway(
    id="check_approval",
    conditions={
        "deploy": lambda ctx: ctx["vision_approved"] == True,
        "create_issue": lambda ctx: ctx["vision_approved"] == False
    }
)

# Build flow
workflow.start() \
    .then(vision_task) \
    .then(approval_gateway) \
    .route("deploy", deploy_task) \
    .route("create_issue", issue_task) \
    .end()
```

### 2.2 YAML Definition (Optional, for Non-Programmers)

```yaml
workflow:
  id: pr_review
  version: "1.0"
  name: Pull Request Review Workflow
  
  variables:
    pr_number: {type: integer, required: true}
    files_changed: {type: list, required: true}
    vision_approved: {type: boolean}
    violations: {type: list}
  
  tasks:
    - id: wowvision_validate
      type: service_task
      agent: WowVisionPrime
      input: [pr_number, files_changed]
      output: [vision_approved, violations]
      compensation: rollback_vision_state
      
    - id: check_approval
      type: exclusive_gateway
      conditions:
        deploy:
          expression: vision_approved == true
        create_issue:
          expression: vision_approved == false
    
    - id: deploy_changes
      type: service_task
      agent: WowDeploy
      precondition: check_approval.deploy
      
    - id: create_github_issue
      type: service_task
      agent: WowVision
      method: create_issue
      precondition: check_approval.create_issue
  
  flow:
    - start → wowvision_validate
    - wowvision_validate → check_approval
    - check_approval[deploy] → deploy_changes
    - check_approval[create_issue] → create_github_issue
    - deploy_changes → end
    - create_github_issue → end
```

---

## 3. Process Variables & Context

### 3.1 Variable Lifecycle

**jBPM Pattern**: Process variables persist across entire workflow, with audit trail

**WAOOAW Implementation**:
```python
@dataclass
class ProcessVariable:
    """jBPM-inspired process variable with versioning"""
    name: str
    value: Any
    type: str  # 'string', 'integer', 'boolean', 'object', 'list'
    version: int  # Increments on each update
    created_at: datetime
    created_by: str  # Agent ID or 'system'
    updated_at: datetime
    updated_by: str  # Agent ID who last modified
    scope: str = "instance"  # 'instance', 'workflow', 'global'

class WorkflowInstance:
    """Active workflow execution"""
    
    def __init__(self, workflow_id: str, version: str):
        self.instance_id = str(uuid.uuid4())
        self.workflow_id = workflow_id
        self.workflow_version = version
        self.variables: Dict[str, ProcessVariable] = {}
        self.state = "ACTIVE"
        self.current_node = None
        self.start_time = datetime.now()
        self.end_time = None
        
    def set_variable(
        self, 
        name: str, 
        value: Any, 
        actor: str,
        variable_type: str = None
    ):
        """Set process variable with audit trail"""
        existing = self.variables.get(name)
        
        var = ProcessVariable(
            name=name,
            value=value,
            type=variable_type or type(value).__name__,
            version=(existing.version + 1) if existing else 1,
            created_at=existing.created_at if existing else datetime.now(),
            created_by=existing.created_by if existing else actor,
            updated_at=datetime.now(),
            updated_by=actor
        )
        
        self.variables[name] = var
        
        # Persist to database
        self._persist_variable(var)
        
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get current variable value"""
        var = self.variables.get(name)
        return var.value if var else default
    
    def get_variable_history(self, name: str) -> List[ProcessVariable]:
        """Get all versions of a variable (audit trail)"""
        return db.query(ProcessVariable).filter(
            ProcessVariable.instance_id == self.instance_id,
            ProcessVariable.name == name
        ).order_by(ProcessVariable.version).all()
```

### 3.2 Context Scopes

| Scope | Lifetime | Use Case | Example |
|-------|----------|----------|---------|
| **Instance** | Single workflow run | PR-specific data | `pr_number`, `author`, `files_changed` |
| **Workflow** | All instances of workflow | Shared config | `approval_threshold`, `timeout_minutes` |
| **Global** | All workflows | Platform settings | `llm_budget`, `rate_limit` |

### 3.3 Example: PR Review Context

```python
# Workflow starts
instance = workflow.start(variables={
    "pr_number": 42,
    "author": "johndoe",
    "files_changed": ["app.py", "config.yaml"],
    "phase": "phase1"
})

# WowVision task executes
instance.set_variable("vision_approved", True, actor="WowVision Prime")
instance.set_variable("violations", [], actor="WowVision Prime")
instance.set_variable("review_duration_ms", 450, actor="WowVision Prime")

# Deploy task sees previous results
approved = instance.get_variable("vision_approved")  # True
violations = instance.get_variable("violations")  # []

# Audit trail available
history = instance.get_variable_history("vision_approved")
# [
#   {version: 1, value: True, updated_by: "WowVision Prime", updated_at: "..."}
# ]
```

---

## 4. Task Types

### 4.1 Service Task (Agent Work)

**jBPM Pattern**: Automated work performed by service/API

**WAOOAW Pattern**: Agent execution

```python
class ServiceTask:
    """Automated task executed by an agent"""
    
    def __init__(
        self,
        id: str,
        agent: Type['WAAOOWAgent'],
        method: str = "execute",
        input_variables: List[str] = None,
        output_variables: List[str] = None,
        timeout: timedelta = timedelta(minutes=5),
        retry_policy: RetryPolicy = None,
        compensation: Callable = None
    ):
        self.id = id
        self.agent = agent
        self.method = method
        self.input_variables = input_variables or []
        self.output_variables = output_variables or []
        self.timeout = timeout
        self.retry_policy = retry_policy
        self.compensation = compensation
    
    async def execute(self, instance: WorkflowInstance):
        """Execute agent task"""
        # Extract input variables
        inputs = {
            var: instance.get_variable(var)
            for var in self.input_variables
        }
        
        # Execute agent
        try:
            agent_instance = self.agent(instance_id=instance.instance_id)
            result = await asyncio.wait_for(
                getattr(agent_instance, self.method)(inputs),
                timeout=self.timeout.total_seconds()
            )
            
            # Store output variables
            for var, value in result.items():
                if var in self.output_variables:
                    instance.set_variable(
                        var, 
                        value, 
                        actor=agent_instance.agent_id
                    )
            
            # Log execution
            await self._log_execution(instance, result, status="SUCCESS")
            
            return result
            
        except Exception as e:
            # Log failure
            await self._log_execution(instance, {}, status="FAILED", error=str(e))
            
            # Run compensation if defined
            if self.compensation:
                await self.compensation(instance)
            
            raise
```

**Example Usage**:
```python
vision_task = ServiceTask(
    id="wowvision_validate",
    agent=WowVisionPrime,
    method="validate_pr",
    input_variables=["pr_number", "files_changed"],
    output_variables=["vision_approved", "violations"],
    timeout=timedelta(minutes=2),
    compensation=rollback_vision_state
)
```

---

### 4.2 User Task (Human Work)

**jBPM Pattern**: Work item assigned to human, workflow waits for completion

**WAOOAW Pattern**: GitHub issue creation, wait for human response

```python
class UserTask:
    """Human work (escalation to GitHub issues)"""
    
    def __init__(
        self,
        id: str,
        title: str,
        body_template: str,
        assignee: Optional[str] = None,
        labels: List[str] = None,
        sla_hours: int = 24,
        on_timeout: Callable = None,
        decision_variable: str = None
    ):
        self.id = id
        self.title = title
        self.body_template = body_template
        self.assignee = assignee
        self.labels = labels or ["human-task", "needs-review"]
        self.sla_hours = sla_hours
        self.on_timeout = on_timeout
        self.decision_variable = decision_variable or f"{id}_decision"
    
    async def execute(self, instance: WorkflowInstance):
        """Create GitHub issue and wait for human response"""
        
        # Render body template with variables
        body = self.body_template.format(**instance.variables)
        
        # Create GitHub issue
        issue = await github_api.create_issue(
            title=f"[Workflow {instance.instance_id}] {self.title}",
            body=body,
            assignee=self.assignee,
            labels=self.labels + [f"workflow-{instance.workflow_id}"]
        )
        
        # Store issue reference
        instance.set_variable(
            f"{self.id}_issue_number",
            issue.number,
            actor="system"
        )
        
        # Wait for response (with timeout)
        try:
            decision = await asyncio.wait_for(
                self._wait_for_github_response(instance, issue.number),
                timeout=timedelta(hours=self.sla_hours).total_seconds()
            )
            
            instance.set_variable(
                self.decision_variable,
                decision,
                actor=issue.resolved_by
            )
            
            return decision
            
        except asyncio.TimeoutError:
            # SLA breached
            if self.on_timeout:
                return await self.on_timeout(instance)
            else:
                # Default: escalate to manager
                return await self._escalate_to_manager(instance, issue)
    
    async def _wait_for_github_response(
        self, 
        instance: WorkflowInstance, 
        issue_number: int
    ):
        """Poll GitHub issue for resolution"""
        while True:
            issue = await github_api.get_issue(issue_number)
            
            # Check for decision labels
            if "approved" in issue.labels:
                return {"approved": True, "comment": issue.last_comment}
            elif "rejected" in issue.labels:
                return {"approved": False, "comment": issue.last_comment}
            
            # Wait before next poll
            await asyncio.sleep(60)  # Check every minute
```

**Example Usage**:
```python
human_review = UserTask(
    id="architect_approval",
    title="Review Major Architecture Change",
    body_template="""
**Workflow**: {instance_id}
**Agent**: {agent_requesting}
**Change**: {change_description}

**Context**:
- Files changed: {files_changed}
- Risk level: {risk_level}
- Estimated impact: {impact}

**Action Required**:
- Review the proposed changes
- Add label `approved` to approve
- Add label `rejected` to reject
- Add comment with reasoning
""",
    assignee="engineering-lead",
    sla_hours=4,
    on_timeout=escalate_to_cto
)
```

---

### 4.3 Script Task (Lightweight Logic)

**jBPM Pattern**: Small snippets of code (calculations, transformations)

**WAOOAW Pattern**: Python functions for simple logic

```python
class ScriptTask:
    """Lightweight Python script execution"""
    
    def __init__(
        self,
        id: str,
        script: Callable[[WorkflowInstance], Any],
        output_variable: str = None
    ):
        self.id = id
        self.script = script
        self.output_variable = output_variable
    
    async def execute(self, instance: WorkflowInstance):
        """Execute Python function"""
        result = await self.script(instance)
        
        if self.output_variable:
            instance.set_variable(
                self.output_variable,
                result,
                actor="system"
            )
        
        return result
```

**Example Usage**:
```python
calculate_priority = ScriptTask(
    id="calculate_priority",
    script=lambda ctx: 5 if ctx.get_variable("files_changed") > 10 else 3,
    output_variable="priority_level"
)
```

---

## 5. Gateway Types (Routing)

### 5.1 Exclusive Gateway (XOR)

**jBPM Pattern**: If-then-else, exactly one path taken

**BPMN Symbol**: ◆ (diamond)

```python
class ExclusiveGateway:
    """XOR gateway - one and only one path"""
    
    def __init__(
        self,
        id: str,
        conditions: Dict[str, Callable[[WorkflowInstance], bool]],
        default_path: str = None
    ):
        self.id = id
        self.conditions = conditions
        self.default_path = default_path
    
    async def execute(self, instance: WorkflowInstance) -> str:
        """Evaluate conditions, return path to take"""
        for path_name, condition in self.conditions.items():
            if await condition(instance):
                return path_name
        
        # No condition matched, use default
        if self.default_path:
            return self.default_path
        
        raise WorkflowError(f"No path matched in gateway {self.id}")
```

**Example**:
```python
approval_gate = ExclusiveGateway(
    id="check_approval",
    conditions={
        "deploy": lambda ctx: ctx.get_variable("vision_approved") == True,
        "fix_violations": lambda ctx: (
            ctx.get_variable("vision_approved") == False and
            len(ctx.get_variable("violations")) < 5
        ),
        "reject": lambda ctx: len(ctx.get_variable("violations")) >= 5
    },
    default_path="reject"
)
```

---

### 5.2 Parallel Gateway (AND)

**jBPM Pattern**: Fork to multiple paths, wait for all to complete

**BPMN Symbol**: ✚ (plus in diamond)

```python
class ParallelGateway:
    """AND gateway - fork/join all paths"""
    
    def __init__(
        self,
        id: str,
        mode: str = "fork"  # 'fork' or 'join'
    ):
        self.id = id
        self.mode = mode
    
    async def execute(
        self, 
        instance: WorkflowInstance,
        tasks: List[Task] = None
    ):
        """Fork: execute all tasks in parallel. Join: wait for all."""
        if self.mode == "fork":
            # Execute all tasks concurrently
            results = await asyncio.gather(*[
                task.execute(instance) for task in tasks
            ])
            return results
        else:
            # Join mode - just a marker, no execution
            return None
```

**Example**:
```python
# Fork: ask 3 agents simultaneously
parallel_review = ParallelGateway(id="parallel_review", mode="fork")

tasks = [
    ServiceTask(id="wowvision", agent=WowVisionPrime),
    ServiceTask(id="wowdomain", agent=WowDomainEnforcer),
    ServiceTask(id="wowbrand", agent=WowBrandVoice)
]

# All execute in parallel
results = await parallel_review.execute(instance, tasks)

# Join: wait for all to complete
join = ParallelGateway(id="join_reviews", mode="join")
```

---

### 5.3 Event-Based Gateway

**jBPM Pattern**: Wait for first of multiple events

**WAOOAW Pattern**: Race between timeout, approval, cancellation

```python
class EventBasedGateway:
    """Wait for first event to occur"""
    
    def __init__(
        self,
        id: str,
        events: Dict[str, Callable]  # event_name → handler
    ):
        self.id = id
        self.events = events
    
    async def execute(self, instance: WorkflowInstance):
        """Wait for first event, return which event occurred"""
        tasks = {
            name: asyncio.create_task(handler(instance))
            for name, handler in self.events.items()
        }
        
        # Wait for first to complete
        done, pending = await asyncio.wait(
            tasks.values(),
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel remaining
        for task in pending:
            task.cancel()
        
        # Return which event won
        completed_task = done.pop()
        event_name = [
            name for name, task in tasks.items() 
            if task == completed_task
        ][0]
        
        return event_name
```

**Example**:
```python
wait_for_event = EventBasedGateway(
    id="wait_approval_or_timeout",
    events={
        "approved": wait_for_github_label("approved"),
        "rejected": wait_for_github_label("rejected"),
        "timeout": asyncio.sleep(3600)  # 1 hour
    }
)

# Returns: "approved", "rejected", or "timeout"
outcome = await wait_for_event.execute(instance)
```

---

## 6. Timer Events

### 6.1 Timer Definitions

**jBPM Pattern**: Three timer types - duration, cycle, date

```python
class TimerEvent:
    """jBPM-style timer event"""
    
    def __init__(
        self,
        id: str,
        timer_type: str,  # 'duration', 'cycle', 'date'
        timer_value: Any
    ):
        self.id = id
        self.timer_type = timer_type
        self.timer_value = timer_value
    
    async def execute(self, instance: WorkflowInstance):
        """Wait for timer"""
        if self.timer_type == "duration":
            # Wait for duration (e.g., 7 days)
            await asyncio.sleep(self.timer_value.total_seconds())
            
        elif self.timer_type == "cycle":
            # Repeating timer (e.g., every day at 9am)
            # Schedule with cron/celery
            await self._schedule_recurring(instance, self.timer_value)
            
        elif self.timer_type == "date":
            # Wait until specific date/time
            wait_seconds = (self.timer_value - datetime.now()).total_seconds()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
```

### 6.2 Use Cases

**A. Trial Expiry (7-Day Duration)**
```python
trial_timer = TimerEvent(
    id="trial_expires",
    timer_type="duration",
    timer_value=timedelta(days=7)
)

# Workflow:
# Start trial → Wait 7 days → Check conversion
workflow.start() \
    .then(start_trial) \
    .then(trial_timer) \
    .then(check_conversion) \
    .end()
```

**B. SLA Timeout (Boundary Event)**
```python
# Attach timeout to human task
human_task = UserTask(id="approval", sla_hours=4)
timeout = TimerEvent(
    id="timeout_4h",
    timer_type="duration",
    timer_value=timedelta(hours=4)
)

# If human doesn't respond in 4 hours, escalate
workflow.add_boundary_event(
    attached_to=human_task,
    event=timeout,
    interrupt=True,  # Cancel human task
    then=escalate_task
)
```

**C. Daily Report (Repeating Cycle)**
```python
daily_report = TimerEvent(
    id="daily_9am",
    timer_type="cycle",
    timer_value="0 9 * * *"  # Cron expression
)

# Every day at 9am, generate report
workflow.start_on_timer(daily_report) \
    .then(generate_report) \
    .then(send_email) \
    .end()
```

---

## 7. Compensation & Rollback

### 7.1 Compensation Pattern

**jBPM Pattern**: Define compensating actions for each task

**WAOOAW Pattern**: Undo agent actions on workflow failure

```python
@dataclass
class CompensationHandler:
    """Defines how to undo a task"""
    task_id: str
    compensate: Callable[[WorkflowInstance], Awaitable[None]]
    order: int = 0  # Compensation order (reverse execution)

class WorkflowTransaction:
    """Transaction-like workflow with rollback"""
    
    def __init__(self):
        self.completed_tasks: List[Tuple[Task, CompensationHandler]] = []
        self.state = "ACTIVE"
    
    async def execute_task(
        self, 
        task: Task, 
        instance: WorkflowInstance,
        compensation: CompensationHandler = None
    ):
        """Execute task and track for compensation"""
        try:
            result = await task.execute(instance)
            
            # Task succeeded, store compensation
            if compensation:
                self.completed_tasks.append((task, compensation))
            
            return result
            
        except Exception as e:
            # Task failed, rollback all previous tasks
            await self.compensate_all(instance)
            raise
    
    async def compensate_all(self, instance: WorkflowInstance):
        """Rollback all completed tasks in reverse order"""
        self.state = "COMPENSATING"
        
        # Reverse order (undo last action first)
        for task, handler in reversed(self.completed_tasks):
            try:
                await handler.compensate(instance)
                logger.info(f"Compensated task {task.id}")
            except Exception as e:
                logger.error(f"Compensation failed for {task.id}: {e}")
                # Continue compensating other tasks
        
        self.state = "COMPENSATED"
```

### 7.2 Example: Multi-Step Campaign Creation

```python
async def rollback_github_issue(instance: WorkflowInstance):
    """Delete created GitHub issue"""
    issue_num = instance.get_variable("issue_number")
    await github_api.close_issue(issue_num, comment="Workflow failed, rolling back")

async def rollback_database_entry(instance: WorkflowInstance):
    """Delete database record"""
    record_id = instance.get_variable("campaign_record_id")
    await db.delete(Campaign, id=record_id)

async def rollback_email(instance: WorkflowInstance):
    """Send cancellation email"""
    customer_email = instance.get_variable("customer_email")
    await email_api.send(
        to=customer_email,
        subject="Campaign Cancelled",
        body="Due to a processing error, your campaign has been cancelled."
    )

# Define workflow with compensation
transaction = WorkflowTransaction()

# Step 1: Create GitHub issue
await transaction.execute_task(
    task=ServiceTask(id="create_issue", agent=WowVision, method="create_issue"),
    instance=instance,
    compensation=CompensationHandler(
        task_id="create_issue",
        compensate=rollback_github_issue,
        order=3
    )
)

# Step 2: Create database record
await transaction.execute_task(
    task=ServiceTask(id="create_record", agent=WowRevenue, method="create_campaign"),
    instance=instance,
    compensation=CompensationHandler(
        task_id="create_record",
        compensate=rollback_database_entry,
        order=2
    )
)

# Step 3: Send confirmation email
await transaction.execute_task(
    task=ServiceTask(id="send_email", agent=WowConnect, method="send_email"),
    instance=instance,
    compensation=CompensationHandler(
        task_id="send_email",
        compensate=rollback_email,
        order=1
    )
)

# If any step fails:
# 1. Send cancellation email (order 1)
# 2. Delete database record (order 2)
# 3. Close GitHub issue (order 3)
```

---

## 8. Process Versioning

### 8.1 Version Management

**jBPM Pattern**: Multiple workflow versions coexist, instances stick to version

```python
class WorkflowRegistry:
    """Manages multiple workflow versions"""
    
    def __init__(self):
        self.workflows: Dict[str, Dict[str, Workflow]] = {}
        # workflows[workflow_id][version] = Workflow
    
    def register(self, workflow: Workflow):
        """Register new workflow version"""
        if workflow.id not in self.workflows:
            self.workflows[workflow.id] = {}
        
        self.workflows[workflow.id][workflow.version] = workflow
        logger.info(f"Registered {workflow.id} v{workflow.version}")
    
    def get(self, workflow_id: str, version: str = "latest") -> Workflow:
        """Get specific workflow version"""
        if version == "latest":
            versions = self.workflows[workflow_id]
            latest_version = max(versions.keys(), key=self._parse_version)
            return versions[latest_version]
        else:
            return self.workflows[workflow_id][version]
    
    def list_versions(self, workflow_id: str) -> List[str]:
        """Get all versions of a workflow"""
        return list(self.workflows[workflow_id].keys())
    
    @staticmethod
    def _parse_version(version: str) -> tuple:
        """Parse semantic version for comparison"""
        return tuple(map(int, version.split('.')))
```

### 8.2 Migration Strategy

```python
class WorkflowMigration:
    """Migrate running instances to new workflow version"""
    
    async def migrate_instance(
        self,
        instance_id: str,
        target_version: str,
        migration_point: str = None  # Where to resume in new version
    ):
        """Migrate running instance to new workflow version"""
        
        # 1. Load current instance
        instance = await self.load_instance(instance_id)
        old_version = instance.workflow_version
        
        # 2. Checkpoint current state
        checkpoint = await self.create_checkpoint(instance)
        
        # 3. Load new workflow version
        new_workflow = registry.get(instance.workflow_id, target_version)
        
        # 4. Map variables (handle schema changes)
        migrated_variables = await self.migrate_variables(
            instance.variables,
            old_version,
            target_version
        )
        
        # 5. Create new instance with migrated state
        new_instance = WorkflowInstance(
            workflow_id=instance.workflow_id,
            version=target_version
        )
        new_instance.variables = migrated_variables
        new_instance.current_node = migration_point or instance.current_node
        
        # 6. Resume from migration point
        await new_workflow.resume(new_instance)
        
        return new_instance
```

### 8.3 Versioning Use Cases

**A. Gradual Rollout**
```python
# Deploy v1.1 to 10% of new workflows
if random.random() < 0.1:
    workflow = registry.get("pr_review", "1.1")
else:
    workflow = registry.get("pr_review", "1.0")
```

**B. A/B Testing**
```python
# Test two approval strategies
if customer.segment == "enterprise":
    workflow = registry.get("onboarding", "2.0-strict")
else:
    workflow = registry.get("onboarding", "2.0-standard")
```

**C. Zero-Downtime Deployment**
```python
# Old instances continue on v1.0
# New instances start on v1.1
# No disruption
```

---

## 9. Integration Points

### 9.1 Message Bus Integration

**How Orchestration Layer Uses Message Bus**:

```python
class WorkflowEngine:
    """Orchestration engine integrated with message bus"""
    
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.registry = WorkflowRegistry()
        self.instances: Dict[str, WorkflowInstance] = {}
    
    async def start_workflow_on_event(
        self,
        trigger_pattern: str,
        workflow_id: str
    ):
        """Start workflow when message matches pattern"""
        
        async def handler(message: Message):
            # Create workflow instance from event
            workflow = self.registry.get(workflow_id, "latest")
            instance = await workflow.start(variables=message.data)
            self.instances[instance.instance_id] = instance
        
        # Subscribe to message bus
        await self.message_bus.subscribe(
            topic=trigger_pattern,
            handler=handler,
            consumer_group="workflow_engine"
        )
```

**Example: GitHub Webhook → Workflow**:
```python
# When PR opened, start PR review workflow
await engine.start_workflow_on_event(
    trigger_pattern="github.pull_request.opened",
    workflow_id="pr_review"
)

# When trial expires, start conversion workflow
await engine.start_workflow_on_event(
    trigger_pattern="customer.trial.expired",
    workflow_id="trial_conversion"
)
```

---

### 9.2 Agent Integration

**How Agents Execute Within Workflows**:

```python
# In base_agent.py
class WAAOOWAgent:
    """Base agent with workflow context awareness"""
    
    def __init__(self, agent_id: str, workflow_instance: WorkflowInstance = None):
        self.agent_id = agent_id
        self.workflow_instance = workflow_instance
        # ... existing fields ...
    
    async def execute_as_service_task(
        self,
        task_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute as workflow service task"""
        
        # Log workflow context
        if self.workflow_instance:
            logger.info(
                f"Agent {self.agent_id} executing in workflow "
                f"{self.workflow_instance.instance_id}"
            )
        
        # Execute agent logic
        result = await self.execute(task_input)
        
        # Return outputs for workflow
        return {
            "success": True,
            "output": result,
            "cost": self.last_execution_cost,
            "duration_ms": self.last_execution_duration
        }
    
    def set_workflow_variable(self, name: str, value: Any):
        """Convenience method to set workflow variables"""
        if self.workflow_instance:
            self.workflow_instance.set_variable(name, value, actor=self.agent_id)
```

---

### 9.3 Database Schema

**New Tables for Orchestration Layer**:

```sql
-- Workflow definitions (versioned)
CREATE TABLE workflow_definitions (
    workflow_id VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    definition_yaml TEXT,  -- YAML workflow definition
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',  -- active, deprecated, retired
    PRIMARY KEY (workflow_id, version)
);

-- Workflow instances (executions)
CREATE TABLE workflow_instances (
    instance_id UUID PRIMARY KEY,
    workflow_id VARCHAR(100) NOT NULL,
    workflow_version VARCHAR(20) NOT NULL,
    state VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE, SUSPENDED, COMPLETED, FAILED, COMPENSATED
    current_node VARCHAR(100),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    started_by VARCHAR(100),
    parent_instance_id UUID,  -- For sub-workflows
    FOREIGN KEY (workflow_id, workflow_version) 
        REFERENCES workflow_definitions(workflow_id, version)
);

-- Process variables (audit trail)
CREATE TABLE process_variables (
    id SERIAL PRIMARY KEY,
    instance_id UUID NOT NULL,
    variable_name VARCHAR(100) NOT NULL,
    variable_value JSONB,
    variable_type VARCHAR(50),
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    scope VARCHAR(20) DEFAULT 'instance',  -- instance, workflow, global
    FOREIGN KEY (instance_id) REFERENCES workflow_instances(instance_id)
);

CREATE INDEX idx_process_variables_instance ON process_variables(instance_id);
CREATE INDEX idx_process_variables_name ON process_variables(variable_name);

-- Task executions (for audit)
CREATE TABLE task_executions (
    id SERIAL PRIMARY KEY,
    instance_id UUID NOT NULL,
    task_id VARCHAR(100) NOT NULL,
    task_type VARCHAR(50),  -- service_task, user_task, script_task
    agent_id VARCHAR(100),
    state VARCHAR(20),  -- PENDING, ACTIVE, COMPLETED, FAILED, COMPENSATED
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    FOREIGN KEY (instance_id) REFERENCES workflow_instances(instance_id)
);

CREATE INDEX idx_task_executions_instance ON task_executions(instance_id);
CREATE INDEX idx_task_executions_agent ON task_executions(agent_id);

-- Human tasks (user tasks)
CREATE TABLE human_tasks (
    id SERIAL PRIMARY KEY,
    instance_id UUID NOT NULL,
    task_id VARCHAR(100) NOT NULL,
    github_issue_number INTEGER,
    assignee VARCHAR(100),
    state VARCHAR(20) DEFAULT 'OPEN',  -- OPEN, CLAIMED, COMPLETED, EXPIRED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    claimed_at TIMESTAMP,
    completed_at TIMESTAMP,
    sla_deadline TIMESTAMP,
    decision_data JSONB,
    FOREIGN KEY (instance_id) REFERENCES workflow_instances(instance_id)
);

CREATE INDEX idx_human_tasks_assignee ON human_tasks(assignee);
CREATE INDEX idx_human_tasks_state ON human_tasks(state);
```

---

## 10. Python Implementation

### 10.1 Core Classes

```python
# waooaw/orchestration/__init__.py
from .workflow import Workflow, WorkflowEngine, WorkflowInstance
from .tasks import ServiceTask, UserTask, ScriptTask
from .gateways import ExclusiveGateway, ParallelGateway, EventBasedGateway
from .events import TimerEvent, MessageEvent, SignalEvent
from .compensation import CompensationHandler, WorkflowTransaction
from .registry import WorkflowRegistry
```

### 10.2 Example: Complete PR Review Workflow

```python
# workflows/pr_review.py
from waooaw.orchestration import (
    Workflow, ServiceTask, UserTask, ExclusiveGateway, 
    ParallelGateway, CompensationHandler
)
from waooaw.agents import WowVisionPrime, WowDomainEnforcer, WowDeploy

# Define workflow
pr_review = Workflow(
    id="pr_review",
    version="1.0",
    name="Pull Request Review and Deployment"
)

# Phase 1: Vision validation
vision_task = ServiceTask(
    id="wowvision_validate",
    agent=WowVisionPrime,
    method="validate_pr",
    input_variables=["pr_number", "files_changed", "author"],
    output_variables=["vision_approved", "violations", "risk_level"],
    timeout=timedelta(minutes=2)
)

# Gateway: Check if approved
approval_gate = ExclusiveGateway(
    id="check_vision_approval",
    conditions={
        "parallel_review": lambda ctx: (
            ctx.get_variable("vision_approved") and
            ctx.get_variable("risk_level") == "high"
        ),
        "direct_deploy": lambda ctx: (
            ctx.get_variable("vision_approved") and
            ctx.get_variable("risk_level") == "low"
        ),
        "create_issue": lambda ctx: not ctx.get_variable("vision_approved")
    }
)

# Parallel review for high-risk PRs
parallel_gate = ParallelGateway(id="parallel_review", mode="fork")
domain_task = ServiceTask(
    id="wowdomain_validate",
    agent=WowDomainEnforcer,
    method="validate_domain_knowledge",
    input_variables=["pr_number", "files_changed"],
    output_variables=["domain_approved", "domain_concerns"]
)

# Human review for high-risk changes
human_review = UserTask(
    id="architect_review",
    title="High-Risk PR Requires Architect Review",
    body_template="""
**PR**: #{pr_number}
**Author**: {author}
**Risk Level**: {risk_level}

**WowVision**: {"✅ Approved" if vision_approved else "❌ Rejected"}
**WowDomain**: {"✅ Approved" if domain_approved else "❌ Concerns raised"}

**Violations**: {violations}
**Domain Concerns**: {domain_concerns}

**Action**: Add label `architect-approved` or `architect-rejected`
""",
    assignee="engineering-lead",
    sla_hours=2
)

# Deploy task
deploy_task = ServiceTask(
    id="deploy_changes",
    agent=WowDeploy,
    method="deploy_pr",
    input_variables=["pr_number"],
    output_variables=["deployment_url", "deployment_status"],
    compensation=rollback_deployment
)

# Create issue task
issue_task = ServiceTask(
    id="create_violation_issue",
    agent=WowVisionPrime,
    method="create_github_issue",
    input_variables=["pr_number", "violations"],
    output_variables=["issue_number"]
)

# Build workflow
pr_review.add_start_event("pr_opened")
pr_review.add_node(vision_task)
pr_review.add_node(approval_gate)

# Conditional flows
pr_review.add_edge(
    "pr_opened", 
    "wowvision_validate"
)
pr_review.add_edge(
    "wowvision_validate", 
    "check_vision_approval"
)

# High-risk path
pr_review.add_conditional_edge(
    "check_vision_approval",
    condition="parallel_review",
    true_target=parallel_gate
)
pr_review.add_parallel_tasks(
    parallel_gate,
    [domain_task, human_review]
)
pr_review.add_edge(
    parallel_gate,
    "deploy_changes"
)

# Low-risk path
pr_review.add_conditional_edge(
    "check_vision_approval",
    condition="direct_deploy",
    true_target="deploy_changes"
)

# Rejection path
pr_review.add_conditional_edge(
    "check_vision_approval",
    condition="create_issue",
    true_target="create_violation_issue"
)

pr_review.add_edge("deploy_changes", "end")
pr_review.add_edge("create_violation_issue", "end")

# Register workflow
registry = WorkflowRegistry()
registry.register(pr_review)
```

### 10.3 Running Workflows

```python
# main.py
from waooaw.orchestration import WorkflowEngine
from waooaw.messaging import MessageBus

# Initialize engine
message_bus = MessageBus(redis_url="redis://localhost:6379")
engine = WorkflowEngine(message_bus)

# Load workflows
engine.load_workflow("workflows/pr_review.py")

# Subscribe to GitHub events
await engine.start_workflow_on_event(
    trigger_pattern="github.pull_request.opened",
    workflow_id="pr_review"
)

# Manual start
instance = await engine.start_workflow(
    workflow_id="pr_review",
    version="1.0",
    variables={
        "pr_number": 42,
        "author": "johndoe",
        "files_changed": ["app.py", "config.yaml"]
    }
)

print(f"Workflow started: {instance.instance_id}")
```

---

## 11. Example Workflows

### 11.1 Customer Onboarding (7-Day Trial)

```python
# workflows/customer_onboarding.py

onboarding = Workflow(id="customer_onboarding", version="1.0")

# Day 1: Capture lead
capture_lead = ServiceTask(
    id="wowconnect_capture",
    agent=WowConnect,
    method="capture_lead",
    input_variables=["email", "selected_agent", "industry"],
    output_variables=["customer_id", "trial_start_date"]
)

# Day 1-7: Daily engagement
daily_value = ServiceTask(
    id="wowonboard_engage",
    agent=WowOnboard,
    method="deliver_daily_value",
    input_variables=["customer_id", "day_number"],
    output_variables=["engagement_score"]
)

# Timer: 7 days
trial_timer = TimerEvent(
    id="wait_7_days",
    timer_type="duration",
    timer_value=timedelta(days=7)
)

# Day 8: Check conversion
check_conversion = ServiceTask(
    id="wowrevenue_check",
    agent=WowRevenue,
    method="check_trial_conversion",
    input_variables=["customer_id"],
    output_variables=["converted", "payment_status"]
)

# Gateway: Converted?
conversion_gate = ExclusiveGateway(
    id="check_converted",
    conditions={
        "activate": lambda ctx: ctx.get_variable("converted") == True,
        "nurture": lambda ctx: (
            ctx.get_variable("converted") == False and
            ctx.get_variable("engagement_score") > 7
        ),
        "churn": lambda ctx: ctx.get_variable("engagement_score") <= 7
    }
)

# Build flow
onboarding.start() \
    .then(capture_lead) \
    .then(daily_value) \
    .then(trial_timer) \
    .then(check_conversion) \
    .then(conversion_gate) \
    .route("activate", activate_subscription) \
    .route("nurture", send_special_offer) \
    .route("churn", record_churn) \
    .end()
```

### 11.2 Marketing Campaign Creation

```python
# workflows/campaign_creation.py

campaign = Workflow(id="campaign_creation", version="1.0")

# Parallel content creation
content_gate = ParallelGateway(id="create_content", mode="fork")

blog_task = ServiceTask(
    id="wowcontent_blog",
    agent=WowContent,
    method="create_blog_post",
    input_variables=["topic", "keywords", "target_audience"],
    output_variables=["blog_url", "word_count"]
)

social_task = ServiceTask(
    id="wowsocial_posts",
    agent=WowSocial,
    method="create_social_posts",
    input_variables=["blog_url", "platforms"],
    output_variables=["post_ids"]
)

email_task = ServiceTask(
    id="wowemail_campaign",
    agent=WowEmail,
    method="create_email_campaign",
    input_variables=["blog_url", "subscriber_list"],
    output_variables=["campaign_id"]
)

# Join: wait for all content
join_gate = ParallelGateway(id="join_content", mode="join")

# Human approval
approval = UserTask(
    id="marketing_manager_approval",
    title="Approve Campaign Launch",
    body_template="""
**Campaign**: {campaign_name}
**Blog**: {blog_url} ({word_count} words)
**Social Posts**: {post_ids}
**Email Campaign**: {campaign_id}

Review and approve for launch.
""",
    assignee="marketing-manager",
    sla_hours=24
)

# Launch
launch = ServiceTask(
    id="launch_campaign",
    agent=WowMarketing,
    method="launch_campaign",
    input_variables=["campaign_id", "post_ids", "blog_url"],
    compensation=rollback_campaign_launch
)

# Build flow with compensation
transaction = WorkflowTransaction()
campaign.start() \
    .then(content_gate) \
    .parallel([blog_task, social_task, email_task]) \
    .then(join_gate) \
    .then(approval) \
    .then(launch) \
    .end()
```

---

## 12. Migration Strategy

### 12.1 Phase 1: Gradual Adoption (Weeks 1-4)

**Week 1-2: Simple Workflows**
- Implement core classes (Workflow, ServiceTask, ExclusiveGateway)
- Migrate simple linear workflows (PR review, file validation)
- Keep existing agent code unchanged

**Week 3-4: Human Tasks**
- Add UserTask implementation
- Migrate escalation workflows
- Integrate with GitHub issues

### 12.2 Phase 2: Advanced Features (Weeks 5-8)

**Week 5-6: Parallel Execution**
- Add ParallelGateway
- Migrate consultation workflows (multi-agent reviews)

**Week 7-8: Timers & Compensation**
- Add TimerEvent for long-running workflows
- Implement compensation for critical workflows

### 12.3 Phase 3: Production Hardening (Weeks 9-12)

**Week 9-10: Process Versioning**
- Implement WorkflowRegistry
- Add version migration logic

**Week 11-12: Monitoring & Optimization**
- Add metrics, traces
- Performance tuning

---

## 13. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Workflow Definition Time** | <2 hours | Time to define new workflow in Python/YAML |
| **Execution Reliability** | 99.9% | % workflows completing without errors |
| **Human Task SLA** | 80% within SLA | % human tasks completed before timeout |
| **Compensation Success** | 100% | % failed workflows properly rolled back |
| **Cost Impact** | $0 added | Orchestration layer should be zero-cost overhead |
| **Developer Satisfaction** | 8/10 | Team survey on workflow framework |

---

## 14. Next Steps

### Immediate (This Week)
1. ✅ Review this design with team
2. ✅ Create GitHub epic for orchestration layer
3. ✅ Update MESSAGE_BUS_ARCHITECTURE.md integration section
4. ✅ Update BASE_AGENT_CORE_ARCHITECTURE.md with workflow awareness

### Week 1-2
- [ ] Implement core classes (Workflow, ServiceTask, ExclusiveGateway)
- [ ] Write unit tests
- [ ] Migrate 1 simple workflow (PR review) as proof-of-concept

### Week 3-4
- [ ] Add UserTask, TimerEvent
- [ ] Implement database schema
- [ ] Migrate 2 more workflows

---

## Appendix A: BPMN Quick Reference

```
SYMBOLS:
⭕ Start Event
⏱️ Timer Start Event
📧 Message Start Event
□ Task (generic)
⚙️ Service Task (automated)
👤 User Task (human)
📝 Script Task (code)
◆ Exclusive Gateway (XOR - one path)
✚ Parallel Gateway (AND - all paths)
◇ Event-Based Gateway (first event wins)
⏸️ Intermediate Timer Event
📬 Intermediate Message Event
⛔ End Event
❌ Error End Event
🏁 Terminate End Event

EXAMPLE:
⭕ → ⚙️(Agent) → ◆ → ⚙️(Deploy) → ⛔
Start   Work    Pass?  Execute   End
                  ↓ Fail
                👤(Human) → ⛔
                Review    End
```

---

## Appendix B: Comparison with Other Orchestration Models

| Feature | WAOOAW (jBPM-inspired) | Temporal | AWS Step Functions | Apache Airflow |
|---------|------------------------|----------|-------------------|----------------|
| **Language** | Python | Go/TS/Python | JSON | Python |
| **Cost** | $0 | $0 | $25/1M transitions | $0 |
| **Long-running** | ✅ Years | ✅ Years | ❌ 1 year max | ✅ Years |
| **Human tasks** | ✅ Built-in | 🟡 Manual | 🟡 Manual | ❌ No |
| **BPMN visual** | ✅ Notation | ❌ Code-first | 🟡 Visual editor | 🟡 DAG view |
| **Compensation** | ✅ Native | ✅ Saga | 🟡 Manual | ❌ No |
| **Versioning** | ✅ Built-in | ✅ Built-in | 🟡 Separate versions | 🟡 Git-based |
| **Local dev** | ✅ Easy | ✅ Easy | ❌ Cloud-only | ✅ Easy |
| **Learning curve** | Medium | Medium | Low | Low |

**Why WAOOAW's Approach Wins**:
- ✅ Python-native (matches our stack)
- ✅ Zero cost (no external services)
- ✅ Proven patterns (18 years jBPM production use)
- ✅ Flexible (can evolve to Temporal if needed)

---

**Version History**:
- v1.0 (Dec 27, 2025): Initial design - jBPM-inspired orchestration layer

**Reviewed By**: [Pending]  
**Approved By**: [Pending]  
**Implementation Start**: v0.3 (Week 1-2, January 2025)
