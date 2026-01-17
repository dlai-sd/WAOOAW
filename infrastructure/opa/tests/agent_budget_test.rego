# Agent Budget Policy Tests
# Version: 1.0

package gateway.agent_budget

test_allow_within_budgets {
    allow with input as {
        "agent_id": "agent_001"
    }
    with data.redis.agent_budgets as {
        "agent_001": {"spent_usd": 0.50}
    }
    with data.redis.platform_budget as {
        "spent_usd": 50.00
    }
}

test_deny_agent_budget_exceeded {
    not allow with input as {
        "agent_id": "agent_002"
    }
    with data.redis.agent_budgets as {
        "agent_002": {"spent_usd": 1.50}
    }
    with data.redis.platform_budget as {
        "spent_usd": 50.00
    }
}

test_deny_platform_budget_exceeded {
    not allow with input as {
        "agent_id": "agent_003"
    }
    with data.redis.agent_budgets as {
        "agent_003": {"spent_usd": 0.50}
    }
    with data.redis.platform_budget as {
        "spent_usd": 105.00
    }
}

test_agent_remaining_budget {
    remaining := agent_remaining with input as {
        "agent_id": "agent_004"
    }
    with data.redis.agent_budgets as {
        "agent_004": {"spent_usd": 0.30}
    }
    remaining == 0.70
}

test_platform_utilization {
    utilization := platform_utilization with data.redis.platform_budget as {
        "spent_usd": 80.00
    }
    utilization == 80.0
}

test_alert_level_normal {
    level := alert_level with data.redis.platform_budget as {
        "spent_usd": 50.00
    }
    level == "normal"
}

test_alert_level_warning {
    level := alert_level with data.redis.platform_budget as {
        "spent_usd": 85.00
    }
    level == "warning"
}

test_alert_level_high {
    level := alert_level with data.redis.platform_budget as {
        "spent_usd": 97.00
    }
    level == "high"
}

test_alert_level_critical {
    level := alert_level with data.redis.platform_budget as {
        "spent_usd": 102.00
    }
    level == "critical"
}

test_deny_reason_agent_exceeded {
    reason := deny_reason with input as {
        "agent_id": "agent_005"
    }
    with data.redis.agent_budgets as {
        "agent_005": {"spent_usd": 1.25}
    }
    with data.redis.platform_budget as {
        "spent_usd": 50.00
    }
    contains(reason, "Agent agent_005 exceeded")
    contains(reason, "$1.25/$1.00")
}

test_budget_status_structure {
    status := budget_status with input as {
        "agent_id": "agent_006"
    }
    with data.redis.agent_budgets as {
        "agent_006": {"spent_usd": 0.40}
    }
    with data.redis.platform_budget as {
        "spent_usd": 70.00
    }
    
    status.agent.agent_id == "agent_006"
    status.agent.spent_usd == 0.40
    status.platform.spent_usd == 70.00
    status.platform.utilization_percent == 70.0
}
