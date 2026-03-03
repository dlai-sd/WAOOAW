# sandbox_routing.rego — Sandbox environment routing policy
#
# Queries: POST /v1/data/gateway/sandbox_routing/allow
# Input:   {"input": {"jwt": {...}, "resource": str, "action": str,
#                     "method": str, "path": str}}
# Output:  {"result": {"allow": bool, "deny_reason": str|null}}
#
# Version 1 — passthrough
# ─────────────────────────────────────────────────────────────────────────────
# Sandbox routing decisions depend on runtime environment metadata (whether the
# target agent is running in a simulation sandbox vs production mode). That
# metadata is not present in the OPA input bundle today.
#
# Until the Plant Gateway forwards a sandbox context header (X-Sandbox-Mode)
# to OPA, this policy passes through all requests. The existing Python
# middleware applies sandbox-routing logic directly.
#
# Iteration 2 of this plan (PLANT-OPA-2) will introduce real sandbox-isolation
# rules once the context header is wired through.

package gateway.sandbox_routing

import rego.v1

allow := {"allow": true, "deny_reason": null}
