# WAOOAW Testing Guide

## Test Structure

```
tests/
├── unit/              # Fast tests with mocked dependencies
├── integration/       # Tests with real database/Redis
├── e2e/              # Full stack end-to-end tests
├── conftest.py       # Shared fixtures
├── requirements.txt  # Test dependencies
└── docker-compose.test.yml  # Test services
```

## Running Tests

### 1. Unit Tests (Fast - No Services Needed)

```bash
# Install dependencies
pip install -r tests/requirements.txt

# Run all unit tests
pytest -m unit

# Run with coverage
pytest -m unit --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py
```

### 2. Integration Tests (Real Services Required)

```bash
# Start test services
docker-compose -f tests/docker-compose.test.yml up -d

# Wait for services to be healthy
sleep 5

# Run integration tests
TEST_MODE=integration pytest -m integration

# Stop test services
docker-compose -f tests/docker-compose.test.yml down
```

### 3. End-to-End Tests (Full Stack)

```bash
# Start all services
docker-compose -f tests/docker-compose.test.yml up -d

# Run E2E tests
TEST_MODE=e2e pytest -m e2e

# Stop services
docker-compose -f tests/docker-compose.test.yml down
```

### 4. Run All Tests

```bash
# Start services
docker-compose -f tests/docker-compose.test.yml up -d

# Run all tests (unit, integration, e2e)
TEST_MODE=integration pytest

# Stop services
docker-compose -f tests/docker-compose.test.yml down
```

## Test Markers

Mark tests with appropriate markers:

```python
import pytest

@pytest.mark.unit
def test_pure_function():
    """Fast test with no dependencies."""
    assert add(1, 2) == 3

@pytest.mark.integration
async def test_database_query(test_database_url):
    """Test with real database."""
    # Uses real PostgreSQL from docker-compose.test.yml
    pass

@pytest.mark.e2e
async def test_full_user_journey():
    """Test complete user flow."""
    pass

@pytest.mark.slow
def test_expensive_operation():
    """Test that takes > 5 seconds."""
    pass
```

## Environment Variables

```bash
# Test mode (unit, integration, e2e)
export TEST_MODE=unit

# Test database (for integration/e2e)
export TEST_DATABASE_URL=postgresql://waooaw_test:waooaw_test_password@localhost:5433/waooaw_test_db

# Test Redis (for integration/e2e)
export TEST_REDIS_URL=redis://localhost:6380/0
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r tests/requirements.txt
      - name: Run unit tests
        run: pytest -m unit --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start test services
        run: docker-compose -f tests/docker-compose.test.yml up -d
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r tests/requirements.txt
      - name: Run integration tests
        run: TEST_MODE=integration pytest -m integration
      - name: Stop test services
        run: docker-compose -f tests/docker-compose.test.yml down
```

## Coverage Reports

After running tests with coverage:

```bash
# View HTML report
open htmlcov/index.html

# View in terminal
pytest --cov=src --cov-report=term-missing
```

## Performance Testing

Run benchmarks:

```bash
pytest tests/ --benchmark-only
```

## Parallel Execution

Speed up test runs:

```bash
# Auto-detect CPU cores
pytest -n auto

# Specific number of workers
pytest -n 4
```

## Best Practices

1. **Unit tests should be fast** (< 1 second each)
2. **Mock external dependencies** in unit tests
3. **Use fixtures** for common setup
4. **Mark slow tests** with `@pytest.mark.slow`
5. **Clean up resources** in fixtures (use `yield`)
6. **Test edge cases** and error conditions
7. **Use descriptive test names** that explain what's being tested

## Troubleshooting

### Tests fail with "connection refused"

```bash
# Check if test services are running
docker-compose -f tests/docker-compose.test.yml ps

# Check service health
docker-compose -f tests/docker-compose.test.yml logs postgres-test

# Restart services
docker-compose -f tests/docker-compose.test.yml restart
```

### Port conflicts

```bash
# Stop conflicting services
docker-compose -f tests/docker-compose.test.yml down

# Change ports in docker-compose.test.yml if needed
```

### Slow tests

```bash
# Identify slow tests
pytest --durations=10

# Run only fast tests
pytest -m "not slow"
```
