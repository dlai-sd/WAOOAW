# Governor Role Policy Tests
# Version: 1.0

package gateway.governor_role

test_is_governor_true {
    is_governor with input as {
        "jwt": {
            "roles": ["admin"],
            "governor_agent_id": "gov_agent_001"
        }
    }
}

test_is_governor_false_no_role {
    not is_governor with input as {
        "jwt": {
            "roles": ["viewer"],
            "governor_agent_id": null
        }
    }
}

test_requires_approval_agent_create {
    requires_approval with input as {
        "action": "agent.create",
        "jwt": {
            "roles": ["agent_orchestrator"]
        }
    }
}

test_no_approval_for_governor {
    not requires_approval with input as {
        "action": "agent.create",
        "jwt": {
            "roles": ["admin"],
            "governor_agent_id": "gov_agent_001"
        }
    }
}

test_allow_governor_any_action {
    allow with input as {
        "action": "system.configuration",
        "jwt": {
            "roles": ["admin"],
            "governor_agent_id": "gov_agent_001"
        }
    }
}

test_deny_non_governor_restricted_action {
    not allow with input as {
        "action": "agent.delete",
        "jwt": {
            "roles": ["agent_orchestrator"]
        },
        "request_id": "req-123"
    }
}

test_allow_with_approval {
    allow with input as {
        "action": "agent.create",
        "jwt": {
            "roles": ["agent_orchestrator"]
        },
        "request_id": "req-456"
    }
    with data.approvals as {
        "req-456": {
            "status": "approved",
            "approved_by_governor_id": "gov_001"
        }
    }
}

test_deny_reason_message {
    reason := deny_reason with input as {
        "action": "budget.override",
        "jwt": {
            "roles": ["viewer"]
        },
        "request_id": "req-789"
    }
    contains(reason, "requires Governor approval")
}
