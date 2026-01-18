# Governor Role Policy
# Version: 1.0
# Owner: Platform Team
#
# Purpose: Enforce Governor approval workflows
# - Certain actions require Governor approval
# - Governor agents have special privileges
# - External execution requests need approval

package gateway.governor_role

import future.keywords.if
import future.keywords.in

# Default deny actions requiring approval
default requires_approval = false
default is_governor = false

# Identify if user is a Governor
is_governor if {
    "admin" in input.jwt.roles
    input.jwt.governor_agent_id
}

# Actions that always require Governor approval
requires_approval if {
    input.action == "agent.create"
    not is_governor
}

requires_approval if {
    input.action == "agent.delete"
    not is_governor
}

requires_approval if {
    input.action == "execution.external"
    not is_governor
}

requires_approval if {
    input.action == "budget.override"
    not is_governor
}

requires_approval if {
    input.action == "system.configuration"
    not is_governor
}

# Allow action if it doesn't require approval
allow if {
    not requires_approval
}

# Allow action if user is Governor
allow if {
    is_governor
}

# Allow action if approval has been granted
allow if {
    requires_approval
    approval_exists
}

# Check if approval exists in system (external data)
approval_exists if {
    data.approvals[input.request_id]
    approval := data.approvals[input.request_id]
    approval.status == "approved"
    approval.approved_by_governor_id
}

# Deny reason when approval required
deny_reason = reason if {
    requires_approval
    not is_governor
    not approval_exists
    reason := sprintf("Action '%s' requires Governor approval", [input.action])
}

# Information about who can approve
approval_info = info if {
    requires_approval
    not is_governor
    info := {
        "required": true,
        "action": input.action,
        "request_id": input.request_id,
        "message": "This action requires approval from a Governor agent",
        "governors": data.governors
    }
}
