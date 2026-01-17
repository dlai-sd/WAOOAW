# RBAC PP Policy Tests
# Version: 1.0

package gateway.rbac_pp

test_admin_full_access {
    allow with input as {
        "resource": "system",
        "action": "configure",
        "jwt": {
            "user_id": "admin-001",
            "email": "admin@waooaw.com",
            "roles": ["admin"]
        }
    }
}

test_viewer_can_view_dashboard {
    allow with input as {
        "resource": "dashboard",
        "action": "view",
        "jwt": {
            "roles": ["viewer"]
        }
    }
}

test_viewer_cannot_create_agent {
    not allow with input as {
        "resource": "agent",
        "action": "create",
        "jwt": {
            "roles": ["viewer"]
        }
    }
}

test_agent_orchestrator_can_create_agent {
    allow with input as {
        "resource": "agent",
        "action": "create",
        "jwt": {
            "roles": ["agent_orchestrator"]
        }
    }
}

test_subscription_manager_can_manage_subscription {
    allow with input as {
        "resource": "subscription",
        "action": "update",
        "jwt": {
            "roles": ["subscription_manager"]
        }
    }
}

test_infrastructure_engineer_can_deploy {
    allow with input as {
        "resource": "infrastructure",
        "action": "deploy",
        "jwt": {
            "roles": ["infrastructure_engineer"]
        }
    }
}

test_helpdesk_can_resolve_tickets {
    allow with input as {
        "resource": "ticket",
        "action": "resolve",
        "jwt": {
            "roles": ["helpdesk_agent"]
        }
    }
}

test_industry_manager_can_manage_industry {
    allow with input as {
        "resource": "industry",
        "action": "manage",
        "jwt": {
            "roles": ["industry_manager"]
        }
    }
}

test_user_role_level_admin {
    level := user_role_level with input as {
        "jwt": {
            "roles": ["admin"]
        }
    }
    level == 7
}

test_user_role_level_viewer {
    level := user_role_level with input as {
        "jwt": {
            "roles": ["viewer"]
        }
    }
    level == 1
}

test_user_role_level_multiple_roles {
    level := user_role_level with input as {
        "jwt": {
            "roles": ["viewer", "helpdesk_agent", "agent_orchestrator"]
        }
    }
    level == 5  # highest is agent_orchestrator
}

test_deny_reason_no_permission {
    reason := deny_reason with input as {
        "resource": "agent",
        "action": "create",
        "jwt": {
            "roles": ["viewer"]
        }
    }
    contains(reason, "lacks permission")
    contains(reason, "agent.create")
}

test_user_info {
    info := user_info with input as {
        "jwt": {
            "user_id": "user-123",
            "email": "user@example.com",
            "roles": ["agent_orchestrator"]
        }
    }
    info.user_id == "user-123"
    info.role_level == 5
    info.is_admin == false
}
