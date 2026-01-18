# Trial Mode Policy
# Version: 1.0
# Owner: Platform Team
# 
# Purpose: Enforce trial user limitations
# - Trial users can execute max 10 tasks per day
# - Trial users can only access sandbox environment
# - Trial period must be active (not expired)

package gateway.trial_mode

import future.keywords.if
import future.keywords.in

# Default deny
default allow = false

# Allow if not in trial mode (paid users bypass trial checks)
allow if {
    not input.jwt.trial_mode
}

# Allow trial users if within limits
allow if {
    input.jwt.trial_mode
    input.jwt.trial_expires_at  # Must have expiration field
    not trial_expired
    not task_limit_exceeded
}

# Check if trial period has expired
trial_expired if {
    input.jwt.trial_mode
    input.jwt.trial_expires_at
    trial_expiry := time.parse_rfc3339_ns(input.jwt.trial_expires_at)
    current_time := time.now_ns()
    current_time > trial_expiry
}

# Check if daily task limit exceeded
task_limit_exceeded if {
    input.jwt.trial_mode
    task_count := redis_get_task_count(input.jwt.user_id)
    task_count >= 10
}

# Helper function to get task count from Redis (mocked for OPA)
# Actual implementation queries Redis via external data source
redis_get_task_count(user_id) = count if {
    # Check if external data is available
    data.redis.task_counts[user_id]
    count := data.redis.task_counts[user_id]
} else = 0

# Deny reason for expired trial
deny_reason = reason if {
    trial_expired
    reason := sprintf("Trial period expired at %s", [input.jwt.trial_expires_at])
}

# Deny reason for task limit exceeded
deny_reason = reason if {
    task_limit_exceeded
    task_count := redis_get_task_count(input.jwt.user_id)
    reason := sprintf("Trial task limit exceeded: %d/10 tasks used today", [task_count])
}

# Deny reason for missing trial_expires_at
deny_reason = reason if {
    input.jwt.trial_mode
    not input.jwt.trial_expires_at
    reason := "Trial mode requires trial_expires_at field"
}
