# governor_role.rego — Governor-level operations require elevated roles
#
# Queries: POST /v1/data/gateway/governor_role/allow
# Input:   {"input": {"jwt": {"roles": [str], ...}, "resource": str, "action": str,
#                     "method": str, "path": str}}
# Output:  {"result": {"allow": bool, "deny_reason": str|null}}
#
# Governor actions (e.g. platform configuration, feature-flag overrides, agent
# lifecycle management) may only be performed by admins or customer_admins.
# For all other roles the request is passed through — rbac_pp is the primary
# privilege gate.

package gateway.governor_role

import rego.v1

governor_roles := {
	"admin",
	"customer_admin",
}

# Governor-controlled resources that require governor_roles
governor_resources := {
	"governor",
	"platform_config",
	"feature_flags",
}

# Default: allow (non-governor resources pass through)
default allow := {"allow": true, "deny_reason": null}

# Deny non-governor users from governor resources
allow := result if {
	governor_resources[input.resource]
	not _has_governor_role
	result := {
		"allow":       false,
		"deny_reason": sprintf("resource %v requires admin or customer_admin role", [input.resource]),
	}
}

_has_governor_role if {
	some r in input.jwt.roles
	governor_roles[r]
}
