# test_rbac_pp.rego — Unit tests for gateway.rbac_pp
package gateway.rbac_pp_test

import rego.v1

import data.gateway.rbac_pp

# ---------------------------------------------------------------------------
# T1 — admin creating a resource: ALLOW
# ---------------------------------------------------------------------------
test_admin_create_allowed if {
	result := rbac_pp.allow with input as {
		"resource": "agents",
		"action":   "create",
		"jwt":      {"user_id": "u1", "email": "admin@waooaw.com", "roles": ["admin"]},
	}
	result.allow == true
	result.user_info.is_admin == true
	result.deny_reason == null
}

# ---------------------------------------------------------------------------
# T2 — viewer trying to create: DENY (level 7 > required 3)
# ---------------------------------------------------------------------------
test_viewer_create_denied if {
	result := rbac_pp.allow with input as {
		"resource": "agents",
		"action":   "create",
		"jwt":      {"user_id": "u2", "email": "viewer@waooaw.com", "roles": ["viewer"]},
	}
	result.allow == false
	result.deny_reason != null
}

# ---------------------------------------------------------------------------
# T3 — viewer reading a resource: ALLOW (level 7 <= required 7)
# ---------------------------------------------------------------------------
test_viewer_read_allowed if {
	result := rbac_pp.allow with input as {
		"resource": "agents",
		"action":   "read",
		"jwt":      {"user_id": "u3", "email": "viewer@waooaw.com", "roles": ["viewer"]},
	}
	result.allow == true
	result.deny_reason == null
}

# ---------------------------------------------------------------------------
# T4 — completely unknown role: DENY
# ---------------------------------------------------------------------------
test_unknown_role_denied if {
	result := rbac_pp.allow with input as {
		"resource": "agents",
		"action":   "read",
		"jwt":      {"user_id": "u4", "email": "ghost@waooaw.com", "roles": ["ghost"]},
	}
	result.allow == false
}

# ---------------------------------------------------------------------------
# T5 — DB Updates safety: admin performing POST on /admin resource: ALLOW
#
# PP sends POST /api/v1/admin/db/execute.
# Plant Gateway strips prefix → resource="admin", action="create".
# Admin level 1 <= required level for "create" (3) → allow.
# ---------------------------------------------------------------------------
test_admin_db_updates_allowed if {
	result := rbac_pp.allow with input as {
		"resource": "admin",
		"action":   "create",
		"jwt":      {"user_id": "u5", "email": "dba@waooaw.com", "roles": ["admin"]},
	}
	result.allow == true
	result.user_info.is_admin == true
}

# ---------------------------------------------------------------------------
# T6 — developer hitting /admin resource: ALLOW at OPA gate
#
# developer level 3 == action_min_level["create"] == 3 → allow=true
# Plant Backend is gate 2 and enforces its own admin-only hard check
# (_require_admin_via_gateway) — a developer will never reach DB execute
# because Plant Backend will reject them at layer 2.
# OPA is intentionally permissive here; Plant Backend is the authoritative gate.
# ---------------------------------------------------------------------------
test_developer_admin_resource_opa_passthrough if {
	result := rbac_pp.allow with input as {
		"resource": "admin",
		"action":   "create",
		"jwt":      {"user_id": "u6", "email": "dev@waooaw.com", "roles": ["developer"]},
	}
	result.allow == true
	result.user_info.is_admin == false
}

# ---------------------------------------------------------------------------
# T7 — manager can approve (level 4 <= required 2? NO — 4 > 2 → DENY)
# ---------------------------------------------------------------------------
test_manager_approve_denied if {
	result := rbac_pp.allow with input as {
		"resource": "payments",
		"action":   "approve",
		"jwt":      {"user_id": "u7", "email": "mgr@waooaw.com", "roles": ["manager"]},
	}
	result.allow == false
}

# ---------------------------------------------------------------------------
# T8 — customer_admin can approve (level 2 <= required 2 → ALLOW)
# ---------------------------------------------------------------------------
test_customer_admin_approve_allowed if {
	result := rbac_pp.allow with input as {
		"resource": "payments",
		"action":   "approve",
		"jwt":      {"user_id": "u8", "email": "ca@waooaw.com", "roles": ["customer_admin"]},
	}
	result.allow == true
}

# ---------------------------------------------------------------------------
# T9 — user with multiple roles uses best (lowest) level
# roles: ["manager", "developer"] → levels [4, 3] → best = 3
# action "create" requires level 3 → ALLOW
# ---------------------------------------------------------------------------
test_multi_role_uses_best_level if {
	result := rbac_pp.allow with input as {
		"resource": "deployments",
		"action":   "create",
		"jwt":      {"user_id": "u9", "email": "multi@waooaw.com", "roles": ["manager", "developer"]},
	}
	result.allow == true
}
