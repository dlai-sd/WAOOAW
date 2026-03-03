# test_agent_budget.rego — Unit tests for gateway.agent_budget (v1 passthrough)
package gateway.agent_budget_test

import rego.v1

import data.gateway.agent_budget

# ---------------------------------------------------------------------------
# T1 — passthrough always allows, returns normal alert level
# ---------------------------------------------------------------------------
test_passthrough_allow if {
	result := agent_budget.allow with input as {
		"jwt":         {"user_id": "u1", "email": "user@waooaw.com", "roles": ["customer_admin"]},
		"agent_id":    "agent-abc",
		"customer_id": "cust-123",
		"path":        "/api/v1/agents/agent-abc/run",
		"method":      "POST",
	}
	result.allow == true
	result.alert_level == "normal"
	result.platform_utilization_percent == 0
	result.agent_utilization_percent == 0
	result.deny_reason == null
}

# ---------------------------------------------------------------------------
# T2 — passthrough works with empty agent_id (edge case)
# ---------------------------------------------------------------------------
test_passthrough_empty_agent if {
	result := agent_budget.allow with input as {
		"jwt":         {"user_id": "u2", "email": "user@waooaw.com", "roles": ["viewer"]},
		"agent_id":    "",
		"customer_id": "cust-999",
		"path":        "/api/v1/status",
		"method":      "GET",
	}
	result.allow == true
}
