"""
Event type constants for agent wake-up filtering.

These constants define the event types that agents can filter on
when deciding whether to wake up and process an event.
"""

# GitHub Events
EVENT_FILE_CREATED = "github.file.created"
EVENT_FILE_UPDATED = "github.file.updated"
EVENT_FILE_DELETED = "github.file.deleted"
EVENT_PR_OPENED = "github.pr.opened"
EVENT_PR_UPDATED = "github.pr.updated"
EVENT_PR_CLOSED = "github.pr.closed"
EVENT_PR_MERGED = "github.pr.merged"
EVENT_ISSUE_OPENED = "github.issue.opened"
EVENT_ISSUE_COMMENT = "github.issue.comment"
EVENT_ISSUE_CLOSED = "github.issue.closed"
EVENT_COMMIT_PUSHED = "github.commit.pushed"
EVENT_BRANCH_CREATED = "github.branch.created"
EVENT_BRANCH_DELETED = "github.branch.deleted"

# Agent Events
EVENT_AGENT_TASK_ASSIGNED = "agent.task.assigned"
EVENT_AGENT_ESCALATION = "agent.escalation"
EVENT_AGENT_PEER_REQUEST = "agent.peer.request"
EVENT_AGENT_CHECKPOINT = "agent.checkpoint"

# System Events
EVENT_SYSTEM_STARTUP = "system.startup"
EVENT_SYSTEM_SHUTDOWN = "system.shutdown"
EVENT_SYSTEM_CONFIG_CHANGED = "system.config.changed"

# Custom Events (agent-specific)
EVENT_CUSTOM = "custom.event"

# Event priorities
PRIORITY_HIGH = 1
PRIORITY_NORMAL = 2
PRIORITY_LOW = 3
