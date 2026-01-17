# Trial Mode Policy Tests
# Version: 1.0

package gateway.trial_mode

test_allow_paid_user {
    allow with input as {
        "jwt": {
            "user_id": "user-123",
            "trial_mode": false
        }
    }
}

test_allow_trial_user_within_limits {
    allow with input as {
        "jwt": {
            "user_id": "user-456",
            "trial_mode": true,
            "trial_expires_at": "2026-12-31T23:59:59Z"
        }
    }
    with data.redis.task_counts as {"user-456": 5}
}

test_deny_trial_user_expired {
    not allow with input as {
        "jwt": {
            "user_id": "user-789",
            "trial_mode": true,
            "trial_expires_at": "2020-01-01T00:00:00Z"
        }
    }
    with data.redis.task_counts as {"user-789": 3}
}

test_deny_trial_user_limit_exceeded {
    not allow with input as {
        "jwt": {
            "user_id": "user-101",
            "trial_mode": true,
            "trial_expires_at": "2026-12-31T23:59:59Z"
        }
    }
    with data.redis.task_counts as {"user-101": 10}
}

test_deny_trial_user_missing_expiration {
    not allow with input as {
        "jwt": {
            "user_id": "user-202",
            "trial_mode": true
        }
    }
}

test_deny_reason_expired {
    reason := deny_reason with input as {
        "jwt": {
            "user_id": "user-303",
            "trial_mode": true,
            "trial_expires_at": "2020-01-01T00:00:00Z"
        }
    }
    contains(reason, "expired")
}

test_deny_reason_limit_exceeded {
    reason := deny_reason with input as {
        "jwt": {
            "user_id": "user-404",
            "trial_mode": true,
            "trial_expires_at": "2026-12-31T23:59:59Z"
        }
    }
    with data.redis.task_counts as {"user-404": 12}
    contains(reason, "exceeded")
    contains(reason, "12/10")
}
