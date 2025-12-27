# GitHub Project Management Setup

**Date**: December 27, 2025  
**Purpose**: Track WAOOAW development with GitHub-native project management

---

## Overview

This repository uses GitHub's native project management features:
- **Issues** - Track designs, implementations, gaps, bugs
- **Projects** - Kanban board for visual progress tracking
- **Milestones** - Group work by version/phase
- **Labels** - Categorize and filter
- **Mobile App** - View/update on the go
- **Copilot Integration** - Comment "@github-copilot complete this task"

---

## Quick Start

### 1. Create GitHub Project Board

**Via GitHub Web UI:**
1. Go to repository: https://github.com/dlai-sd/WAOOAW
2. Click **Projects** tab → **New project**
3. Choose **Board** template
4. Name: **WAOOAW Development Tracker**
5. Add columns:
   - 📋 **Backlog** (No status)
   - 🎨 **Design** (In progress)
   - 💻 **Implementation** (In progress)
   - 🧪 **Testing** (In progress)
   - ✅ **Done** (Done)

**Via GitHub CLI:**
```bash
# Install GitHub CLI
# https://cli.github.com/

# Create project
gh project create --owner dlai-sd --repo WAOOAW \
  --title "WAOOAW Development Tracker" \
  --body "Track all design, implementation, and gap work"

# Add to project manually via web UI (columns)
```

### 2. Create Initial Issues (Past Work)

Use the scripts below or create manually via:
- Web UI: **Issues** → **New issue** → Choose template
- GitHub CLI: See commands in next section

---

## Initial Issues to Create

### Completed Work (v0.2.0 - v0.2.2)

#### Issue #1: [Design] Base Agent Architecture
```yaml
Title: [Design] Base Agent Architecture (15 Dimensions)
Labels: design, dimension-all, v0.2.0
Milestone: Foundation (v0.2.0)
Status: ✅ Done

Body:
## Component Name
Base Agent Architecture (15 Dimensions)

## Related Dimension
Multiple Dimensions (all 15)

## Problem Statement
Need foundational agent class that all 14 CoEs can inherit from, implementing industry-standard multi-agent architecture patterns.

## Requirements
- Dual-identity framework (Specialization + Personality)
- 6-step wake protocol
- Hybrid decision framework (deterministic + LLM)
- All 15 dimensions as methods (even if stubbed)
- PostgreSQL + vector memory
- GitHub integration

## Design Decisions
- Python base class (WAAOOWAgent) with inheritance model
- Composition over inheritance where appropriate
- Async-first design
- Database schema with 10 core tables

## Deliverables
- [x] base_agent.py (1681 lines, 82 methods)
- [x] BASE_AGENT_CORE_ARCHITECTURE.md
- [x] base_agent_schema.sql
- [x] WowVisionPrime as first implementation
- [x] All 15 dimension methods present

## Target Version
v0.2.0

## Related Issues
- Blocks: #2 (Message Bus)
- Blocks: #3 (Message Handler)
- Related: ARCHITECTURAL_COMPLIANCE_CHECK.md
```

#### Issue #2: [Design] Message Bus Architecture
```yaml
Title: [Design] Message Bus Architecture (Redis Streams)
Labels: design, dimension-7, v0.2.1
Milestone: Communication Infrastructure
Status: ✅ Done

Body:
## Component Name
Message Bus (Redis Streams-based)

## Related Dimension
7 - Communication Protocol

## Problem Statement
Agents need a nervous system to communicate, collaborate, and coordinate. Current state: agents cannot send/receive messages, no event-driven wake.

## Requirements
- At-least-once delivery with acknowledgment
- 10K msg/day, 1K burst/sec capacity
- 2-year message retention + replay
- Priority handling (1-5 scale)
- Separate audit trail (7-year compliance)
- Dead Letter Queue for failures
- $0 cost (use existing Redis)

## Design Decisions
- Technology: Redis Streams (already in infrastructure)
- Delivery: At-least-once with consumer groups + pending entries
- Persistence: AOF + RDB for durability
- Priority: 5 separate streams (p5 = critical → p1 = background)
- Audit: Separate PostgreSQL store

## Deliverables
- [x] MESSAGE_BUS_ARCHITECTURE.md (1000+ lines)
- [x] Complete message schema (routing, payload, metadata, audit)
- [x] 5 routing patterns (point-to-point, broadcast, topic, request-response, self)
- [x] Redis persistence gap analysis
- [x] 2-week implementation plan

## Target Version
v0.2.1

## Related Issues
- Depends on: #1 (Base Agent)
- Blocks: #3 (Message Handler)
- Blocks: #4 (MessageBus Implementation)
- Gap: #7 (Redis Persistence Config)

## Related Docs
- docs/MESSAGE_BUS_ARCHITECTURE.md
```

#### Issue #3: [Design] Agent Message Handler
```yaml
Title: [Design] Agent Message Handler (Component)
Labels: design, dimension-7, v0.2.2
Milestone: Communication Infrastructure
Status: ✅ Done

Body:
## Component Name
Agent Message Handler (MessageHandler class)

## Related Dimension
7 - Communication Protocol

## Problem Statement
Agents need client-side component to interact with Message Bus. Need patterns for sending, receiving, subscribing, request-response, state tracking.

## Requirements
- Send messages (point-to-point, broadcast)
- Receive messages (sync polling, async loop, callbacks)
- Handler registration (manual + decorator pattern)
- Priority queue (process critical first)
- Request-response pattern (sync + async)
- Message state tracking (sent, pending, completed, failed)
- Correlation IDs for pairing

## Design Decisions
- Architecture: Separate component (composition pattern) in base agent
- Patterns: Hybrid - async loop + sync polling + callbacks
- Registration: Manual register() + @message_handler decorator
- Priority: Weighted polling (critical 10x more than background)
- State: In-memory tracking with optional DB persistence

## Deliverables
- [x] AGENT_MESSAGE_HANDLER_DESIGN.md (1000+ lines)
- [x] MessageHandler class structure
- [x] 3 messaging patterns (always-on, wake-sleep, callback)
- [x] Priority queue implementation
- [x] Request-response patterns
- [x] Integration design with base_agent.py
- [x] Usage examples (5 complete patterns)
- [x] 1.5-week implementation plan

## Target Version
v0.2.2

## Related Issues
- Depends on: #1 (Base Agent), #2 (Message Bus)
- Blocks: #5 (MessageHandler Implementation)
- Blocks: #6 (Base Agent Integration)

## Related Docs
- docs/AGENT_MESSAGE_HANDLER_DESIGN.md
- docs/MESSAGE_BUS_ARCHITECTURE.md
```

---

### Upcoming Work (v0.2.3+)

#### Issue #4: [Implementation] MessageBus Class
```yaml
Title: [Implementation] MessageBus Class (Redis Streams)
Labels: implementation, dimension-7, v0.2.3
Milestone: Week 1-2 Implementation
Status: 📋 Backlog

Body:
## Component Name
MessageBus class (waooaw/messaging/message_bus.py)

## Related Dimension
7 - Communication Protocol

## Implementation Scope
Implement MessageBus class with Redis Streams integration:
- publish() - XADD to stream
- subscribe() - XREADGROUP with consumer groups
- acknowledge() - XACK message
- claim_pending() - XCLAIM stale messages
- Consumer group setup

## Design Reference
- Design: #2 [Design] Message Bus Architecture
- Document: docs/MESSAGE_BUS_ARCHITECTURE.md

## Implementation Tasks
- [ ] Create waooaw/messaging/ directory
- [ ] Create waooaw/messaging/message_bus.py
- [ ] Implement MessageBus class
  - [ ] __init__() - Redis connection
  - [ ] publish() - XADD with priority routing
  - [ ] subscribe() - XREADGROUP with consumer groups
  - [ ] acknowledge() - XACK
  - [ ] claim_pending() - XCLAIM
- [ ] Create waooaw/messaging/models.py
  - [ ] Message class (Pydantic)
  - [ ] MessageRouting class
  - [ ] MessagePayload class
  - [ ] MessageMetadata class
  - [ ] AuditInfo class
- [ ] Setup consumer groups (initialization script)
- [ ] Write unit tests (test_message_bus.py)
- [ ] Integration test with Redis

## Estimated Lines of Code
~400 LOC (message_bus.py)

## Estimated Time
3-4 days

## Target Version
v0.2.3

## Acceptance Criteria
- [ ] All tests passing
- [ ] Can publish message to Redis stream
- [ ] Can subscribe and read messages
- [ ] Consumer groups working
- [ ] At-least-once delivery verified

## Commands for Copilot
@github-copilot Implement the MessageBus class following MESSAGE_BUS_ARCHITECTURE.md
@github-copilot Write unit tests for publish() and subscribe() methods
```

#### Issue #5: [Implementation] MessageHandler Class
```yaml
Title: [Implementation] MessageHandler Class (Agent Component)
Labels: implementation, dimension-7, v0.2.3
Milestone: Week 1-2 Implementation
Status: 📋 Backlog

Body:
## Component Name
MessageHandler class (waooaw/messaging/message_handler.py)

## Related Dimension
7 - Communication Protocol

## Implementation Scope
Implement agent-side message handling component:
- send(), broadcast(), reply() methods
- register() - handler registration
- check_messages() - sync polling
- _message_loop() - async background task
- send_and_wait() - request-response with timeout
- Priority queue for inbox
- Message state tracking

## Design Reference
- Design: #3 [Design] Agent Message Handler
- Document: docs/AGENT_MESSAGE_HANDLER_DESIGN.md

## Implementation Tasks
- [ ] Create waooaw/messaging/message_handler.py
- [ ] Implement MessageHandler class
  - [ ] __init__() - setup queues, registry
  - [ ] send() - publish to bus
  - [ ] broadcast() - publish to all
  - [ ] reply() - reply to message
  - [ ] register() - register handler
  - [ ] check_messages() - sync polling
- [ ] Implement PriorityQueue class
- [ ] Implement MessageState tracking
- [ ] Implement _message_loop() - async task
- [ ] Implement send_and_wait() - request-response
- [ ] Implement _match_handlers() - topic matching
- [ ] Write unit tests (test_message_handler.py)
- [ ] Integration test (agent-to-agent)

## Estimated Lines of Code
~600 LOC (message_handler.py)

## Estimated Time
4-5 days

## Target Version
v0.2.3

## Acceptance Criteria
- [ ] All tests passing
- [ ] Can send messages via handler
- [ ] Can receive and route to handlers
- [ ] Priority queue working
- [ ] Request-response pattern working
- [ ] Background loop functional

## Commands for Copilot
@github-copilot Implement MessageHandler class following AGENT_MESSAGE_HANDLER_DESIGN.md
@github-copilot Implement send_and_wait() with timeout handling
```

#### Issue #6: [Implementation] Base Agent Messaging Integration
```yaml
Title: [Implementation] Base Agent Messaging Integration
Labels: implementation, dimension-7, v0.2.3
Milestone: Week 1-2 Implementation
Status: 📋 Backlog

Body:
## Component Name
Base Agent Messaging Integration (base_agent.py)

## Related Dimension
7 - Communication Protocol

## Implementation Scope
Integrate MessageHandler into base_agent.py:
- Add self.message_handler to __init__()
- Replace send_message() stub with real implementation
- Replace receive_message() stub with real implementation
- Replace subscribe_to_channel() stub with real implementation
- Add _register_default_message_handlers()
- Add default handlers (shutdown, pause, resume, health_check)

## Design Reference
- Design: #3 [Design] Agent Message Handler
- Document: docs/AGENT_MESSAGE_HANDLER_DESIGN.md

## Implementation Tasks
- [ ] Update base_agent.py __init__()
  - [ ] Add self.message_handler = MessageHandler(...)
- [ ] Replace Dimension 7 stub methods:
  - [ ] send_message() - call handler.send()
  - [ ] receive_message() - call handler.check_messages()
  - [ ] subscribe_to_channel() - call handler.register()
- [ ] Add _register_default_message_handlers()
- [ ] Implement default handlers:
  - [ ] on_shutdown()
  - [ ] on_pause()
  - [ ] on_resume()
  - [ ] on_health_check()
- [ ] Update agent_config.yaml with messaging config
- [ ] Write integration tests
- [ ] Test with WowVisionPrime

## Estimated Lines of Code
~100 LOC (changes to base_agent.py)

## Estimated Time
2-3 days

## Target Version
v0.2.3

## Acceptance Criteria
- [ ] All tests passing
- [ ] Agents can send messages
- [ ] Agents can receive messages
- [ ] Agents can subscribe to topics
- [ ] Default handlers working
- [ ] WowVision can communicate with WowContent

## Commands for Copilot
@github-copilot Update base_agent.py to integrate MessageHandler component
@github-copilot Implement default message handlers for system broadcasts
```

#### Issue #7: [Gap] Redis Persistence Configuration
```yaml
Title: [Gap] Redis Persistence Configuration Missing
Labels: gap, infrastructure, critical
Milestone: Week 1 Setup
Status: 📋 Backlog

Body:
## Gap Description
Redis in docker-compose.yml has no persistence configuration (AOF/RDB). Messages may be lost on crash.

## Severity
Critical - Blocks autonomous operation

## Related Dimension
Infrastructure (affects Dimension 7 - Communication)

## Impact
Without this:
- Messages written after last RDB snapshot lost on crash
- At-least-once delivery compromised
- No guarantee of 2-year retention
- System reliability affected

## Identified During
- Document: MESSAGE_BUS_ARCHITECTURE.md (Redis verification section)
- Issue: #2 [Design] Message Bus Architecture

## Proposed Solution
Update infrastructure/docker/docker-compose.yml:

```yaml
redis:
  image: redis:7-alpine
  command: >
    redis-server
    --appendonly yes
    --appendfsync everysec
    --maxmemory 2gb
    --maxmemory-policy noeviction
    --save 900 1
    --save 300 10
    --save 60 10000
  volumes:
    - redis-data:/data
  deploy:
    resources:
      limits:
        memory: 2.5gb
```

## Estimated Effort
1-2 hours

## Target Version
v0.2.3

## Tasks
- [ ] Update docker-compose.yml with Redis config
- [ ] Test persistence: write messages → restart Redis → verify recovery
- [ ] Document backup strategy
- [ ] Update MESSAGE_BUS_ARCHITECTURE.md (mark gap as resolved)

## Commands for Copilot
@github-copilot Update docker-compose.yml to add Redis persistence configuration
```

---

## Creating Issues via GitHub CLI

```bash
# Install GitHub CLI
# https://cli.github.com/

# Authenticate
gh auth login

# Create completed issues (past work)
gh issue create --repo dlai-sd/WAOOAW \
  --title "[Design] Base Agent Architecture (15 Dimensions)" \
  --label "design,dimension-all,v0.2.0" \
  --milestone "Foundation (v0.2.0)" \
  --body "$(cat .github/issues/001-design-base-agent.md)"

gh issue create --repo dlai-sd/WAOOAW \
  --title "[Design] Message Bus Architecture (Redis Streams)" \
  --label "design,dimension-7,v0.2.1" \
  --milestone "Communication Infrastructure" \
  --body "$(cat .github/issues/002-design-message-bus.md)"

gh issue create --repo dlai-sd/WAOOAW \
  --title "[Design] Agent Message Handler (Component)" \
  --label "design,dimension-7,v0.2.2" \
  --milestone "Communication Infrastructure" \
  --body "$(cat .github/issues/003-design-message-handler.md)"

# Create upcoming work issues
gh issue create --repo dlai-sd/WAOOAW \
  --title "[Implementation] MessageBus Class (Redis Streams)" \
  --label "implementation,dimension-7,v0.2.3" \
  --milestone "Week 1-2 Implementation" \
  --body "$(cat .github/issues/004-impl-message-bus.md)"

gh issue create --repo dlai-sd/WAOOAW \
  --title "[Implementation] MessageHandler Class (Agent Component)" \
  --label "implementation,dimension-7,v0.2.3" \
  --milestone "Week 1-2 Implementation" \
  --body "$(cat .github/issues/005-impl-message-handler.md)"

gh issue create --repo dlai-sd/WAOOAW \
  --title "[Implementation] Base Agent Messaging Integration" \
  --label "implementation,dimension-7,v0.2.3" \
  --milestone "Week 1-2 Implementation" \
  --body "$(cat .github/issues/006-impl-base-agent-integration.md)"

gh issue create --repo dlai-sd/WAOOAW \
  --title "[Gap] Redis Persistence Configuration Missing" \
  --label "gap,infrastructure,critical" \
  --milestone "Week 1 Setup" \
  --body "$(cat .github/issues/007-gap-redis-persistence.md)"

# Close completed issues
gh issue close 1 --reason "completed" --comment "Completed in v0.2.0"
gh issue close 2 --reason "completed" --comment "Completed in v0.2.1"
gh issue close 3 --reason "completed" --comment "Completed in v0.2.2"
```

---

## Labels to Create

```bash
# Dimension labels
gh label create "dimension-1" --color "0052CC" --description "Wake Protocol"
gh label create "dimension-2" --color "0052CC" --description "Context Management"
gh label create "dimension-3" --color "0052CC" --description "Identity System"
gh label create "dimension-4" --color "0052CC" --description "Hierarchy/RACI"
gh label create "dimension-5" --color "0052CC" --description "Collaboration"
gh label create "dimension-6" --color "0052CC" --description "Learning & Memory"
gh label create "dimension-7" --color "0052CC" --description "Communication Protocol"
gh label create "dimension-8" --color "0052CC" --description "Resource Management"
gh label create "dimension-9" --color "0052CC" --description "Trust & Reputation"
gh label create "dimension-10" --color "0052CC" --description "Error Handling"
gh label create "dimension-11" --color "0052CC" --description "Observability"
gh label create "dimension-12" --color "0052CC" --description "Security & Privacy"
gh label create "dimension-13" --color "0052CC" --description "Performance"
gh label create "dimension-14" --color "0052CC" --description "Testing"
gh label create "dimension-15" --color "0052CC" --description "Lifecycle"
gh label create "dimension-all" --color "0052CC" --description "Multiple Dimensions"

# Type labels
gh label create "design" --color "D4C5F9" --description "Design component"
gh label create "implementation" --color "5319E7" --description "Implementation task"
gh label create "gap" --color "FBCA04" --description "Gap or missing feature"
gh label create "bug" --color "D93F0B" --description "Bug report"

# Version labels
gh label create "v0.2.0" --color "BFD4F2" --description "Foundation"
gh label create "v0.2.1" --color "BFD4F2" --description "Message Bus Design"
gh label create "v0.2.2" --color "BFD4F2" --description "Message Handler Design"
gh label create "v0.2.3" --color "BFD4F2" --description "Messaging Implementation"

# Severity labels
gh label create "critical" --color "B60205" --description "Critical severity"
gh label create "high" --color "D93F0B" --description "High severity"
gh label create "medium" --color "FBCA04" --description "Medium severity"
gh label create "low" --color "0E8A16" --description "Low severity"

# Component labels
gh label create "infrastructure" --color "C2E0C6" --description "Infrastructure"
gh label create "agent" --color "C2E0C6" --description "Agent component"
gh label create "database" --color "C2E0C6" --description "Database"
gh label create "messaging" --color "C2E0C6" --description "Messaging system"
```

---

## Milestones to Create

```bash
# Create milestones
gh api repos/dlai-sd/WAOOAW/milestones \
  -f title="Foundation (v0.2.0)" \
  -f description="Base agent architecture with 15 dimensions" \
  -f state="closed"

gh api repos/dlai-sd/WAOOAW/milestones \
  -f title="Communication Infrastructure" \
  -f description="Message Bus + Message Handler design (v0.2.1, v0.2.2)" \
  -f state="closed"

gh api repos/dlai-sd/WAOOAW/milestones \
  -f title="Week 1-2 Implementation" \
  -f description="Implement MessageBus + MessageHandler (v0.2.3)" \
  -f state="open" \
  -f due_on="2025-01-10T00:00:00Z"

gh api repos/dlai-sd/WAOOAW/milestones \
  -f title="Week 1 Setup" \
  -f description="Fix infrastructure gaps" \
  -f state="open" \
  -f due_on="2025-01-03T00:00:00Z"
```

---

## Using GitHub Mobile App

### View Issues
1. Open GitHub mobile app
2. Navigate to **dlai-sd/WAOOAW**
3. Tap **Issues** tab
4. Filter by label (e.g., "dimension-7", "v0.2.3")
5. Tap issue to view details

### Update Status
1. Open issue
2. Scroll to checkboxes in description
3. Tap checkbox to mark complete
4. Changes sync immediately

### View Project Board
1. In repository, tap **Projects**
2. Select **WAOOAW Development Tracker**
3. View cards in columns (Backlog → Design → Implementation → Testing → Done)
4. Drag cards between columns

### Comment on Issue
1. Open issue
2. Tap comment field
3. Type update or use **@github-copilot** mention
4. Post comment

---

## Using GitHub Copilot in Issues

### Request Implementation
Comment on issue:
```
@github-copilot Please implement the MessageBus class as described in this issue. 
Follow the design in docs/MESSAGE_BUS_ARCHITECTURE.md.

Focus on:
- publish() method with Redis XADD
- subscribe() method with XREADGROUP
- Consumer group setup

Use async/await pattern and include error handling.
```

### Request Tests
```
@github-copilot Write unit tests for the MessageBus class.

Test cases:
- test_publish_message() - verify message added to stream
- test_subscribe_messages() - verify consumer group reads messages
- test_acknowledge_message() - verify XACK removes from pending
- test_at_least_once_delivery() - verify redelivery on crash

Use pytest and mock Redis connection.
```

### Request Code Review
```
@github-copilot Review the MessageBus implementation in PR #10.

Check for:
- Correct Redis Streams usage
- Error handling
- Async/await patterns
- Type hints
- Documentation

Suggest improvements if needed.
```

### Request Bug Fix
```
@github-copilot Fix the KeyError in message_handler.py line 123.

The error occurs when receiving a malformed message without 'payload' field.
Add validation and handle gracefully with error logging.
```

---

## Slice & Dice Views

### View by Dimension
```bash
# All Communication Protocol work
gh issue list --label "dimension-7"

# All Learning & Memory work
gh issue list --label "dimension-6"
```

### View by Phase
```bash
# All designs
gh issue list --label "design"

# All implementations
gh issue list --label "implementation"

# All gaps
gh issue list --label "gap"
```

### View by Version
```bash
# v0.2.3 work
gh issue list --label "v0.2.3"

# v0.2.2 work (completed)
gh issue list --label "v0.2.2" --state "closed"
```

### View by Status
```bash
# Open issues
gh issue list --state "open"

# Closed issues
gh issue list --state "closed"

# Issues in milestone
gh issue list --milestone "Week 1-2 Implementation"
```

### View Critical Gaps
```bash
gh issue list --label "gap,critical"
```

---

## Project Board Views

### On Web UI

**Backlog View**: All unstarted work
- Filter: Status = No status
- Group by: Label (dimension-1, dimension-2, etc.)

**In Progress View**: Current work
- Filter: Status = Design OR Implementation OR Testing
- Group by: Assignee

**Completed View**: Done work
- Filter: Status = Done
- Group by: Version (v0.2.0, v0.2.1, v0.2.2)

**Dimension View**: By dimension
- Group by: Dimension label
- Sort by: Priority

---

## Next Steps

1. **Create Project Board**
   ```bash
   # Via web UI or CLI
   ```

2. **Create Labels & Milestones**
   ```bash
   # Run label creation commands above
   # Run milestone creation commands above
   ```

3. **Create Initial Issues**
   ```bash
   # Use templates or CLI commands
   # Create #1-7 for past work + upcoming work
   ```

4. **Link to Project Board**
   - Add issues to project
   - Assign to columns (Done, Backlog, etc.)

5. **Start Using**
   - View on mobile app
   - Comment with @github-copilot
   - Track progress daily

---

## Tips

- **Use issue numbers** in commits: "Implements #4", "Fixes #7", "Closes #5"
- **Update checklists** in issue descriptions as you work
- **Comment on issues** with progress updates
- **Use @mentions** to notify team members
- **Link issues** with "Depends on #X", "Blocks #Y"
- **@github-copilot** for implementation help directly in issues

---

**Status**: ✅ Templates created, ready to setup project board  
**Next**: Create GitHub Project board and initial issues  
**Estimated Setup Time**: 30-60 minutes
