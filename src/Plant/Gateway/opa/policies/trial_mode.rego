# trial_mode.rego — Restrict access to billing/subscription resources during trials
#
# Queries: POST /v1/data/gateway/trial_mode/allow
# Input:   {"input": {"jwt": {"trial_mode": bool, ...}, "resource": str, "action": str,
#                     "method": str, "path": str}}
# Output:  {"result": {"allow": bool, "deny_reason": str|null}}
#
# Trial users (jwt.trial_mode == true) are blocked from:
#   invoices, subscriptions, billing
#
# All paid users (trial_mode == false or absent) are allowed unconditionally
# through this gate — the rbac_pp policy enforces privilege checks.

package gateway.trial_mode

import rego.v1

# Resources that trial users cannot access
trial_blocked_resources := {
	"invoices",
	"subscriptions",
	"billing",
}

# Default: allow (used when the deny condition below does not match)
default allow := {"allow": true, "deny_reason": null}

# Block trial users from restricted resources
allow := result if {
	input.jwt.trial_mode == true
	trial_blocked_resources[input.resource]
	result := {
		"allow":       false,
		"deny_reason": sprintf("trial accounts cannot access %v", [input.resource]),
	}
}
