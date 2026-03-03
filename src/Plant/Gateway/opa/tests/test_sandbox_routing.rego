# test_sandbox_routing.rego — Unit tests for gateway.sandbox_routing (v1 passthrough)
package gateway.sandbox_routing_test

import rego.v1

import data.gateway.sandbox_routing

# ---------------------------------------------------------------------------
# T1 — passthrough always allows
# ---------------------------------------------------------------------------
test_passthrough_allow if {
	result := sandbox_routing.allow with input as {
		"jwt":      {"user_id": "u1", "roles": ["developer"]},
		"resource": "agents",
		"action":   "create",
		"method":   "POST",
		"path":     "/api/v1/agents",
	}
	result.allow == true
	result.deny_reason == null
}

# ---------------------------------------------------------------------------
# T2 — passthrough with sandbox-style path
# ---------------------------------------------------------------------------
test_passthrough_sandbox_path if {
	result := sandbox_routing.allow with input as {
		"jwt":      {"user_id": "u2", "roles": ["customer_admin"]},
		"resource": "sandbox",
		"action":   "create",
		"method":   "POST",
		"path":     "/api/v1/sandbox/run",
	}
	result.allow == true
}
