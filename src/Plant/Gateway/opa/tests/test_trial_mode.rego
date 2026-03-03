# test_trial_mode.rego — Unit tests for gateway.trial_mode
package gateway.trial_mode_test

import rego.v1

import data.gateway.trial_mode

# ---------------------------------------------------------------------------
# T1 — trial user accessing billing: DENY
# ---------------------------------------------------------------------------
test_trial_user_billing_denied if {
	result := trial_mode.allow with input as {
		"jwt":      {"user_id": "u1", "trial_mode": true, "roles": ["customer_admin"]},
		"resource": "billing",
		"action":   "read",
		"method":   "GET",
		"path":     "/api/v1/billing",
	}
	result.allow == false
	result.deny_reason != null
}

# ---------------------------------------------------------------------------
# T2 — trial user accessing invoices: DENY
# ---------------------------------------------------------------------------
test_trial_user_invoices_denied if {
	result := trial_mode.allow with input as {
		"jwt":      {"user_id": "u2", "trial_mode": true, "roles": ["customer_admin"]},
		"resource": "invoices",
		"action":   "read",
		"method":   "GET",
		"path":     "/api/v1/invoices",
	}
	result.allow == false
}

# ---------------------------------------------------------------------------
# T3 — trial user accessing subscriptions: DENY
# ---------------------------------------------------------------------------
test_trial_user_subscriptions_denied if {
	result := trial_mode.allow with input as {
		"jwt":      {"user_id": "u3", "trial_mode": true, "roles": ["customer_admin"]},
		"resource": "subscriptions",
		"action":   "read",
		"method":   "GET",
		"path":     "/api/v1/subscriptions",
	}
	result.allow == false
}

# ---------------------------------------------------------------------------
# T4 — trial user accessing agents (not blocked): ALLOW
# ---------------------------------------------------------------------------
test_trial_user_agents_allowed if {
	result := trial_mode.allow with input as {
		"jwt":      {"user_id": "u4", "trial_mode": true, "roles": ["customer_admin"]},
		"resource": "agents",
		"action":   "read",
		"method":   "GET",
		"path":     "/api/v1/agents",
	}
	result.allow == true
	result.deny_reason == null
}

# ---------------------------------------------------------------------------
# T5 — paid user accessing billing: ALLOW (trial_mode absent/false)
# ---------------------------------------------------------------------------
test_paid_user_billing_allowed if {
	result := trial_mode.allow with input as {
		"jwt":      {"user_id": "u5", "trial_mode": false, "roles": ["customer_admin"]},
		"resource": "billing",
		"action":   "read",
		"method":   "GET",
		"path":     "/api/v1/billing",
	}
	result.allow == true
}

# ---------------------------------------------------------------------------
# T6 — trial_mode key absent from JWT: ALLOW (defaults to non-trial)
# ---------------------------------------------------------------------------
test_missing_trial_mode_key_allows if {
	result := trial_mode.allow with input as {
		"jwt":      {"user_id": "u6", "roles": ["developer"]},
		"resource": "billing",
		"action":   "read",
		"method":   "GET",
		"path":     "/api/v1/billing",
	}
	result.allow == true
}
