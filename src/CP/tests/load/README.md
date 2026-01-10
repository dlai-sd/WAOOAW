# Load Testing

This directory contains load and performance tests for the CP backend using Locust.

## Running Locally

### Install Locust
```bash
pip install locust
```

### Start Backend
```bash
cd src/CP/BackEnd
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Run Load Tests

**Basic Load Test** (50 users, 2 minutes):
```bash
locust -f src/CP/tests/load/locustfile.py \
  --headless \
  --users 50 \
  --spawn-rate 10 \
  --run-time 2m \
  --host http://localhost:8000
```

**Stress Test** (500 users, 5 minutes):
```bash
locust -f src/CP/tests/load/locustfile.py \
  --headless \
  --users 500 \
  --spawn-rate 50 \
  --run-time 5m \
  --host http://localhost:8000 \
  --csv stress-test-results
```

**Web UI Mode** (interactive):
```bash
locust -f src/CP/tests/load/locustfile.py \
  --host http://localhost:8000
# Open http://localhost:8089
```

## Test Scenarios

### CPBackendUser
- **Health Checks** (3x weight): Basic availability
- **Auth Health** (2x weight): Auth service availability
- **API Docs** (1x weight): Documentation access

### CPStressTest
- Rapid-fire requests with minimal wait time
- Tests system under high concurrency

### CPEnduranceTest
- Long-running sustained load
- Tests memory leaks and resource exhaustion

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| **Response Time (p95)** | < 200ms | < 500ms |
| **Response Time (p99)** | < 500ms | < 1000ms |
| **Error Rate** | < 0.1% | < 1% |
| **Throughput** | > 100 RPS | > 50 RPS |

## CI/CD Integration

Load tests run in GitHub Actions when `run_load_tests` is enabled:
- 50 users, 10 spawn rate
- 2 minute duration
- Generates HTML report and CSV results

## Interpreting Results

### Good Signs ✅
- Response times stable over duration
- Error rate near 0%
- Throughput increases linearly with users

### Warning Signs ⚠️
- Response times increasing over time (memory leak)
- Error rate > 0.1%
- CPU/memory maxing out

### Critical Issues ❌
- Response times > 1 second
- Error rate > 1%
- Service crashes or timeouts
