# RBAC Policy for Partner Platform
# Version: 1.0
# Owner: Platform Team
#
# Purpose: Enforce role-based access control for PP users
# - 7-role hierarchy: admin, subscription_manager, agent_orchestrator, 
#   infrastructure_engineer, helpdesk_agent, industry_manager, viewer
# - Each role has specific permissions
# - Admins have full access

package gateway.rbac_pp

import future.keywords.if
import future.keywords.in

# Default deny
default allow = false

# Role hierarchy (higher number = more permissions)
role_levels := {
    "admin": 7,
    "subscription_manager": 6,
    "agent_orchestrator": 5,
    "infrastructure_engineer": 4,
    "helpdesk_agent": 3,
    "industry_manager": 2,
    "viewer": 1
}

# Permission to role mapping
permissions := {
    # Admin permissions (level 7)
    "system.configure": ["admin"],
    "user.delete": ["admin"],
    "billing.manage": ["admin", "subscription_manager"],
    
    # Subscription manager permissions (level 6)
    "subscription.create": ["admin", "subscription_manager"],
    "subscription.update": ["admin", "subscription_manager"],
    "subscription.cancel": ["admin", "subscription_manager"],
    "customer.manage": ["admin", "subscription_manager"],
    
    # Agent orchestrator permissions (level 5)
    "agent.create": ["admin", "agent_orchestrator"],
    "agent.update": ["admin", "agent_orchestrator"],
    "agent.deploy": ["admin", "agent_orchestrator"],
    "agent.execute": ["admin", "agent_orchestrator"],
    "task.create": ["admin", "agent_orchestrator"],
    "task.cancel": ["admin", "agent_orchestrator"],
    
    # Infrastructure engineer permissions (level 4)
    "infrastructure.deploy": ["admin", "infrastructure_engineer"],
    "infrastructure.configure": ["admin", "infrastructure_engineer"],
    "database.access": ["admin", "infrastructure_engineer"],
    "monitoring.configure": ["admin", "infrastructure_engineer"],
    
    # Helpdesk agent permissions (level 3)
    "customer.view": ["admin", "subscription_manager", "helpdesk_agent"],
    "ticket.create": ["admin", "helpdesk_agent"],
    "ticket.update": ["admin", "helpdesk_agent"],
    "ticket.resolve": ["admin", "helpdesk_agent"],
    
    # Industry manager permissions (level 2)
    "industry.manage": ["admin", "industry_manager"],
    "agent.categorize": ["admin", "industry_manager"],
    
    # Viewer permissions (level 1)
    "dashboard.view": ["admin", "subscription_manager", "agent_orchestrator", "infrastructure_engineer", "helpdesk_agent", "industry_manager", "viewer"],
    "report.view": ["admin", "subscription_manager", "agent_orchestrator", "infrastructure_engineer", "helpdesk_agent", "industry_manager", "viewer"],
    "agent.view": ["admin", "subscription_manager", "agent_orchestrator", "infrastructure_engineer", "helpdesk_agent", "industry_manager", "viewer"],
}

# Get user's highest role level
user_role_level = level if {
    user_roles := input.jwt.roles
    levels := [role_levels[role] | role := user_roles[_]; role_levels[role]]
    level := max(levels)
} else = 0

# Get user's roles
user_roles = roles if {
    roles := input.jwt.roles
} else = []

# Check if user has permission
has_permission(permission) if {
    # Get allowed roles for this permission
    allowed_roles := permissions[permission]
    
    # Check if user has any of the allowed roles
    user_has_role := [role | role := user_roles[_]; role == allowed_roles[_]]
    count(user_has_role) > 0
}

# Allow if user has permission for the requested resource
allow if {
    permission := sprintf("%s.%s", [input.resource, input.action])
    has_permission(permission)
}

# Allow admin for everything
allow if {
    "admin" in user_roles
}

# Deny reason
deny_reason = reason if {
    not allow
    permission := sprintf("%s.%s", [input.resource, input.action])
    permissions[permission]  # Check permission exists
    allowed_roles := permissions[permission]
    reason := sprintf("User lacks permission '%s'. Required roles: %v. User roles: %v", [
        permission,
        allowed_roles,
        user_roles
    ])
} else = reason if {
    not allow
    permission := sprintf("%s.%s", [input.resource, input.action])
    reason := sprintf("Unknown permission '%s'. User roles: %v", [
        permission,
        user_roles
    ])
}

# Get all permissions for user's roles
user_permissions = perms if {
    perms := {perm | 
        perm := permissions[p][_]
        permissions[p]
        perm == user_roles[_]
    }
}

# Get user info
user_info = info if {
    info := {
        "user_id": input.jwt.user_id,
        "email": input.jwt.email,
        "roles": user_roles,
        "role_level": user_role_level,
        "is_admin": "admin" in user_roles
    }
}
