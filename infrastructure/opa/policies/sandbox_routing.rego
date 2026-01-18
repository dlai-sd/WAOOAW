# Sandbox Routing Policy
# Version: 1.0
# Owner: Platform Team
#
# Purpose: Route trial users to sandbox environment
# - Trial users (trial_mode=true) use sandbox Plant API
# - Paid users use production Plant API
# - Sandbox provides isolated environment for testing

package gateway.sandbox_routing

import future.keywords.if

# Default routing
default route_to_sandbox = false
default target_url = ""

# Route trial users to sandbox
route_to_sandbox if {
    input.jwt.trial_mode == true
}

# Determine target URL based on trial mode
target_url = url if {
    input.jwt.trial_mode == true
    url := data.config.sandbox_url
} else = url if {
    url := data.config.production_url
}

# Get target URL with fallback
get_target_url = url if {
    input.jwt.trial_mode == true
    data.config.sandbox_url
    url := data.config.sandbox_url
} else = url if {
    input.jwt.trial_mode == true
    url := "https://plant.sandbox.waooaw.com"
} else = url if {
    data.config.production_url
    url := data.config.production_url
} else = "https://plant.waooaw.com"

# Routing decision
routing_decision = decision if {
    decision := {
        "route_to_sandbox": route_to_sandbox,
        "target_url": get_target_url,
        "trial_mode": input.jwt.trial_mode,
        "user_id": input.jwt.user_id,
        "customer_id": input.jwt.customer_id
    }
}

# Sandbox configuration
sandbox_config = config if {
    route_to_sandbox
    config := {
        "environment": "sandbox",
        "isolated": true,
        "data_retention_days": 7,
        "rate_limit_multiplier": 0.5,
        "features": {
            "real_execution": false,
            "mock_apis": true,
            "cost_tracking": false
        }
    }
}

# Production configuration
production_config = config if {
    not route_to_sandbox
    config := {
        "environment": "production",
        "isolated": false,
        "data_retention_days": 365,
        "rate_limit_multiplier": 1.0,
        "features": {
            "real_execution": true,
            "mock_apis": false,
            "cost_tracking": true
        }
    }
}

# Get active configuration
active_config = config if {
    route_to_sandbox
    config := sandbox_config
} else = production_config
