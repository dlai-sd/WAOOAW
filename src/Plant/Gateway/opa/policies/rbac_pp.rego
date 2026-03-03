# rbac_pp.rego — RBAC policy for Partner Platform (PP) Gateway
#
# Queries: POST /v1/data/gateway/rbac_pp/allow
# Input:   {"input": {"resource": str, "action": str, "jwt": {"user_id": str, "email": str, "roles": [str], ...}}}
# Output:  {"result": {"allow": bool, "user_info": {...}, "deny_reason": str|null}}
#
# 7-role hierarchy (level 1 = highest privilege):
#   admin(1) > customer_admin(2) > developer(3) > manager(4) > analyst(5) > support(6) > viewer(7)
#
# DB Updates screen safety:
#   PP /db/* routes carry a db_updates token with roles:["admin"].
#   OPA sees resource="admin", action="create" (POST).
#   Admin is level 1 <= any required level -> allow=true.
#   Plant Backend /api/v1/admin/db is a second hard gate (requires X-Gateway + admin role).

package gateway.rbac_pp

import rego.v1

# ---------------------------------------------------------------------------
# Role hierarchy — lower number = more privileged
# ---------------------------------------------------------------------------
role_hierarchy := {
	"admin":          1,
	"customer_admin": 2,
	"developer":      3,
	"manager":        4,
	"analyst":        5,
	"support":        6,
	"viewer":         7,
}

# Minimum privilege level required per action (lower number = more privileged)
action_min_level := {
	"create":  3,
	"update":  3,
	"delete":  2,
	"read":    7,
	"execute": 3,
	"approve": 2,
	"deploy":  3,
	"manage":  2,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Collect numeric levels for all roles the user holds that exist in the hierarchy
_user_levels := {lvl |
	some r in input.jwt.roles
	lvl := role_hierarchy[r]
}

# Best (lowest number = highest privilege) level the user holds.
# Evaluates to undefined when the user has no recognized roles.
_best_level := min(_user_levels) if count(_user_levels) > 0

# Best role name matching _best_level
_best_role := r if {
	some r in input.jwt.roles
	role_hierarchy[r] == _best_level
}

# Whether the action is one we know about
_known_action if action_min_level[input.action]

# Required level — undefined for unknown actions
_required_level := action_min_level[input.action] if _known_action

# ---------------------------------------------------------------------------
# Main rule — returns an object (never a bare boolean)
# The middleware does: opa_response.get("result", {}).get("allow", False)
#
# Uses `default` for the deny case so there is never a conflict when
# the allow condition is true (one path produces one object).
# ---------------------------------------------------------------------------

default allow := {
	"allow":       false,
	"user_info":   {},
	"deny_reason": "No recognized role or insufficient privilege",
}

# Allow when user has a recognized role with sufficient privilege
allow := result if {
	_best_level <= _required_level
	result := {
		"allow": true,
		"user_info": {
			"user_id":     input.jwt.user_id,
			"email":       input.jwt.email,
			"roles":       input.jwt.roles,
			"role_level":  _best_level,
			"is_admin":    _best_role == "admin",
			"permissions": [],
		},
		"deny_reason": null,
	}
}
