# Agent Budget Policy
# Version: 1.0
# Owner: Platform Team
#
# Purpose: Enforce budget caps
# - Each agent limited to $1/day spending
# - Platform limited to $100/month total
# - Automatic throttling at thresholds

package gateway.agent_budget

import future.keywords.if
import future.keywords.in

# Budget caps (USD)
agent_daily_cap := 1.00
platform_monthly_cap := 100.00

# Cost guard thresholds
threshold_80 := 80.00
threshold_95 := 95.00
threshold_100 := 100.00

# Default deny
default allow = false
default budget_exceeded = false

# Allow if budgets not exceeded
allow if {
    not agent_budget_exceeded
    not platform_budget_exceeded
}

# Check agent daily budget
agent_budget_exceeded if {
    agent_spent := redis_get_agent_spent(input.agent_id)
    agent_spent >= agent_daily_cap
} else = false

# Check platform monthly budget
platform_budget_exceeded if {
    platform_spent := redis_get_platform_spent()
    platform_spent >= platform_monthly_cap
} else = false

# Get agent spending from Redis
redis_get_agent_spent(agent_id) = spent if {
    data.redis.agent_budgets[agent_id]
    budget := data.redis.agent_budgets[agent_id]
    spent := budget.spent_usd
} else = 0.0

# Get platform spending from Redis
redis_get_platform_spent() = spent if {
    data.redis.platform_budget
    spent := data.redis.platform_budget.spent_usd
} else = 0.0

# Calculate remaining budget for agent
agent_remaining = remaining if {
    spent := redis_get_agent_spent(input.agent_id)
    remaining := agent_daily_cap - spent
}

# Calculate remaining platform budget
platform_remaining = remaining if {
    spent := redis_get_platform_spent()
    remaining := platform_monthly_cap - spent
}

# Calculate platform budget utilization percentage
platform_utilization = percent if {
    spent := redis_get_platform_spent()
    percent := (spent / platform_monthly_cap) * 100
}

# Determine alert level based on utilization
alert_level = level if {
    utilization := platform_utilization
    utilization >= 100
    level := "critical"
} else = level if {
    utilization := platform_utilization
    utilization >= 95
    level := "high"
} else = level if {
    utilization := platform_utilization
    utilization >= 80
    level := "warning"
} else = "normal"

# Deny reasons
deny_reason = reason if {
    agent_budget_exceeded
    spent := redis_get_agent_spent(input.agent_id)
    reason := sprintf("Agent %s exceeded daily budget: $%.2f/$%.2f", [
        input.agent_id,
        spent,
        agent_daily_cap
    ])
}

deny_reason = reason if {
    platform_budget_exceeded
    spent := redis_get_platform_spent()
    reason := sprintf("Platform exceeded monthly budget: $%.2f/$%.2f", [
        spent,
        platform_monthly_cap
    ])
}

# Budget status information
budget_status = {
    "agent": {
        "agent_id": input.agent_id,
        "spent_usd": redis_get_agent_spent(input.agent_id),
        "cap_usd": agent_daily_cap,
        "remaining_usd": agent_remaining,
        "exceeded": agent_budget_exceeded
    },
    "platform": {
        "spent_usd": redis_get_platform_spent(),
        "cap_usd": platform_monthly_cap,
        "remaining_usd": platform_remaining,
        "utilization_percent": platform_utilization,
        "alert_level": alert_level,
        "exceeded": platform_budget_exceeded
    }
}
