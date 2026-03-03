# test_governor_role.rego — Unit tests for gateway.governor_role
package gateway.governor_role_test

import rego.v1

import data.gateway.governor_role

# ---------------------------------------------------------------------------
# T1 — admin accessing a governor resource: ALLOW
# ---------------------------------------------------------------------------
test_admin_governor_resource_allowed if {
	result := governor_role.allow with input as {
		"jwt":      {"user_id": "u1", "roles": ["admin"]},
		"resource": "governor",
		"action":   "manage",
		"method":   "POST",
		"path":     "/api/v1/governor",
	}
	result.allow == true
	result.deny_reason == null
}

# ---------------------------------------------------------------------------
# T2 — customer_admin accessing platform_config: ALLOW
# ---------------------------------------------------------------------------
test_customer_admin_platform_config_allowed if {
	result := governor_role.allow with input as {
		"jwt":      {"user_id": "u2", "roles": ["customer_admin"]},
		"resource": "platform_config",
		"action":   "update",
		"method":   "PUT",
		"path":     "/api/v1/platform_config",
	}
	result.allow == true
}

# ---------------------------------------------------------------------------
# T3 — developer accessing governor resource: DENY
# ---------------------------------------------------------------------------
test_developer_governor_denied if {
	result := governor_role.allow with input as {
		"jwt":      {"user_id": "u3", "roles": ["developer"]},
		"resource": "governor",
		"action":   "manage",
		"method":   "POST",
		"path":     "/api/v1/governor",
	}
	result.allow == false
	result.deny_reason != null
}

# ---------------------------------------------------------------------------
# T4 — viewer accessing non-governor resource: ALLOW (pass-through)
# ---------------------------------------------------------------------------
test_viewer_non_governor_passthrough if {
	result := governor_role.allow with input as {
		"jwt":      {"user_id": "u4", "roles": ["viewer"]},
		"resource": "agents",
		"action":   "read",
		"method":   "GET",
		"path":     "/api/v1/agents",
	}
	result.allow == true
}

# ---------------------------------------------------------------------------
# T5 — support accessing feature_flags: DENY
# ---------------------------------------------------------------------------
test_support_feature_flags_denied if {
	result := governor_role.allow with input as {
		"jwt":      {"user_id": "u5", "roles": ["support"]},
		"resource": "feature_flags",
		"action":   "update",
		"method":   "PUT",
		"path":     "/api/v1/feature_flags",
	}
	result.allow == false
}
