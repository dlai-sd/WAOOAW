# agent_budget.rego — Budget guard policy for the Plant Gateway
#
# Queries: POST /v1/data/gateway/agent_budget/allow
# Input:   {"input": {"jwt": {...}, "agent_id": str, "customer_id": str, "path": str, "method": str}}
# Output:  {"result": {"allow": bool, "alert_level": str, "platform_utilization_percent": int,
#                      "agent_utilization_percent": int, "deny_reason": str|null}}
#
# Version 1 — passthrough
# ─────────────────────────────────────────────────────────────────────────────
# Budget utilization data lives in Redis (updated by Celery workers) and is NOT
# accessible to OPA at policy-evaluation time. Until a budget-data side-car
# (REST adapter over Redis) is wired in, this policy always passes through to
# let the existing Python middleware perform the Redis-backed budget check.
#
# Iteration 2 of this plan (PLANT-OPA-2) will replace this passthrough with
# real budget rules once the data feed is in place.

package gateway.agent_budget

import rego.v1

allow := {
	"allow":                         true,
	"alert_level":                   "normal",
	"platform_utilization_percent":  0,
	"agent_utilization_percent":     0,
	"deny_reason":                   null,
}
