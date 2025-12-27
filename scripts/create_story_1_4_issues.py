#!/usr/bin/env python3
"""Create GitHub issues for Story 1.4 technical decisions and future work"""

import subprocess
import sys

ISSUES = [
    {
        "title": "Add real GitHub webhook fixtures to E2E tests",
        "body": """**Context**: Story 1.4 E2E tests use synthetic webhook payloads

**Current Approach**:
- Tests use minimal payloads (10-15 fields)
- Synthetic data constructed manually
- Works but misses edge cases

**Problem**:
- Real GitHub webhooks have 50+ fields
- Null values, extra fields, nested objects
- Edge cases not covered (empty arrays, missing optional fields)

**Proposed Solution**:
Add real webhook fixture files captured from GitHub:
- `tests/fixtures/github_push_payload.json` (real push webhook)
- `tests/fixtures/github_pr_opened_payload.json` (real PR webhook)
- `tests/fixtures/github_issue_comment_payload.json` (real comment webhook)

Benefits:
- Catch serialization edge cases
- Validate against real GitHub schema
- Test backwards compatibility with GitHub API changes

**Acceptance Criteria**:
- [ ] Capture 5+ real webhook payloads from GitHub
- [ ] Add to `tests/fixtures/` directory
- [ ] Update E2E tests to use fixtures
- [ ] Verify all tests still pass
- [ ] Document fixture collection process

**Priority**: Medium  
**Effort**: 2 hours  
**Story**: 1.4 E2E Wake Test""",
        "labels": ["testing", "fixtures"]
    },
    {
        "title": "Add performance regression tests for wake latency",
        "body": """**Context**: Story 1.4 measures wake latency (p50/p95/p99) but doesn't track trends

**Current State**:
- E2E tests measure latency: p50=45ms, p95=89ms
- Meets <5s p95 requirement ✅
- But no tracking over time

**Problem**:
- Performance degradations not detected until production
- No baseline for comparison
- Architectural changes may slow down wake

**Proposed Solution**:
Track latency metrics over time:

```python
# tests/performance/test_wake_latency_regression.py

def test_wake_latency_p95_regression():
    \"\"\"Ensure p95 wake latency doesn't regress\"\"\"
    latencies = measure_wake_latency(n=100)
    p95 = percentile(latencies, 95)
    
    # Historical baseline
    assert p95 < 150ms, f"p95 regressed to {p95}ms (baseline: 89ms)"
    
    # SLA requirement
    assert p95 < 5000ms, f"p95 {p95}ms exceeds 5s SLA"
```

Store baselines:
- `tests/performance/baselines.json`
- Track p50, p95, p99 over commits
- Alert if >20% regression

CI/CD integration:
- Run performance tests on PRs
- Comment with latency comparison
- Block merge if >20% regression

**Acceptance Criteria**:
- [ ] Add performance test suite
- [ ] Store baseline metrics
- [ ] CI/CD integration (GitHub Actions)
- [ ] Alert on regression (comment on PR)
- [ ] Dashboard for tracking trends

**Priority**: High  
**Effort**: 4 hours  
**Story**: 1.4 E2E Wake Test  
**Dependencies**: Story 1.4 baseline metrics""",
        "labels": ["testing"]
    },
    {
        "title": "Add E2E tests for all 14 Platform CoE agents",
        "body": """**Context**: Story 1.4 E2E tests validate WowVision Prime wake pattern

**Current Coverage**:
- ✅ WowVision Prime (tested)
- ❌ 13 other Platform CoE agents (not tested)

**Problem**:
All 14 Platform CoE agents should follow same wake pattern:
1. Subscribe to topics
2. Evaluate should_wake()
3. Load context
4. Execute action

But only WowVision Prime is E2E tested.

**Proposed Solution**:
Extend E2E test suite to all Platform CoE agents:

```python
# tests/test_e2e_wake_all_agents.py

@pytest.mark.parametrize("agent_class,event_type", [
    (WowVisionPrime, EVENT_FILE_CREATED),
    (ProjectPlanner, EVENT_PR_OPENED),
    (TechWriter, EVENT_FILE_CREATED),
    (CodeReviewer, EVENT_PR_OPENED),
    # ... all 14 agents
])
def test_agent_wake_protocol(agent_class, event_type):
    \"\"\"Validate wake protocol for each agent\"\"\"
    agent = agent_class()
    
    # Publish event
    message_bus.publish(event)
    
    # Agent wakes
    assert agent.should_wake(event) == True
    
    # Agent processes
    result = agent.process_event(event)
    assert result is not None
```

Test scenarios per agent:
- Wake on relevant events
- Skip irrelevant events  
- Handle errors gracefully
- Meet latency SLA (<5s p95)

**Acceptance Criteria**:
- [ ] E2E tests for all 14 Platform CoE agents
- [ ] Parametrized test suite (one test, 14 agents)
- [ ] Agent-specific event scenarios
- [ ] Wake latency validated for each agent
- [ ] All tests passing (100%)

**Priority**: High  
**Effort**: 8 hours  
**Story**: 1.4 E2E Wake Test  
**Blocked By**: None (can start after Story 1.4)  
**Blocks**: Epic 2 (GitHub Integration)""",
        "labels": ["testing"]
    },
    {
        "title": "Add chaos testing for Redis failures and network partitions",
        "body": """**Context**: Story 1.4 tests basic error handling (Redis unavailable)

**Current Coverage**:
- ✅ Redis connection error (startup)
- ✅ Partial message bus failures
- ❌ Redis connection drops (mid-operation)
- ❌ Network partitions
- ❌ Redis failover scenarios
- ❌ Stream corruption

**Problem**:
Production failures are more complex:
- Redis crashes during agent wake
- Network partition (agent can't reach Redis)
- Redis leader failover (Redis Sentinel/Cluster)
- Stream corruption (bad data in Redis)

Current tests don't validate resilience to these scenarios.

**Proposed Solution**:
Add chaos testing library (e.g., `chaos-toolkit`, `toxiproxy`):

```python
# tests/chaos/test_redis_failure_scenarios.py

def test_agent_wake_during_redis_crash():
    \"\"\"Simulate Redis crash mid-wake\"\"\"
    # Start wake
    agent.start_wake()
    
    # Crash Redis
    chaos.kill_redis()
    
    # Should retry and eventually succeed
    assert agent.wait_for_wake(timeout=10s)

def test_network_partition_during_publish():
    \"\"\"Simulate network partition\"\"\"
    # Introduce latency
    toxiproxy.add_latency(redis_proxy, latency_ms=5000)
    
    # Publish should timeout gracefully
    with pytest.raises(TimeoutError):
        message_bus.publish(event, timeout=2s)

def test_redis_failover_mid_stream():
    \"\"\"Simulate Redis Sentinel failover\"\"\"
    # Start consuming
    consumer.start()
    
    # Trigger failover
    redis_sentinel.failover()
    
    # Consumer should reconnect
    assert consumer.is_healthy(timeout=10s)
```

Scenarios:
1. Redis crashes during agent wake
2. Network partition (high latency)
3. Redis leader failover
4. Stream corruption (bad JSON)
5. Consumer group rebalancing
6. Full Redis restart

**Acceptance Criteria**:
- [ ] Chaos testing framework integrated
- [ ] 6+ failure scenarios tested
- [ ] Agent retries and recovers gracefully
- [ ] No message loss during failures
- [ ] Documentation: failure modes and recovery

**Priority**: Medium  
**Effort**: 6 hours  
**Story**: 1.4 E2E Wake Test  
**Dependencies**: Docker/toxiproxy setup""",
        "labels": ["testing"]
    }
]

def create_issues():
    """Create GitHub issues using gh CLI"""
    for issue in ISSUES:
        title = issue["title"]
        body = issue["body"]
        labels = ",".join(issue["labels"])
        
        print(f"Creating issue: {title}")
        
        result = subprocess.run(
            ["gh", "issue", "create", "--title", title, "--body", body, "--label", labels],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Created: {result.stdout.strip()}")
        else:
            print(f"❌ Failed: {result.stderr}")
            sys.exit(1)
    
    print(f"\n🎉 Created {len(ISSUES)} GitHub issues for Story 1.4 follow-up work")

if __name__ == "__main__":
    create_issues()
