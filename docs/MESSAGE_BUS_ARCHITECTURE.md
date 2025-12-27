# Message Bus Architecture for WAOOAW Agent Network

**Version**: 1.0  
**Date**: December 27, 2025  
**Status**: Design Complete → Implementation Ready

---

## Executive Summary

The Message Bus is the **nervous system** of the WAOOAW agent network, enabling all 14 Centers of Excellence (CoEs) to communicate, collaborate, and coordinate autonomously. This document defines the complete architecture for a Redis Streams-based message infrastructure.

### Key Design Decisions

| Requirement | Solution | Rationale |
|------------|----------|-----------|
| **Delivery** | At-least-once with ACK | Reliability without complexity |
| **Persistence** | 2+ years (configurable) | Audit compliance, replay capability |
| **Response** | Async fire-and-watch | Non-blocking, event-driven |
| **Priority** | 1-5 scale, 5 streams | Sender-controlled urgency |
| **Scale** | 10K msg/day, 1K burst/sec | Redis handles 100K+ easily |
| **Cost** | $0 (existing Redis) | Already in infrastructure |
| **Audit** | Separate PostgreSQL store | Independent compliance trail |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     WAOOAW Message Bus Layer                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐│
│  │  Agent A     │─────────│  Message Bus │─────────│  Agent B     ││
│  │ (WowVision)  │ publish │  (Redis)     │subscribe│ (WowContent) ││
│  └──────────────┘         └──────────────┘         └──────────────┘│
│         │                        │                        │         │
│         │                        │                        │         │
│         └────────────────────────┼────────────────────────┘         │
│                                  │                                  │
│                                  ▼                                  │
│                         ┌────────────────┐                          │
│                         │  Audit Trail   │                          │
│                         │  (PostgreSQL)  │                          │
│                         └────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Message Bus (Redis Streams)

**Technology**: Redis 7+ with Streams data structure  
**Location**: `waooaw/messaging/message_bus.py`

**Redis Streams Architecture**:
```
Redis
├── waooaw:messages:p5    (Priority 5 - Critical/Urgent)
├── waooaw:messages:p4    (Priority 4 - High)
├── waooaw:messages:p3    (Priority 3 - Normal) ← Default
├── waooaw:messages:p2    (Priority 2 - Low)
├── waooaw:messages:p1    (Priority 1 - Background)
├── waooaw:topics:*       (Topic-based routing)
├── waooaw:broadcast      (All agents)
└── waooaw:dlq            (Dead letter queue)
```

**Consumer Groups**:
- Each agent type has a consumer group (e.g., `cg_wowvision`)
- Multiple instances of same agent share load (e.g., `wowvision_001`, `wowvision_002`)
- Pending entries list ensures at-least-once delivery
- Acknowledgment (XACK) confirms processing

**Key Features**:
- **Persistence**: XADD with MAXLEN ~10M messages (auto-trim old)
- **Replay**: XREAD from any message ID (timestamp-based)
- **At-least-once**: Consumer groups + pending entries + XACK
- **Acknowledgment**: Sender gets stream ID as confirmation
- **Priority**: 5 separate streams for priority levels
- **TTL**: Message metadata includes expiry, cleanup via background job

---

### 2. Message Schema

**Format**: JSON (validated with Pydantic)  
**Location**: `waooaw/messaging/models.py`

```python
class Message(BaseModel):
    """
    Standard message format for agent communication.
    """
    # Identity
    message_id: str  # msg_{timestamp}_{uuid}
    version: str = "1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Routing
    routing: MessageRouting
    
    # Content
    payload: MessagePayload
    
    # Metadata
    metadata: MessageMetadata
    
    # Audit
    audit: AuditInfo

class MessageRouting(BaseModel):
    from_agent: str  # Agent ID (e.g., "wowvision_prime")
    to_agents: List[str]  # ["agent_id"] or ["*"] for broadcast
    topic: str  # Hierarchical: "vision.review.complete"
    reply_to: Optional[str]  # Channel for responses
    correlation_id: Optional[str]  # For request-response pairing

class MessagePayload(BaseModel):
    subject: str  # Human-readable summary
    body: str  # Detailed message content
    action: str  # Verb (e.g., "review_complete", "task_assigned")
    expected_outcome: Optional[str]  # What sender expects
    priority: int = 3  # 1-5 scale (5 = urgent)
    data: Dict[str, Any]  # Structured payload

class MessageMetadata(BaseModel):
    ttl: int = 86400  # Time to live (seconds)
    retry_count: int = 0
    max_retries: int = 3
    idempotency_key: str  # Unique operation ID
    tags: List[str] = []  # For filtering/categorization

class AuditInfo(BaseModel):
    sender_version: str  # Agent version (e.g., "v0.2.0")
    sender_instance_id: str  # Instance ID (e.g., "wowvision_001")
    trace_id: str  # Distributed tracing
    span_id: str  # Current span
```

**Example Message**:
```json
{
  "message_id": "msg_20251227_103045_a1b2c3d4",
  "version": "1.0",
  "timestamp": "2025-12-27T10:30:45.123Z",
  
  "routing": {
    "from_agent": "wowvision_prime",
    "to_agents": ["wowcontent_marketing"],
    "topic": "vision.review.complete",
    "reply_to": "wowvision_prime.responses",
    "correlation_id": "req_pr42_review"
  },
  
  "payload": {
    "subject": "Vision review complete for PR #42",
    "body": "Reviewed 15 files across 3 components. Found 3 vision violations requiring attention.",
    "action": "review_complete",
    "expected_outcome": "create_issue",
    "priority": 4,
    "data": {
      "pr_number": 42,
      "files_reviewed": 15,
      "violations": [
        {
          "file": "frontend/index.html",
          "line": 234,
          "severity": "high",
          "message": "Logo not using brand gradient"
        }
      ]
    }
  },
  
  "metadata": {
    "ttl": 86400,
    "retry_count": 0,
    "max_retries": 3,
    "idempotency_key": "vision_review_pr42_attempt1",
    "tags": ["vision", "pr_review", "quality_gate"]
  },
  
  "audit": {
    "sender_version": "v0.2.0",
    "sender_instance_id": "wowvision_001",
    "trace_id": "trace_abc123def456",
    "span_id": "span_xyz789"
  }
}
```

---

### 3. Message Routing Patterns

**Pattern 1: Point-to-Point (Direct)**
```
WowVision → WowContent
Topic: "vision.handoff.content_needed"
Use case: Vision agent identifies missing content, assigns to content agent
```

**Pattern 2: Broadcast (All Agents)**
```
Coordinator → All Agents (*)
Topic: "system.shutdown.graceful"
Use case: System maintenance notification
```

**Pattern 3: Topic-Based (Pub/Sub)**
```
Any Agent → Topic "marketing.*"
Subscribers: WowContent, WowSEO, WowSocial, etc.
Topic: "marketing.campaign.launched"
Use case: New campaign announced, all marketing agents react
```

**Pattern 4: Request-Response (Async)**
```
WowVision → WowSEO
Request: "Get keyword rankings for 'AI agent marketplace'"
Reply-to: "wowvision_prime.responses"
Correlation-id: "req_keywords_001"

WowSEO → WowVision (reply)
Correlation-id: "req_keywords_001"
Data: {rankings: [...]}
```

**Pattern 5: Self-Messaging (State Tracking)**
```
WowVision → WowVision
Topic: "wowvision.state.checkpoint"
Use case: Agent saves progress for resume after crash
```

---

### 4. Priority Handling

**Priority Levels**:
- **5 - Critical**: System errors, security alerts (process immediately)
- **4 - High**: Urgent tasks, customer-facing issues (process within minutes)
- **3 - Normal**: Regular tasks, collaborations (default, process within hours)
- **2 - Low**: Background processing, non-urgent updates (process within days)
- **1 - Background**: Analytics, cleanup, maintenance (process when idle)

**Implementation**:
- 5 separate Redis streams (one per priority)
- Agents poll in priority order: p5 → p4 → p3 → p2 → p1
- High-priority messages processed first, even if normal queue has backlog

**Example**:
```python
# Agent polling logic
async def fetch_messages(agent_id: str):
    for priority in [5, 4, 3, 2, 1]:
        messages = await bus.read(
            stream=f"waooaw:messages:p{priority}",
            consumer_group=f"cg_{agent_id}",
            consumer_name=agent_id,
            count=10
        )
        if messages:
            return messages  # Process high-priority first
    return []  # No messages
```

---

### 5. Delivery Guarantees (At-Least-Once)

**How It Works**:

1. **Sender Publishes**:
   - `XADD waooaw:messages:p3 * message {json}`
   - Redis returns stream ID: `1735297845123-0`
   - Stream ID is **confirmation** that message is persisted

2. **Receiver Reads**:
   - `XREADGROUP GROUP cg_wowcontent wowcontent_001 STREAMS waooaw:messages:p3 >`
   - Message added to **Pending Entries List (PEL)** for `wowcontent_001`

3. **Receiver Processes**:
   - Agent processes message
   - If successful: `XACK waooaw:messages:p3 cg_wowcontent {message_id}`
   - Message removed from PEL

4. **Failure Handling**:
   - If agent crashes before XACK, message stays in PEL
   - Another instance can claim via `XCLAIM` after timeout (e.g., 5 minutes)
   - After max retries (3), move to Dead Letter Queue (DLQ)

**Idempotency**:
- Each message has `idempotency_key` in metadata
- Receivers check: "Have I processed this key before?"
- Prevents duplicate execution if message delivered multiple times

---

### 6. Message Persistence & Retention

**Retention Policy**:
- **Default**: 2 years (configurable via `MESSAGE_RETENTION_DAYS`)
- **Implementation**: Redis MAXLEN with approximate trimming
- **Calculation**: 10K msg/day × 730 days = 7.3M messages (~2GB for 2 years)

**Configuration**:
```python
# .env or config.yaml
MESSAGE_RETENTION_DAYS=730  # 2 years
MESSAGE_MAX_LENGTH=10000000  # ~10M messages max in stream
MESSAGE_TRIM_STRATEGY="~"  # Approximate trimming (faster)
```

**Replay Capability**:
```python
# Read from specific time (e.g., 7 days ago)
timestamp = datetime.utcnow() - timedelta(days=7)
message_id = f"{int(timestamp.timestamp() * 1000)}-0"

messages = await bus.read(
    stream="waooaw:messages:p3",
    start_id=message_id,
    count=1000
)
```

**Archival** (for compliance):
- Background job runs daily
- Copies messages older than 30 days from Redis → PostgreSQL `message_archive` table
- Redis trimmed, but full history in PostgreSQL for 2+ years

---

### 7. Audit Trail (Separate Component)

**Why Separate**:
- Compliance requirement (GDPR, SOC2)
- Different retention rules (7 years for audit vs 2 years for messages)
- Query patterns differ (audit = historical search, messages = real-time)

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                     Audit Trail Service                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Message Bus → Audit Listener (async) → PostgreSQL         │
│                                                             │
│  Table: audit_log                                           │
│  - audit_id (PK)                                            │
│  - message_id (indexed)                                     │
│  - timestamp                                                │
│  - event_type (message_sent, message_received, etc.)       │
│  - agent_id                                                 │
│  - topic                                                    │
│  - payload_summary (not full payload, for privacy)         │
│  - trace_id (for distributed tracing)                      │
│  - metadata (JSONB)                                         │
│                                                             │
│  Retention: 7 years (compliance default)                   │
│  Query API: GET /audit/messages?agent_id=X&from=Y&to=Z     │
└─────────────────────────────────────────────────────────────┘
```

**Implementation**:
- `AuditTrailService` subscribes to `waooaw:audit` topic
- Every message sent/received publishes audit event
- Async write to PostgreSQL (doesn't block agent)
- Separate retention policy (7 years for compliance)

**Location**: `waooaw/audit/trail_service.py`

---

### 8. Dead Letter Queue (DLQ)

**Purpose**: Store messages that fail processing after max retries

**Flow**:
1. Message fails processing (exception raised)
2. Retry count incremented (retry_count < max_retries)
3. Re-publish to same stream with updated retry_count
4. After 3 failures → Move to `waooaw:dlq`
5. Alert sent to monitoring (Slack/email)
6. Human reviews DLQ periodically, can replay manually

**DLQ Message Schema**:
```json
{
  "original_message": {...},
  "failure_info": {
    "attempts": 3,
    "last_error": "ValueError: Invalid PR number",
    "failed_at": "2025-12-27T12:00:00Z",
    "failed_by": "wowcontent_001"
  },
  "actions": {
    "can_retry": true,
    "requires_fix": "Update PR validation logic"
  }
}
```

---

## Message Flow Examples

### Example 1: PR Opened → Multi-Agent Collaboration

```
Timeline: PR #42 opened by user

1. GitHub Webhook → EventBus
   - Topic: "github.pr.opened"
   - Priority: 3 (Normal)
   - Data: {pr_number: 42, files: [...]}

2. WowVision wakes (should_wake() returns True)
   - Reads message from stream
   - Processes: Reviews files for vision compliance
   
3. WowVision → WowContent (Direct)
   - Topic: "vision.handoff.content_needed"
   - Priority: 4 (High)
   - Expected outcome: "create_blog_post"
   - Data: {pr_number: 42, missing_content: ["SEO metadata"]}
   
4. WowContent wakes
   - Reads message
   - Generates content
   
5. WowContent → WowVision (Reply)
   - Topic: "content.delivery.complete"
   - Correlation ID: links to original request
   - Priority: 3 (Normal)
   - Data: {content_url: "..."}
   
6. WowVision → GitHub (Output)
   - Creates issue #43 "Vision review complete"
   - Comments on PR #42 with results
```

**Message Count**: 4 messages  
**Agents Involved**: 2 (WowVision, WowContent)  
**Time**: ~2-5 minutes end-to-end

---

### Example 2: System Maintenance (Broadcast)

```
Timeline: Scheduled maintenance in 10 minutes

1. Coordinator → All Agents (Broadcast)
   - Topic: "system.maintenance.warning"
   - Priority: 5 (Critical)
   - To: ["*"]
   - Data: {
       starts_at: "2025-12-27T14:00:00Z",
       duration_minutes: 15,
       action_required: "pause_and_checkpoint"
     }

2. All 14 agents receive message
   - Each agent: pause(), save state, stop processing

3. Coordinator → All Agents (after maintenance)
   - Topic: "system.maintenance.complete"
   - Priority: 5 (Critical)
   - To: ["*"]
   
4. All agents: resume()
```

**Message Count**: 2 messages × 14 agents = 28 reads  
**Time**: <1 second to broadcast

---

### Example 3: Self-Messaging (Checkpointing)

```
Timeline: WowVision processing long task

1. WowVision reviews 100 PRs (long task)
   
2. After every 10 PRs, self-message:
   - From: "wowvision_prime"
   - To: ["wowvision_prime"]
   - Topic: "wowvision.checkpoint"
   - Priority: 2 (Low)
   - Data: {
       task_id: "review_batch_001",
       progress: 10/100,
       last_processed_pr: 42,
       state: {...}
     }

3. If crash occurs:
   - On resume, WowVision reads own checkpoint messages
   - Resumes from PR #43 (last checkpoint + 1)
   - No work lost
```

**Message Count**: 10 checkpoints for 100 PRs  
**Purpose**: Fault tolerance, resume capability

---

## Redis Implementation Details

### Current Redis Setup Verification

**Location**: `infrastructure/docker/docker-compose.yml`

**Current Configuration**:
```yaml
redis:
  image: redis:7-alpine
  container_name: waooaw-redis
  ports:
    - "6379:6379"
  volumes:
    - redis-data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 3s
    retries: 5
  networks:
    - waooaw-network
```

**Verification Results**:

| Aspect | Current Status | Gap | Required Action |
|--------|----------------|-----|-----------------|
| **Image** | ✅ redis:7-alpine | None | Redis 7+ supports Streams |
| **Volume Mount** | ✅ redis-data:/data | None | Persistence directory configured |
| **Persistence Mode** | ⚠️ Not specified | **RDB/AOF not configured** | Add command or config file |
| **Memory Limits** | ❌ Not set | **No memory limit** | Add deploy.resources.limits |
| **Max Memory Policy** | ❌ Default | **No eviction policy** | Configure for message bus workload |
| **Append-Only File** | ❌ Disabled | **No AOF** | Enable for durability |
| **Network** | ✅ waooaw-network | None | Isolated network |
| **Health Check** | ✅ Configured | None | Monitors availability |

**Critical Gaps Identified**:

1. **No Persistence Configuration** ⚠️
   - Current: Redis uses default RDB (saves to disk periodically)
   - Gap: No explicit AOF (Append-Only File) for durability
   - Risk: Messages written after last RDB snapshot lost on crash
   - **Impact**: At-least-once delivery compromised

2. **No Memory Limits** ❌
   - Current: Redis can grow unbounded
   - Gap: No max memory setting
   - Risk: Container OOM kill, message loss
   - **Impact**: System instability under load

3. **No Eviction Policy** ❌
   - Current: Default policy (may evict messages)
   - Gap: No `maxmemory-policy` configured
   - Risk: Old messages evicted prematurely
   - **Impact**: 2-year retention not guaranteed

**Recommended Configuration** (Add to docker-compose.yml):

```yaml
redis:
  image: redis:7-alpine
  container_name: waooaw-redis
  command: >
    redis-server
    --appendonly yes
    --appendfsync everysec
    --maxmemory 2gb
    --maxmemory-policy noeviction
    --save 900 1
    --save 300 10
    --save 60 10000
  ports:
    - "6379:6379"
  volumes:
    - redis-data:/data
  deploy:
    resources:
      limits:
        memory: 2.5gb
      reservations:
        memory: 1gb
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 3s
    retries: 5
  networks:
    - waooaw-network
```

**Configuration Breakdown**:

| Flag | Value | Purpose |
|------|-------|---------|
| `--appendonly yes` | Enable AOF | Every write logged to disk |
| `--appendfsync everysec` | Sync every 1s | Balance durability/performance |
| `--maxmemory 2gb` | 2GB limit | Prevents unbounded growth |
| `--maxmemory-policy noeviction` | Never evict | Preserves all messages (fail write if full) |
| `--save 900 1` | RDB snapshot | After 900s if 1+ key changed |
| `--save 300 10` | RDB snapshot | After 300s if 10+ keys changed |
| `--save 60 10000` | RDB snapshot | After 60s if 10K+ keys changed |

**Alternative: Redis Config File** (Preferred for complex setups):

```yaml
# infrastructure/docker/redis.conf
redis:
  # ... (same as above)
  volumes:
    - redis-data:/data
    - ./redis.conf:/usr/local/etc/redis/redis.conf
  command: redis-server /usr/local/etc/redis/redis.conf
```

**Memory Calculation** (2-year retention):
- Messages: 10K/day × 730 days = 7.3M messages
- Avg size: ~1KB per message (JSON + metadata)
- Total: 7.3GB raw data
- Compressed: ~2-3GB (Redis compression)
- **Recommendation**: 2GB max memory + 500MB buffer = 2.5GB container limit

**Persistence Strategy**:
- **AOF**: Append-Only File for durability (everysec fsync)
- **RDB**: Snapshot backups for fast restarts
- **Both**: Dual persistence for maximum safety

**Failover Plan**:
- If Redis OOM: noeviction policy rejects writes (alerts triggered)
- If Redis crash: AOF + RDB restore messages within seconds
- If container restart: Volume persists data across restarts

**Action Items for Week 1**:
1. Update docker-compose.yml with recommended config
2. Test persistence: Write messages → restart Redis → verify recovery
3. Monitor memory usage: Set alerts at 80% capacity
4. Document backup strategy (AOF + RDB snapshots)

---

### Stream Commands Used

| Operation | Redis Command | Purpose |
|-----------|---------------|---------|
| **Publish** | `XADD stream * field value` | Add message to stream |
| **Read** | `XREADGROUP GROUP cg consumer STREAMS stream >` | Read new messages |
| **Acknowledge** | `XACK stream group message_id` | Confirm processing |
| **Claim** | `XCLAIM stream group consumer min_idle_time id` | Reclaim stale message |
| **Pending** | `XPENDING stream group` | Check unacked messages |
| **Info** | `XINFO STREAM stream` | Get stream metadata |
| **Trim** | `XTRIM stream MAXLEN ~ 10000000` | Limit stream size |

### Consumer Group Setup

```bash
# Create consumer group for each agent type (one-time setup)
redis-cli XGROUP CREATE waooaw:messages:p3 cg_wowvision $ MKSTREAM
redis-cli XGROUP CREATE waooaw:messages:p3 cg_wowcontent $ MKSTREAM
# ... (repeat for all 14 agents)
```

### Performance Tuning

**Batch Reads**:
- Read 10-100 messages per call (reduce roundtrips)
- `XREADGROUP ... COUNT 10`

**Block Reads** (optional):
- `XREADGROUP ... BLOCK 5000` (wait up to 5 seconds)
- Reduces CPU on idle agents

**Pipeline Commands**:
- Publish multiple messages in one roundtrip
- Use Redis pipeline: `XADD` + `XADD` + `XADD` → single network call

**Connection Pool**:
- Reuse Redis connections (don't create per message)
- `redis.asyncio.ConnectionPool` with max 20 connections

---

## Configuration

**Environment Variables** (`.env`):
```bash
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_password_here

# Message Bus
MESSAGE_RETENTION_DAYS=730  # 2 years
MESSAGE_MAX_LENGTH=10000000  # 10M messages
MESSAGE_BATCH_SIZE=10  # Read 10 at a time
MESSAGE_BLOCK_MS=5000  # Block for 5 seconds on read
MESSAGE_MAX_RETRIES=3  # Retry failed messages 3 times
MESSAGE_RETRY_DELAY_S=60  # Wait 60s before retry

# Audit Trail
AUDIT_ENABLED=true
AUDIT_RETENTION_DAYS=2555  # 7 years
AUDIT_ASYNC=true  # Don't block on audit writes

# Monitoring
MESSAGE_BUS_METRICS_ENABLED=true
MESSAGE_BUS_TRACING_ENABLED=true
```

**Agent Config** (`waooaw/config/agent_config.yaml`):
```yaml
messaging:
  enabled: true
  consumer_group_prefix: "cg_"
  consumer_name_template: "{agent_id}_{instance_id}"
  
  # Topics each agent subscribes to
  subscriptions:
    wowvision_prime:
      - "github.pr.opened"
      - "github.pr.updated"
      - "vision.*"
    wowcontent_marketing:
      - "vision.handoff.content_needed"
      - "marketing.*"
      - "content.*"
    # ... (all 14 agents)
  
  # Priority polling order
  priority_order: [5, 4, 3, 2, 1]
  
  # Dead letter queue
  dlq:
    enabled: true
    alert_on_dlq: true
    alert_channels: ["slack", "email"]
```

---

## Cost Analysis

### Redis (Current Setup - Docker)

| Component | Cost | Notes |
|-----------|------|-------|
| **Redis Container** | $0 | Self-hosted in docker-compose |
| **Memory** | $0 | ~2GB for 2 years of messages |
| **CPU** | Negligible | Redis is very efficient |
| **Total** | **$0/month** | Already running |

### Scaling Options (If Needed)

| Tier | Provider | Cost | Capacity |
|------|----------|------|----------|
| **Current** | Self-hosted | $0 | 10K msg/day, 1K burst |
| **Redis Cloud Free** | Redis Labs | $0 | 30MB, 30 connections |
| **Redis Cloud Paid** | Redis Labs | $5-10/mo | 250MB, 256 connections |
| **AWS ElastiCache** | Amazon | $15-50/mo | t3.micro, 1GB memory |
| **Azure Cache** | Microsoft | $15-50/mo | C0, 250MB |

**Recommendation**: Start with self-hosted (current), scale if needed after 50K+ msg/day.

---

## Implementation Checklist

### Phase 1: Core Infrastructure (Week 1, Days 1-3)
- [ ] Create `waooaw/messaging/` directory
- [ ] Implement `message_bus.py` (MessageBus class)
  - [ ] `publish(message)` → XADD
  - [ ] `subscribe(topic, consumer_group, consumer_name)` → XREADGROUP
  - [ ] `acknowledge(message_id)` → XACK
  - [ ] `claim_pending(consumer_group)` → XCLAIM
- [ ] Implement `models.py` (Message, MessageRouting, etc.)
- [ ] Create Redis consumer groups (setup script)
- [ ] Add configuration to `.env` and `agent_config.yaml`

### Phase 2: Agent Integration (Week 1, Days 4-5)
- [ ] Update `base_agent.py` dimension methods:
  - [ ] `send_message()` → calls `message_bus.publish()`
  - [ ] `receive_message()` → calls `message_bus.subscribe()`
  - [ ] `subscribe_to_channel()` → registers topic subscription
- [ ] Add message polling to agent lifecycle:
  - [ ] `wake_up()` → check messages before deciding
  - [ ] New method: `process_messages()` → fetch and handle
- [ ] Update `WowVisionPrime` to subscribe to topics
- [ ] Test: Manual message publish → agent receives

### Phase 3: Priority & DLQ (Week 2, Days 1-2)
- [ ] Implement priority routing (5 streams)
- [ ] Implement retry logic with exponential backoff
- [ ] Implement Dead Letter Queue
- [ ] Add monitoring/alerting for DLQ
- [ ] Test: Force failure → verify DLQ movement

### Phase 4: Audit Trail (Week 2, Days 3-4)
- [ ] Create `audit/trail_service.py`
- [ ] Create PostgreSQL schema (`audit_log` table)
- [ ] Subscribe to message events
- [ ] Implement async audit writes
- [ ] Create audit query API
- [ ] Test: Send message → verify audit entry

### Phase 5: Testing & Documentation (Week 2, Day 5)
- [ ] Unit tests for MessageBus (pytest)
- [ ] Integration tests (agent → agent communication)
- [ ] Load test (1K msg/sec burst)
- [ ] Document message flow patterns
- [ ] Create troubleshooting guide

---

## Testing Strategy

### Unit Tests
```python
# tests/test_message_bus.py
async def test_publish_message():
    bus = MessageBus()
    msg = Message(
        routing=MessageRouting(from_agent="test", to_agents=["target"]),
        payload=MessagePayload(subject="Test", body="Hello", action="test")
    )
    
    message_id = await bus.publish(msg, priority=3)
    assert message_id is not None  # Confirmation
    
async def test_subscribe_and_receive():
    bus = MessageBus()
    messages = await bus.subscribe(
        stream="waooaw:messages:p3",
        consumer_group="cg_test",
        consumer_name="test_001"
    )
    assert len(messages) > 0
```

### Integration Tests
```python
# tests/test_agent_messaging.py
async def test_vision_to_content_handoff():
    # Setup
    vision = WowVisionPrime(instance_id="vision_test")
    content = WowContentMarketing(instance_id="content_test")
    
    # Vision sends message
    msg_id = await vision.send_message(
        to="wowcontent_marketing",
        subject="Need blog post",
        data={"topic": "AI agents"}
    )
    
    # Content receives and processes
    messages = await content.receive_message()
    assert len(messages) == 1
    assert messages[0].payload.subject == "Need blog post"
```

### Load Test
```python
# tests/test_load.py
async def test_burst_1k_per_second():
    bus = MessageBus()
    
    start = time.time()
    tasks = []
    for i in range(1000):
        msg = create_test_message(i)
        tasks.append(bus.publish(msg, priority=3))
    
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    assert len(results) == 1000  # All published
    assert elapsed < 2.0  # Under 2 seconds
```

---

## Troubleshooting Guide

### Issue: Messages not received by agent

**Symptoms**: Agent running, but no messages processed

**Checks**:
1. Consumer group exists?
   ```bash
   redis-cli XINFO GROUPS waooaw:messages:p3
   ```
2. Agent subscribed to correct topic?
   ```python
   # Check agent_config.yaml subscriptions
   ```
3. Messages in stream?
   ```bash
   redis-cli XLEN waooaw:messages:p3
   ```

**Solution**: Create consumer group, verify subscriptions

---

### Issue: Messages stuck in pending (not acknowledged)

**Symptoms**: XPENDING shows growing list

**Checks**:
```bash
redis-cli XPENDING waooaw:messages:p3 cg_wowvision
```

**Solution**: Agent crashed before ACK, use XCLAIM to recover:
```bash
redis-cli XCLAIM waooaw:messages:p3 cg_wowvision consumer2 300000 <message_id>
```

---

### Issue: High memory usage in Redis

**Symptoms**: Redis memory growing over time

**Checks**:
```bash
redis-cli INFO memory
redis-cli XLEN waooaw:messages:p3  # Check stream length
```

**Solution**: Enable trimming:
```python
# In message_bus.py publish()
await redis.xadd(
    stream,
    {"message": json.dumps(msg.dict())},
    maxlen=10000000,  # Trim to 10M
    approximate=True  # Faster trimming
)
```

---

## Future Enhancements (Post-Week 4)

### 1. Message Compression (Week 8)
- Large payloads (>10KB) compressed with zlib
- Reduces Redis memory by 60-70%
- Transparent to agents

### 2. Message Encryption (Week 12)
- Sensitive data encrypted at rest
- AES-256 encryption for payload
- Key rotation policy

### 3. Multi-Region Support (Week 20)
- Redis Cluster with replication
- Cross-region message routing
- Latency optimization

### 4. GraphQL Subscription API (Week 24)
- Expose message bus to external clients
- WebSocket-based real-time updates
- Filtered subscriptions

### 5. Message Analytics (Week 28)
- Dashboards for message volume, latency
- Agent collaboration visualizations
- Anomaly detection

---

## Summary

| Aspect | Decision |
|--------|----------|
| **Technology** | Redis Streams (already in infrastructure) |
| **Cost** | $0/month (self-hosted) |
| **Delivery** | At-least-once with acknowledgment |
| **Persistence** | 2 years (configurable), replay capable |
| **Priority** | 1-5 scale, 5 separate streams |
| **Scale** | 10K msg/day, 1K burst/sec (easily handled) |
| **Audit** | Separate PostgreSQL store, 7-year retention |
| **Implementation** | 2 weeks (Week 1-2 of IMPLEMENTATION_PLAN) |
| **LOC** | ~800 lines (message_bus.py + models.py + tests) |

---

## Next Steps

1. **Review this design** with team/user
2. **Start implementation** (Phase 1: Core Infrastructure)
3. **Test basic pub/sub** (agent → agent)
4. **Integrate with WowVision** (first real use case)
5. **Monitor and optimize** (Week 2 onwards)

**Ready to implement?** Let me know if any questions, or we can start coding `message_bus.py` immediately! 🚀

---

**Document Status**: ✅ Complete  
**Next Action**: User approval → Begin Phase 1 implementation  
**Estimated Time**: 2 weeks to production-ready message bus
