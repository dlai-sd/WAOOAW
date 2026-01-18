# Sandbox Routing Policy Tests
# Version: 1.0

package gateway.sandbox_routing

test_route_trial_to_sandbox {
    route_to_sandbox with input as {
        "jwt": {
            "trial_mode": true,
            "user_id": "user-trial-001"
        }
    }
}

test_route_paid_to_production {
    not route_to_sandbox with input as {
        "jwt": {
            "trial_mode": false,
            "user_id": "user-paid-001"
        }
    }
}

test_target_url_sandbox {
    url := get_target_url with input as {
        "jwt": {
            "trial_mode": true
        }
    }
    with data.config.sandbox_url as "https://plant.sandbox.waooaw.com"
    url == "https://plant.sandbox.waooaw.com"
}

test_target_url_production {
    url := get_target_url with input as {
        "jwt": {
            "trial_mode": false
        }
    }
    with data.config.production_url as "https://plant.waooaw.com"
    url == "https://plant.waooaw.com"
}

test_target_url_fallback_sandbox {
    url := get_target_url with input as {
        "jwt": {
            "trial_mode": true
        }
    }
    # No data.config.sandbox_url provided
    url == "https://plant.sandbox.waooaw.com"
}

test_target_url_fallback_production {
    url := get_target_url with input as {
        "jwt": {
            "trial_mode": false
        }
    }
    # No data.config.production_url provided
    url == "https://plant.waooaw.com"
}

test_routing_decision_trial {
    decision := routing_decision with input as {
        "jwt": {
            "trial_mode": true,
            "user_id": "user-123",
            "customer_id": "cust-456"
        }
    }
    decision.route_to_sandbox == true
    decision.trial_mode == true
    decision.user_id == "user-123"
}

test_sandbox_config {
    config := sandbox_config with input as {
        "jwt": {
            "trial_mode": true
        }
    }
    config.environment == "sandbox"
    config.isolated == true
    config.data_retention_days == 7
    config.features.real_execution == false
    config.features.mock_apis == true
}

test_production_config {
    config := production_config with input as {
        "jwt": {
            "trial_mode": false
        }
    }
    config.environment == "production"
    config.isolated == false
    config.data_retention_days == 365
    config.features.real_execution == true
    config.features.cost_tracking == true
}

test_active_config_sandbox {
    config := active_config with input as {
        "jwt": {
            "trial_mode": true
        }
    }
    config.environment == "sandbox"
}

test_active_config_production {
    config := active_config with input as {
        "jwt": {
            "trial_mode": false
        }
    }
    config.environment == "production"
}
