# Agent Message Handler Design

**Version**: 1.0  
**Date**: December 27, 2025  
**Status**: Design Complete → Implementation Ready  
**Related**: MESSAGE_BUS_ARCHITECTURE.md (v0.2.1)

---

## Executive Summary

Now that we have the **nervous system** (Message Bus), we need **neural receptors** in each agent to handle messages. This document defines the agent-side message handling component that integrates with the Redis Streams message bus.

### Key Design Principle

**Separation of Concerns**:
- **Message Bus** (infrastructure): Transport, persistence, routing
- **Message Handler** (agent component): Processing, callbacks, state

**Analogy**: Message Bus = postal service, Message Handler = mailbox + secretary

---

## Design Questions Answered

### 1. Should message handling be part of base agent or separate component?

**Answer**: **Separate component (composition pattern)**, but tightly integrated

**Rationale**:
- ✅ Single Responsibility: Agent focuses on domain logic, handler focuses on messaging
- ✅ Testability: Can mock handler for agent unit tests
- ✅ Reusability: Same handler for all 14 CoEs
- ✅ Swappable: Can replace with different message systems later

**Implementation**:
```python
class WAAOOWAgent:
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        # ... existing init ...
        self.message_handler = MessageHandler(
            agent_id=agent_id,
            message_bus=MessageBus(config),
            agent=self  # Circular reference for callbacks
        )
```

---

### 2. Async message loop vs event-driven callbacks?

**Answer**: **Both** - Hybrid approach

**Pattern 1: Async Background Loop** (for always-listening agents)
- Continuously polls message bus
- Processes messages as they arrive
- Runs in separate asyncio task

**Pattern 2: Synchronous Polling** (for wake-sleep agents)
- Agent calls `check_messages()` during wake cycle
- Processes messages, then sleeps
- More CPU-efficient for infrequent messages

**Pattern 3: Event-Driven Callbacks** (for reactive handlers)
- Register callbacks for specific message types
- Handler invokes callback when message matches
- Best for request-response patterns

**Use Cases**:
- **Coordinator agents**: Pattern 1 (always-on, background loop)
- **Specialist agents**: Pattern 2 (wake-sleep cycle)
- **Reactive handlers**: Pattern 3 (callbacks for specific events)

---

### 3. How to register message handlers for different topics?

**Answer**: **Decorator pattern + registration dict**

**Interface**:
```python
class MyAgent(WAAOOWAgent):
    def __init__(self, ...):
        super().__init__(...)
        self._register_message_handlers()
    
    def _register_message_handlers(self):
        """Register handlers for message types"""
        self.message_handler.register("vision.review.complete", self.handle_review_complete)
        self.message_handler.register("task.assigned", self.handle_task_assigned)
        self.message_handler.register("system.*", self.handle_system_broadcast)
    
    async def handle_review_complete(self, message: Message):
        """Handle vision review completion"""
        pr_number = message.payload.data.get("pr_number")
        # Process review results...
```

**Alternative: Decorator Pattern**:
```python
class MyAgent(WAAOOWAgent):
    @message_handler("vision.review.complete")
    async def on_review_complete(self, message: Message):
        # Auto-registered on agent init
        pass
    
    @message_handler("task.assigned", priority="high")
    async def on_task_assigned(self, message: Message):
        pass
```

---

### 4. Message priority handling in agent?

**Answer**: **Priority queue with weighted polling**

**Strategy**:
- Poll high-priority streams (p5, p4) more frequently
- Process high-priority messages first
- Low-priority messages processed during idle time

**Algorithm**:
```
while agent.is_running:
    for priority in [5, 4, 3, 2, 1]:
        messages = fetch_messages(priority, limit=10)
        if messages:
            process_messages(messages)
            if priority >= 4:  # High priority
                continue  # Check again immediately
            else:
                break  # Process others in next cycle
    
    await asyncio.sleep(poll_interval)
```

---

### 5. Message state tracking?

**Answer**: **In-memory state + optional DB persistence**

**States**:
- `sent`: Published to bus, awaiting delivery
- `pending_reply`: Request sent, awaiting response
- `processing`: Currently being processed
- `completed`: Successfully handled
- `failed`: Error occurred, moved to DLQ

**Tracking**:
```python
class MessageState:
    message_id: str
    correlation_id: Optional[str]  # For request-response
    state: str  # sent, pending_reply, processing, completed, failed
    sent_at: datetime
    timeout_at: Optional[datetime]
    retry_count: int
    metadata: Dict[str, Any]
```

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      WAAOOWAgent                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            MessageHandler Component                      │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │  │
│  │  │   Inbox     │  │   Outbox     │  │   Handlers    │  │  │
│  │  │ (Priority Q)│  │ (Sent Queue) │  │  (Registry)   │  │  │
│  │  └─────────────┘  └──────────────┘  └───────────────┘  │  │
│  │         │                 │                  │          │  │
│  │         └─────────────────┼──────────────────┘          │  │
│  │                           │                             │  │
│  │                    ┌──────▼───────┐                     │  │
│  │                    │ Message Loop │                     │  │
│  │                    │ (async task) │                     │  │
│  │                    └──────────────┘                     │  │
│  │                           │                             │  │
│  └───────────────────────────┼─────────────────────────────┘  │
│                              │                                 │
│                              ▼                                 │
│                     ┌────────────────┐                         │
│                     │  Message Bus   │                         │
│                     │ (Redis Streams)│                         │
│                     └────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## MessageHandler Class Design

### Class Structure

```python
class MessageHandler:
    """
    Agent-side message handling component.
    
    Responsibilities:
    - Poll messages from bus (inbox)
    - Track sent messages (outbox)
    - Route to registered handlers
    - Manage message state
    - Handle timeouts & retries
    """
    
    def __init__(
        self,
        agent_id: str,
        message_bus: MessageBus,
        agent: 'WAAOOWAgent',
        config: Optional[Dict[str, Any]] = None
    ):
        self.agent_id = agent_id
        self.bus = message_bus
        self.agent = agent
        self.config = config or {}
        
        # Message queues
        self.inbox = PriorityQueue()  # Received messages
        self.outbox = {}  # Sent messages {msg_id: MessageState}
        
        # Handler registry
        self.handlers = {}  # {topic_pattern: [handler_func, ...]}
        self.default_handler = None
        
        # State
        self.is_running = False
        self.message_loop_task = None
        
        # Metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_processed": 0,
            "messages_failed": 0,
        }
    
    # =====================================================================
    # PUBLIC API (used by agents)
    # =====================================================================
    
    async def start(self):
        """Start message handling loop"""
        pass
    
    async def stop(self):
        """Stop message handling loop"""
        pass
    
    def register(self, topic_pattern: str, handler: Callable):
        """Register handler for message topic"""
        pass
    
    async def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        action: str,
        data: Dict[str, Any],
        priority: int = 3,
        expected_outcome: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> str:
        """Send message to another agent(s)"""
        pass
    
    async def send_and_wait(
        self,
        to: str,
        subject: str,
        body: str,
        action: str,
        data: Dict[str, Any],
        timeout: int = 300  # 5 minutes
    ) -> Message:
        """Send message and wait for reply"""
        pass
    
    async def broadcast(
        self,
        subject: str,
        body: str,
        action: str,
        data: Dict[str, Any],
        priority: int = 3
    ) -> str:
        """Broadcast to all agents"""
        pass
    
    async def reply(
        self,
        original_message: Message,
        subject: str,
        body: str,
        data: Dict[str, Any]
    ) -> str:
        """Reply to a message"""
        pass
    
    async def check_messages(self, limit: int = 10) -> List[Message]:
        """
        Synchronous polling: fetch and process messages.
        Used by wake-sleep agents during wake cycle.
        """
        pass
    
    # =====================================================================
    # INTERNAL METHODS (used by component)
    # =====================================================================
    
    async def _message_loop(self):
        """Background loop for async message processing"""
        pass
    
    async def _fetch_from_bus(self, priority: int, limit: int) -> List[Message]:
        """Fetch messages from message bus"""
        pass
    
    async def _process_message(self, message: Message):
        """Route message to appropriate handler"""
        pass
    
    def _match_handlers(self, topic: str) -> List[Callable]:
        """Find handlers matching topic pattern"""
        pass
    
    async def _handle_timeout(self, message_id: str):
        """Handle message timeout"""
        pass
    
    async def _handle_failure(self, message: Message, error: Exception):
        """Handle processing failure"""
        pass
```

---

## Message Handler Patterns

### Pattern 1: Always-Listening (Background Loop)

**Use Case**: Coordinator agents, always-on services

**Implementation**:
```python
class CoordinatorAgent(WAAOOWAgent):
    async def run(self):
        """Main run loop"""
        # Start background message handler
        await self.message_handler.start()
        
        # Agent does other work...
        while True:
            await self.do_coordination_work()
            await asyncio.sleep(10)

# MessageHandler
async def start(self):
    self.is_running = True
    self.message_loop_task = asyncio.create_task(self._message_loop())

async def _message_loop(self):
    """Continuously poll and process messages"""
    while self.is_running:
        try:
            # Poll high priority first
            for priority in [5, 4, 3, 2, 1]:
                messages = await self._fetch_from_bus(priority, limit=10)
                
                for msg in messages:
                    await self._process_message(msg)
                
                # If high priority, check again immediately
                if priority >= 4 and messages:
                    continue
            
            # Sleep between poll cycles
            await asyncio.sleep(self.config.get("poll_interval", 5))
        
        except Exception as e:
            logger.error(f"Message loop error: {e}")
            await asyncio.sleep(10)  # Back off on error
```

**Pros**:
- ✅ Instant message processing (low latency)
- ✅ Always responsive
- ✅ Good for high-throughput agents

**Cons**:
- ❌ Constant CPU usage (even when idle)
- ❌ More complex lifecycle management

---

### Pattern 2: Wake-Sleep Polling

**Use Case**: Specialist agents (WowVision, WowContent, etc.)

**Implementation**:
```python
class SpecialistAgent(WAAOOWAgent):
    async def run(self):
        """Main run loop"""
        while True:
            # Check if should wake
            if not self.should_wake():
                await asyncio.sleep(60)
                continue
            
            # Wake up: restore context
            await self.wake_up()
            
            # Check messages during wake
            messages = await self.message_handler.check_messages(limit=50)
            for msg in messages:
                await self.handle_message(msg)
            
            # Execute pending tasks
            tasks = await self._get_pending_tasks()
            for task in tasks:
                await self.execute_task(task)
            
            # Sleep until next wake
            await asyncio.sleep(self.wake_interval)

# MessageHandler
async def check_messages(self, limit: int = 10) -> List[Message]:
    """Synchronous polling during wake cycle"""
    messages = []
    
    # Poll all priorities
    for priority in [5, 4, 3, 2, 1]:
        batch = await self._fetch_from_bus(priority, limit=limit)
        messages.extend(batch)
        
        if len(messages) >= limit:
            break
    
    # Process immediately
    for msg in messages:
        await self._process_message(msg)
    
    return messages
```

**Pros**:
- ✅ CPU-efficient (sleeps when idle)
- ✅ Simple lifecycle (no background tasks)
- ✅ Good for periodic work

**Cons**:
- ❌ Higher latency (up to wake_interval)
- ❌ May miss urgent messages if asleep

**Optimization**: Hybrid approach
```python
# Wake on high-priority messages
async def should_wake(self) -> bool:
    # Quick check: any p5 (critical) messages?
    critical = await self.message_handler.peek_critical()
    if critical:
        logger.info("🚨 Waking for critical message")
        return True
    
    # Regular wake schedule
    return self._regular_wake_schedule()
```

---

### Pattern 3: Callback Registration

**Use Case**: Event-driven handlers for specific message types

**Implementation**:
```python
class WowVisionPrime(WAAOOWAgent):
    def _register_message_handlers(self):
        """Register handlers for vision-related messages"""
        
        # Direct registration
        self.message_handler.register(
            topic="github.pr.opened",
            handler=self.on_pr_opened
        )
        self.message_handler.register(
            topic="vision.review.requested",
            handler=self.on_review_requested
        )
        
        # Wildcard patterns
        self.message_handler.register(
            topic="vision.*",
            handler=self.on_vision_event
        )
        
        # Broadcast messages
        self.message_handler.register(
            topic="system.*",
            handler=self.on_system_broadcast
        )
    
    async def on_pr_opened(self, message: Message):
        """Handle PR opened event"""
        pr_number = message.payload.data["pr_number"]
        logger.info(f"🔍 New PR #{pr_number} to review")
        
        # Execute vision review
        result = await self.review_pr(pr_number)
        
        # Send results to content agent
        await self.message_handler.send(
            to="wowcontent_marketing",
            subject=f"Vision review complete: PR #{pr_number}",
            body=f"Reviewed PR, found {len(result.violations)} violations",
            action="review_complete",
            data={"pr_number": pr_number, "result": result.dict()}
        )

# MessageHandler
def register(self, topic_pattern: str, handler: Callable):
    """Register handler for topic"""
    if topic_pattern not in self.handlers:
        self.handlers[topic_pattern] = []
    self.handlers[topic_pattern].append(handler)

async def _process_message(self, message: Message):
    """Route message to registered handlers"""
    topic = message.routing.topic
    
    # Find matching handlers
    matched = self._match_handlers(topic)
    
    if not matched and self.default_handler:
        matched = [self.default_handler]
    
    # Invoke handlers
    for handler in matched:
        try:
            await handler(message)
            self.metrics["messages_processed"] += 1
        except Exception as e:
            logger.error(f"Handler error: {e}")
            await self._handle_failure(message, e)
            self.metrics["messages_failed"] += 1
    
    # Acknowledge processing
    await self.bus.acknowledge(message.message_id)

def _match_handlers(self, topic: str) -> List[Callable]:
    """Match topic to registered patterns"""
    matched = []
    
    for pattern, handlers in self.handlers.items():
        if self._topic_matches(topic, pattern):
            matched.extend(handlers)
    
    return matched

def _topic_matches(self, topic: str, pattern: str) -> bool:
    """Check if topic matches pattern (supports wildcards)"""
    # Exact match
    if topic == pattern:
        return True
    
    # Wildcard match: "vision.*" matches "vision.review.complete"
    if pattern.endswith(".*"):
        prefix = pattern[:-2]
        return topic.startswith(prefix)
    
    # Single-level wildcard: "vision.*.complete"
    # TODO: Implement full wildcard matching
    
    return False
```

**Pros**:
- ✅ Clean separation of concerns
- ✅ Easy to add/remove handlers
- ✅ Type-safe with proper signatures

**Cons**:
- ❌ Requires registration boilerplate
- ❌ Handler discovery not automatic

---

### Pattern 4: Decorator-Based (Advanced)

**Use Case**: Auto-discovery of message handlers

**Implementation**:
```python
def message_handler(topic: str, priority: Optional[str] = None):
    """Decorator to auto-register message handlers"""
    def decorator(func):
        # Mark function with metadata
        func._is_message_handler = True
        func._message_topic = topic
        func._message_priority = priority
        return func
    return decorator

class WowContentMarketing(WAAOOWAgent):
    def __init__(self, ...):
        super().__init__(...)
        self._auto_register_handlers()
    
    def _auto_register_handlers(self):
        """Scan for @message_handler decorated methods"""
        for name in dir(self):
            method = getattr(self, name)
            if callable(method) and getattr(method, "_is_message_handler", False):
                topic = method._message_topic
                self.message_handler.register(topic, method)
                logger.info(f"📝 Registered handler: {name} for {topic}")
    
    @message_handler("vision.handoff.content_needed")
    async def on_content_needed(self, message: Message):
        """Auto-registered handler"""
        logger.info("✍️ Content request received")
        # Generate content...
    
    @message_handler("marketing.*", priority="high")
    async def on_marketing_event(self, message: Message):
        """Auto-registered wildcard handler"""
        pass
```

**Pros**:
- ✅ No registration boilerplate
- ✅ Self-documenting (decorators show intent)
- ✅ Easy discovery (grep for @message_handler)

**Cons**:
- ❌ More magic (harder to debug)
- ❌ Requires reflection/introspection

---

## Request-Response Pattern

**Use Case**: Agent A sends request, waits for Agent B's reply

### Synchronous Wait (with timeout)

```python
# Agent A: Send and wait
async def request_keywords(self, topic: str) -> Dict[str, Any]:
    """Request keyword rankings from SEO agent"""
    
    response = await self.message_handler.send_and_wait(
        to="wowseo_specialist",
        subject=f"Keyword rankings for '{topic}'",
        body=f"Please provide keyword rankings and suggestions for: {topic}",
        action="request_keywords",
        data={"topic": topic},
        timeout=60  # Wait up to 60 seconds
    )
    
    return response.payload.data

# MessageHandler
async def send_and_wait(
    self,
    to: str,
    subject: str,
    body: str,
    action: str,
    data: Dict[str, Any],
    timeout: int = 300
) -> Message:
    """Send message and wait for reply"""
    
    # Generate correlation ID
    correlation_id = f"req_{uuid.uuid4().hex[:8]}"
    reply_channel = f"{self.agent_id}.responses"
    
    # Subscribe to reply channel (if not already)
    await self.bus.subscribe(reply_channel)
    
    # Send request
    msg_id = await self.send(
        to=to,
        subject=subject,
        body=body,
        action=action,
        data=data,
        reply_to=reply_channel,
        correlation_id=correlation_id
    )
    
    # Track state
    self.outbox[msg_id] = MessageState(
        message_id=msg_id,
        correlation_id=correlation_id,
        state="pending_reply",
        sent_at=datetime.now(),
        timeout_at=datetime.now() + timedelta(seconds=timeout)
    )
    
    # Wait for reply
    start = time.time()
    while time.time() - start < timeout:
        # Check for reply with matching correlation_id
        reply = await self._check_reply(correlation_id)
        if reply:
            self.outbox[msg_id].state = "completed"
            return reply
        
        await asyncio.sleep(0.5)  # Poll every 500ms
    
    # Timeout
    self.outbox[msg_id].state = "timeout"
    raise TimeoutError(f"No reply from {to} after {timeout}s")

async def _check_reply(self, correlation_id: str) -> Optional[Message]:
    """Check if reply with correlation_id received"""
    # Scan inbox for matching correlation_id
    for msg in list(self.inbox.queue):
        if msg.routing.correlation_id == correlation_id:
            self.inbox.queue.remove(msg)
            return msg
    return None
```

### Async Callback (non-blocking)

```python
# Agent A: Send with callback
async def request_keywords_async(self, topic: str):
    """Request keywords, continue work, callback when reply arrives"""
    
    await self.message_handler.send(
        to="wowseo_specialist",
        subject=f"Keyword rankings for '{topic}'",
        body=f"Please provide rankings for: {topic}",
        action="request_keywords",
        data={"topic": topic},
        reply_to=f"{self.agent_id}.responses",
        correlation_id="req_keywords_001"
    )
    
    # Register callback for reply
    self.message_handler.register_reply_handler(
        correlation_id="req_keywords_001",
        handler=self.on_keywords_received
    )
    
    # Continue other work...
    logger.info("⏳ Keyword request sent, continuing work...")

async def on_keywords_received(self, reply: Message):
    """Called when reply arrives"""
    keywords = reply.payload.data.get("keywords", [])
    logger.info(f"✅ Received {len(keywords)} keywords")
    # Use keywords...
```

---

## Priority Queue Implementation

```python
import heapq
from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class PrioritizedMessage:
    priority: int
    message: Any = field(compare=False)
    timestamp: float = field(compare=False)

class PriorityQueue:
    """Priority queue for messages (high priority = low number)"""
    
    def __init__(self):
        self._queue = []
        self._counter = 0
    
    def put(self, message: Message):
        """Add message to queue"""
        # Priority 5 (critical) = 0, Priority 1 (background) = 4
        priority = 5 - message.payload.priority
        
        # Use counter for FIFO within same priority
        item = PrioritizedMessage(
            priority=priority,
            message=message,
            timestamp=time.time()
        )
        heapq.heappush(self._queue, item)
        self._counter += 1
    
    def get(self) -> Optional[Message]:
        """Get highest priority message"""
        if self._queue:
            item = heapq.heappop(self._queue)
            return item.message
        return None
    
    def peek(self) -> Optional[Message]:
        """Look at highest priority without removing"""
        if self._queue:
            return self._queue[0].message
        return None
    
    def size(self) -> int:
        return len(self._queue)
    
    def is_empty(self) -> bool:
        return len(self._queue) == 0
```

---

## Integration with Base Agent

### Add to base_agent.py

```python
class WAAOOWAgent:
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        # ... existing init ...
        
        # Initialize message handler
        self.message_handler = MessageHandler(
            agent_id=self.agent_id,
            message_bus=MessageBus(config),
            agent=self,
            config=config.get("messaging", {})
        )
        
        # Register default handlers (can be overridden)
        self._register_default_message_handlers()
    
    def _register_default_message_handlers(self):
        """Register default handlers (subclasses can override)"""
        # System broadcasts
        self.message_handler.register("system.shutdown", self.on_shutdown)
        self.message_handler.register("system.pause", self.on_pause)
        self.message_handler.register("system.resume", self.on_resume)
        
        # Health checks
        self.message_handler.register("system.health_check", self.on_health_check)
    
    # ========================================================================
    # DIMENSION 7: COMMUNICATION PROTOCOL (Updated with real implementation)
    # ========================================================================
    
    async def send_message(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        action: str,
        data: Optional[Dict[str, Any]] = None,
        priority: int = 3,
        expected_outcome: Optional[str] = None
    ) -> str:
        """
        Send message to another agent(s).
        
        Args:
            to: Agent ID or list of IDs, or "*" for broadcast
            subject: Human-readable message summary
            body: Detailed message content
            action: Verb (e.g., "task_assigned", "review_complete")
            data: Structured payload
            priority: 1-5 scale (5 = critical, 1 = background)
            expected_outcome: What sender expects (optional)
        
        Returns:
            message_id: Confirmation that message sent
        """
        return await self.message_handler.send(
            to=to,
            subject=subject,
            body=body,
            action=action,
            data=data or {},
            priority=priority,
            expected_outcome=expected_outcome
        )
    
    async def receive_message(self, limit: int = 10) -> List[Message]:
        """
        Poll and process messages (for wake-sleep agents).
        
        Args:
            limit: Max messages to fetch
            
        Returns:
            List of messages processed
        """
        return await self.message_handler.check_messages(limit=limit)
    
    def subscribe_to_channel(self, topic: str, handler: Callable):
        """
        Subscribe to message topic with handler.
        
        Args:
            topic: Topic pattern (e.g., "vision.*", "marketing.campaign.*")
            handler: Async function to call when message arrives
        """
        self.message_handler.register(topic, handler)
    
    # Default message handlers
    async def on_shutdown(self, message: Message):
        """Handle shutdown broadcast"""
        logger.warning("🛑 Shutdown requested")
        await self.pause()
    
    async def on_pause(self, message: Message):
        """Handle pause request"""
        logger.info("⏸️ Pause requested")
        await self.pause()
    
    async def on_resume(self, message: Message):
        """Handle resume request"""
        logger.info("▶️ Resume requested")
        await self.resume()
    
    async def on_health_check(self, message: Message):
        """Respond to health check"""
        health = await self.get_health_status()
        await self.message_handler.reply(
            original_message=message,
            subject="Health check response",
            body=f"Status: {health['status']}",
            data=health
        )
```

---

## Configuration

### agent_config.yaml

```yaml
messaging:
  enabled: true
  
  # Message handler mode
  mode: "wake_sleep"  # Options: "always_on", "wake_sleep", "hybrid"
  
  # Polling configuration
  poll_interval: 5  # seconds (for always_on mode)
  wake_interval: 60  # seconds (for wake_sleep mode)
  
  # Priority configuration
  priority_weights:
    5: 10  # Critical: poll 10x more often
    4: 5   # High: poll 5x more often
    3: 1   # Normal: baseline
    2: 0.5 # Low: poll half as often
    1: 0.1 # Background: poll 1/10th as often
  
  # Batch sizes
  batch_size:
    critical: 50  # Process up to 50 critical messages
    high: 20
    normal: 10
    low: 5
    background: 1
  
  # Timeouts
  request_timeout: 300  # 5 minutes for send_and_wait()
  handler_timeout: 60   # 1 minute per handler execution
  
  # Retry configuration
  max_retries: 3
  retry_delay: 60  # seconds
  
  # Agent-specific subscriptions
  subscriptions:
    wowvision_prime:
      - "github.pr.opened"
      - "github.pr.updated"
      - "vision.*"
      - "system.*"
    
    wowcontent_marketing:
      - "vision.handoff.content_needed"
      - "marketing.*"
      - "content.*"
      - "system.*"
    
    # ... (all 14 agents)
```

---

## Implementation Checklist

### Phase 1: Core MessageHandler (Week 1, Days 1-2)
- [ ] Create `waooaw/messaging/message_handler.py`
- [ ] Implement `MessageHandler` class
  - [ ] `send()`, `broadcast()`, `reply()`
  - [ ] `register()`, `_match_handlers()`
  - [ ] `check_messages()` (sync polling)
- [ ] Implement `PriorityQueue` class
- [ ] Implement `MessageState` tracking
- [ ] Unit tests for handler registration

### Phase 2: Async Loop (Week 1, Day 3)
- [ ] Implement `start()` / `stop()` lifecycle
- [ ] Implement `_message_loop()` background task
- [ ] Implement priority-weighted polling
- [ ] Test: background message processing

### Phase 3: Request-Response (Week 1, Day 4)
- [ ] Implement `send_and_wait()`
- [ ] Implement reply tracking (correlation IDs)
- [ ] Implement timeout handling
- [ ] Test: request-response pattern

### Phase 4: Base Agent Integration (Week 1, Day 5)
- [ ] Update `base_agent.py`:
  - [ ] Add `self.message_handler` to `__init__()`
  - [ ] Replace stubs: `send_message()`, `receive_message()`, `subscribe_to_channel()`
  - [ ] Add `_register_default_message_handlers()`
  - [ ] Add default handlers: shutdown, pause, resume, health_check
- [ ] Update `agent_config.yaml` with messaging config
- [ ] Test: base agent can send/receive messages

### Phase 5: Pattern Examples (Week 2, Day 1)
- [ ] Example: Always-on coordinator agent
- [ ] Example: Wake-sleep specialist agent
- [ ] Example: Callback-based reactive agent
- [ ] Test: all patterns working

### Phase 6: Advanced Features (Week 2, Days 2-3)
- [ ] Decorator pattern: `@message_handler()`
- [ ] Wildcard matching: `vision.*`, `system.*`
- [ ] Message filtering in inbox
- [ ] Metrics collection (sent, received, processed, failed)
- [ ] Test: advanced features

### Phase 7: Documentation & Testing (Week 2, Days 4-5)
- [ ] Integration tests (agent-to-agent)
- [ ] Load tests (1000 messages/sec)
- [ ] Document usage patterns
- [ ] Create troubleshooting guide

---

## Usage Examples

### Example 1: WowVision Reviews PR, Hands Off to Content

```python
class WowVisionPrime(WAAOOWAgent):
    def _register_message_handlers(self):
        """Register vision-specific handlers"""
        self.subscribe_to_channel("github.pr.opened", self.on_pr_opened)
    
    async def on_pr_opened(self, message: Message):
        """New PR opened - review for vision compliance"""
        pr_number = message.payload.data["pr_number"]
        
        # Execute vision review
        result = await self.review_pr(pr_number)
        
        if result.has_violations():
            # Send to content agent for fixes
            await self.send_message(
                to="wowcontent_marketing",
                subject=f"Content needed for PR #{pr_number}",
                body=f"Found {len(result.violations)} vision violations",
                action="handoff_content_needed",
                data={
                    "pr_number": pr_number,
                    "violations": [v.dict() for v in result.violations]
                },
                priority=4,  # High priority
                expected_outcome="create_content"
            )
            
            logger.info(f"✅ Handed off PR #{pr_number} to content agent")

class WowContentMarketing(WAAOOWAgent):
    def _register_message_handlers(self):
        """Register content-specific handlers"""
        self.subscribe_to_channel("vision.handoff.content_needed", self.on_content_needed)
    
    async def on_content_needed(self, message: Message):
        """Vision agent needs content"""
        pr_number = message.payload.data["pr_number"]
        violations = message.payload.data["violations"]
        
        logger.info(f"✍️ Generating content for PR #{pr_number}")
        
        # Generate content
        content = await self.generate_content(violations)
        
        # Reply to vision agent
        await self.message_handler.reply(
            original_message=message,
            subject=f"Content ready for PR #{pr_number}",
            body=f"Generated {len(content)} content pieces",
            data={"pr_number": pr_number, "content": content}
        )
```

### Example 2: Coordinator Broadcasts Maintenance

```python
class CoordinatorAgent(WAAOOWAgent):
    async def schedule_maintenance(self, starts_at: datetime, duration_minutes: int):
        """Notify all agents of scheduled maintenance"""
        
        # Broadcast to all agents
        await self.message_handler.broadcast(
            subject="Scheduled maintenance",
            body=f"Maintenance starting at {starts_at}, duration {duration_minutes} min",
            action="maintenance_warning",
            data={
                "starts_at": starts_at.isoformat(),
                "duration_minutes": duration_minutes,
                "action_required": "pause_and_checkpoint"
            },
            priority=5  # Critical
        )
        
        logger.info(f"📢 Maintenance broadcast sent to all agents")

# All agents receive broadcast
class WowVisionPrime(WAAOOWAgent):
    def _register_message_handlers(self):
        self.subscribe_to_channel("system.*", self.on_system_broadcast)
    
    async def on_system_broadcast(self, message: Message):
        """Handle system broadcasts"""
        action = message.payload.action
        
        if action == "maintenance_warning":
            starts_at = datetime.fromisoformat(message.payload.data["starts_at"])
            
            # Checkpoint current work
            await self.checkpoint_state()
            
            # Pause before maintenance
            wait_seconds = (starts_at - datetime.now()).total_seconds()
            await asyncio.sleep(max(0, wait_seconds))
            await self.pause()
```

### Example 3: Request-Response (Sync)

```python
class WowContentMarketing(WAAOOWAgent):
    async def create_blog_post(self, topic: str):
        """Create blog post, request keywords from SEO agent"""
        
        # Request keywords (wait for reply)
        keywords = await self.request_keywords_from_seo(topic)
        
        # Use keywords to create content
        content = await self.generate_content(topic, keywords)
        
        return content
    
    async def request_keywords_from_seo(self, topic: str) -> List[str]:
        """Request keyword recommendations from SEO agent"""
        
        response = await self.message_handler.send_and_wait(
            to="wowseo_specialist",
            subject=f"Keyword recommendations for '{topic}'",
            body=f"Planning blog post on: {topic}. Need keyword suggestions.",
            action="request_keywords",
            data={"topic": topic, "target_region": "US"},
            timeout=60  # Wait up to 60 seconds
        )
        
        return response.payload.data.get("keywords", [])

class WowSEOSpecialist(WAAOOWAgent):
    def _register_message_handlers(self):
        self.subscribe_to_channel("seo.request_keywords", self.on_keywords_requested)
    
    async def on_keywords_requested(self, message: Message):
        """Provide keyword recommendations"""
        topic = message.payload.data["topic"]
        
        # Fetch keywords from SEO tools
        keywords = await self.get_keyword_recommendations(topic)
        
        # Reply with keywords
        await self.message_handler.reply(
            original_message=message,
            subject=f"Keyword recommendations for '{topic}'",
            body=f"Found {len(keywords)} relevant keywords",
            data={"keywords": keywords}
        )
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_message_handler.py
import pytest
from waooaw.messaging.message_handler import MessageHandler

@pytest.mark.asyncio
async def test_send_message():
    """Test sending message"""
    handler = MessageHandler(agent_id="test", message_bus=mock_bus, agent=mock_agent)
    
    msg_id = await handler.send(
        to="target_agent",
        subject="Test",
        body="Hello",
        action="test",
        data={}
    )
    
    assert msg_id is not None
    assert handler.metrics["messages_sent"] == 1

@pytest.mark.asyncio
async def test_register_and_match_handler():
    """Test handler registration and matching"""
    handler = MessageHandler(...)
    
    # Register handler
    async def my_handler(msg):
        pass
    
    handler.register("vision.*", my_handler)
    
    # Match
    matched = handler._match_handlers("vision.review.complete")
    assert len(matched) == 1
    assert matched[0] == my_handler

@pytest.mark.asyncio
async def test_priority_queue():
    """Test priority queue ordering"""
    queue = PriorityQueue()
    
    # Add messages with different priorities
    msg_low = Message(payload=MessagePayload(priority=1, ...))
    msg_high = Message(payload=MessagePayload(priority=5, ...))
    msg_normal = Message(payload=MessagePayload(priority=3, ...))
    
    queue.put(msg_low)
    queue.put(msg_high)
    queue.put(msg_normal)
    
    # Should dequeue in priority order: high, normal, low
    assert queue.get() == msg_high
    assert queue.get() == msg_normal
    assert queue.get() == msg_low
```

### Integration Tests

```python
# tests/test_agent_messaging.py
@pytest.mark.asyncio
async def test_vision_to_content_handoff():
    """Test message handoff between agents"""
    
    # Setup agents
    vision = WowVisionPrime(...)
    content = WowContentMarketing(...)
    
    # Vision sends message
    await vision.send_message(
        to="wowcontent_marketing",
        subject="Need content",
        action="handoff_content_needed",
        data={"pr_number": 42}
    )
    
    # Content receives and processes
    messages = await content.receive_message()
    assert len(messages) == 1
    assert messages[0].payload.action == "handoff_content_needed"

@pytest.mark.asyncio
async def test_request_response_pattern():
    """Test request-response flow"""
    
    # Agent A requests
    content = WowContentMarketing(...)
    
    # Agent B responds (simulated)
    seo = WowSEOSpecialist(...)
    seo.message_handler.start()  # Start background loop
    
    # Send request
    response = await content.message_handler.send_and_wait(
        to="wowseo_specialist",
        subject="Keywords?",
        action="request_keywords",
        data={"topic": "AI agents"},
        timeout=10
    )
    
    assert response is not None
    assert "keywords" in response.payload.data
```

---

## Summary

| Aspect | Design Decision |
|--------|-----------------|
| **Architecture** | Separate `MessageHandler` component (composition) |
| **Patterns** | Hybrid: async loop + sync polling + callbacks |
| **Registration** | Manual + decorator pattern |
| **Priority** | Priority queue + weighted polling |
| **Request-Response** | Correlation IDs + reply channels + timeouts |
| **State Tracking** | In-memory + optional DB persistence |
| **Integration** | Tight integration with `base_agent.py` |
| **Configuration** | `agent_config.yaml` + `.env` |
| **Testing** | Unit + integration + load tests |
| **LOC** | ~600 lines (message_handler.py) |

---

## Integration with Orchestration Layer

**Related Document**: [ORCHESTRATION_LAYER_DESIGN.md](./ORCHESTRATION_LAYER_DESIGN.md)

### Workflow-Aware Message Handling

When agents execute within workflows, message handlers must understand workflow context:

```python
class MessageHandler:
    """Enhanced with workflow context awareness"""
    
    async def process_message(self, message: Message):
        """Process message with optional workflow context"""
        
        # Check if message is from workflow
        workflow_context = message.metadata.get("workflow_context")
        
        if workflow_context:
            # Load workflow instance
            instance_id = message.metadata["workflow_instance_id"]
            workflow_instance = await self._load_workflow_instance(instance_id)
            
            # Set agent's workflow context
            self.agent.workflow_instance = workflow_instance
        
        # Execute handler
        handler = self._get_handler(message.topic)
        result = await handler(message)
        
        # If workflow context, send response to workflow
        if workflow_context:
            reply_to = message.metadata.get("reply_to")
            if reply_to:
                await self.message_bus.publish(Message(
                    topic=reply_to,
                    data={
                        "task_id": message.data["task_id"],
                        "status": "completed",
                        "result": result
                    }
                ))
```

### Workflow Task Message Pattern

**When orchestration layer assigns task to agent:**

```python
# Message structure for workflow tasks
{
  "topic": "agent.wowvision.task.validate",
  "data": {
    "workflow_instance_id": "uuid-123",
    "task_id": "wowvision_validate",
    "task_type": "service_task",
    "input_variables": {
      "pr_number": 42,
      "files_changed": ["app.py", "config.yaml"]
    },
    "output_variables": ["vision_approved", "violations"]
  },
  "metadata": {
    "workflow_context": true,
    "reply_to": "workflow.uuid-123.responses",
    "correlation_id": "task-wowvision-validate-001",
    "timeout_seconds": 120
  }
}
```

**Agent handler for workflow tasks:**

```python
@agent.on_message("agent.{agent_id}.task.*")
async def handle_workflow_task(message: Message):
    """Handle task assigned by orchestration layer"""
    
    # Extract workflow context
    instance_id = message.data["workflow_instance_id"]
    task_id = message.data["task_id"]
    inputs = message.data["input_variables"]
    
    # Execute agent logic
    result = await agent.execute_as_service_task(inputs)
    
    # Extract requested output variables
    outputs = {
        var: result[var] 
        for var in message.data["output_variables"]
        if var in result
    }
    
    # Send response back to workflow
    await agent.message_bus.publish(Message(
        topic=message.metadata["reply_to"],
        data={
            "task_id": task_id,
            "status": "completed",
            "result": outputs,
            "execution_metadata": {
                "duration_ms": result.get("duration_ms"),
                "cost": result.get("cost"),
                "method": result.get("method")  # deterministic/cached/llm
            }
        },
        metadata={
            "correlation_id": message.metadata["correlation_id"]
        }
    ))
```

### Benefits

✅ **Agents don't need to know about workflows** - they just respond to messages  
✅ **Orchestration layer controls flow** - agents are stateless workers  
✅ **Reusable handlers** - same handler works standalone or in workflow  
✅ **Transparent integration** - add `workflow_context` flag, handler adapts

---

## Next Steps

1. **Review this design** with team/user
2. **Start implementation** (Phase 1: Core MessageHandler)
3. **Add workflow context support** (Phase 2)
4. **Test with WowVision** (first real use case)
5. **Update base_agent.py** (replace stubs)
6. **Document usage patterns** (for agent developers)

**Ready to implement?** This design gives agents full nervous system integration + workflow orchestration! 🧠⚡🔄

---

**Document Status**: ✅ Design Complete (Updated for Orchestration Integration)  
**Next Action**: User approval → Begin implementation  
**Estimated Time**: 1.5 weeks (MessageHandler + base agent integration)  
**Related**: See ORCHESTRATION_LAYER_DESIGN.md for workflow patterns
