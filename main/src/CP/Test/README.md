# CP Tests

Unit, integration, and end-to-end tests for Customer Portal.

## Directory Structure (To Be Created)

```
Test/
├── unit/               # Unit tests
│   ├── test_agents.py
│   ├── test_trials.py
│   └── test_subscriptions.py
├── integration/        # Integration tests
│   ├── test_api.py
│   └── test_database.py
├── e2e/                # End-to-end tests
│   ├── test_trial_flow.py
│   └── test_subscription_flow.py
└── conftest.py         # Pytest fixtures
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=main/src/CP/BackEnd --cov-report=html

# Run specific test file
pytest Test/unit/test_agents.py

# Run with verbose output
pytest -v
```

## Test Strategy

- **Unit Tests**: Test individual functions/methods in isolation
- **Integration Tests**: Test API endpoints with real database (test DB)
- **E2E Tests**: Test full user flows (signup → trial → subscription)

## Coverage Target

- Minimum: 80% overall
- Critical paths: 90%+ (trial signup, payment processing)
