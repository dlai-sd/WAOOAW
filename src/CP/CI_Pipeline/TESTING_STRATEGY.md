# CP Testing Strategy

**Coverage Target**: 95% (Progressive improvement from current 79%)  
**Last Updated**: January 10, 2026

---

## Testing Pyramid

```
         /\
        /UI\          5% - UI/E2E Tests (Playwright)
       /----\
      / API  \        15% - API/Integration Tests
     /--------\
    /   Unit   \      80% - Unit Tests (Fast, Isolated)
   /------------\
```

---

## 1. Unit Tests

**Target Coverage**: 95% of business logic  
**Current**: 79% (46 tests)  
**Tools**: pytest (backend), vitest (frontend)

### Backend Unit Tests (`pytest`)
**Location**: `src/CP/BackEnd/tests/`

- **test_auth.py**: Auth endpoint tests
- **test_jwt.py**: JWT token creation/validation
- **test_jwt_advanced.py**: Edge cases, expiry, malformed tokens
- **test_dependencies.py**: Auth middleware, decorators
- **test_user_store.py**: User CRUD operations
- **test_config.py**: Configuration properties
- **test_routes.py**: Route validation

**Run Locally**:
```bash
cd src/CP/BackEnd
pytest tests/ -v --cov=api --cov=core --cov=models --cov-report=html
```

**Coverage Targets by Module**:
- `core/`: 100% ✅
- `models/`: 100% ✅
- `api/auth/dependencies.py`: 100% ✅
- `api/auth/user_store.py`: 100% ✅
- `api/auth/routes.py`: Target 80% (OAuth integration)
- `api/auth/google_oauth.py`: Target 70% (external API)

### Frontend Unit Tests (`vitest`)
**Location**: `src/CP/FrontEnd/src/__tests__/`, `src/CP/FrontEnd/src/test/`

- Component tests (GoogleLoginButton, AuthModal, etc.)
- Hook tests (useAuth)
- Service tests (auth.service)
- Page tests (Dashboard, MyAgents, Approvals)

**Run Locally**:
```bash
cd src/CP/FrontEnd
npm test
npm run test:coverage
```

---

## 2. Integration Tests

**Target Coverage**: Critical API flows  
**Tools**: pytest with TestClient, API mocking

### Backend Integration Tests
**Location**: `src/CP/BackEnd/tests/test_integration.py`

**Current Tests**:
- API health check
- Auth service health check
- API documentation availability

**To Add** (for 95% coverage):
- [ ] Full OAuth flow (mock Google)
- [ ] Token refresh flow
- [ ] User session management
- [ ] Cross-module interactions
- [ ] Database operations (when DB added)

**Run Locally**:
```bash
cd src/CP/BackEnd
pytest tests/ -v -m "integration"
```

### Frontend Integration Tests
**To Add**:
- [ ] Auth context provider tests
- [ ] API service integration
- [ ] Router navigation tests
- [ ] Theme provider tests

---

## 3. Regression Tests

**Purpose**: Prevent breaking changes  
**Tools**: pytest baseline comparison

**Location**: Runs same test suite, compares with baseline

**Strategy**:
1. Store baseline test results in artifact
2. Run full test suite on every PR
3. Compare results: new failures = regression
4. Block PR if regressions detected

**Run in CI**:
```yaml
- Enable: run_regression_tests: true
- Runs all unit + integration tests
- Compares with previous successful run
```

---

## 4. Load & Performance Tests

**Target**: 100 RPS, p95 < 200ms  
**Tools**: Locust

**Location**: `src/CP/tests/load/locustfile.py`

### Test Scenarios

**1. CPBackendUser** (Normal Load)
- 50 concurrent users
- 10 users/second spawn rate
- 2 minute duration
- Simulates typical user behavior

**2. CPStressTest** (Stress)
- 500 concurrent users
- High request rate
- Tests system limits

**3. CPEnduranceTest** (Endurance)
- Long-running (30+ minutes)
- Tests memory leaks
- Resource exhaustion

### Performance SLAs

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Response Time (p95) | < 200ms | 200-500ms | > 500ms |
| Response Time (p99) | < 500ms | 500-1000ms | > 1000ms |
| Error Rate | < 0.1% | 0.1-1% | > 1% |
| Throughput | > 100 RPS | 50-100 RPS | < 50 RPS |
| CPU Usage | < 70% | 70-90% | > 90% |
| Memory Usage | < 80% | 80-95% | > 95% |

**Run Locally**:
```bash
# Start backend
cd src/CP/BackEnd
uvicorn main:app --host 0.0.0.0 --port 8000

# Run load test
locust -f src/CP/tests/load/locustfile.py \
  --headless --users 50 --spawn-rate 10 --run-time 2m \
  --host http://localhost:8000
```

**Run in CI**:
```yaml
- Enable: run_load_tests: true
- Runs on staging environment
- Generates HTML report + CSV results
```

---

## 5. UI Tests (E2E)

**Target**: Critical user journeys  
**Tools**: Playwright

**Location**: `src/CP/FrontEnd/e2e/`

### Test Suites

**1. Landing Page** (`app.spec.ts`)
- Page loads correctly
- Theme toggle works
- Responsive design (mobile, tablet, desktop)

**2. Authentication Flow**
- Sign in button opens modal
- Modal closes on outside click
- Google OAuth button visible
- (Future) Complete login flow

**3. Authenticated Portal**
- Dashboard loads
- Navigation works
- Agent list displays
- Approvals workflow

**4. Accessibility**
- No a11y violations
- Keyboard navigation
- Screen reader compatibility
- ARIA labels present

**5. Performance**
- Page load < 3 seconds
- First Contentful Paint < 1.5s
- Time to Interactive < 3.5s

### Browser Coverage
- ✅ Chromium (Desktop)
- ✅ Firefox (Desktop)
- ✅ WebKit/Safari (Desktop)
- ✅ Mobile Chrome (Pixel 5)
- ✅ Mobile Safari (iPhone 12)
- ✅ Microsoft Edge
- ✅ Google Chrome

**Run Locally**:
```bash
cd src/CP/FrontEnd
npm run test:e2e          # Run all tests
npm run test:e2e:ui       # Interactive mode
npm run test:e2e:debug    # Debug mode
```

**Run in CI**:
```yaml
- Enable: run_ui_tests: true
- Runs against preview build
- Generates HTML report with screenshots
```

---

## 6. Security Testing

**Continuous**: Every pipeline run  
**Tools**: pip-audit, bandit, safety (backend), npm audit (frontend), Trivy (containers)

### Backend Security
1. **pip-audit**: CVE scanning for Python packages
2. **bandit**: SAST for Python code
3. **safety**: Dependency vulnerability database

### Frontend Security
1. **npm audit**: NPM security advisories
2. **ESLint security rules**: Code patterns

### Container Security
1. **Trivy**: Multi-layer container scanning
   - OS packages
   - Application dependencies
   - Misconfigurations

**Always Runs**: Enabled by default in pipeline

---

## 7. Code Review & Quality

**Tools**: CodeQL, SonarCloud

### CodeQL
- Automated code scanning
- Security vulnerability detection
- Code quality issues

### SonarCloud
- **Coverage**: Tracks test coverage trends
- **Bugs**: Identifies potential bugs
- **Code Smells**: Maintainability issues
- **Security Hotspots**: Security risks
- **Duplications**: Code duplication

**Quality Gates**:
- Coverage: 95% (target)
- Bugs: 0
- Vulnerabilities: 0
- Code Smells: < 10
- Security Hotspots: 0
- Duplications: < 3%

---

## Pipeline Execution Matrix

| Test Type | Manual | PR | Push | Scheduled | Duration |
|-----------|--------|----|----|-----------|----------|
| **Unit Tests** | ✅ | ✅ | ✅ | Daily | ~30s |
| **Integration** | ✅ | ✅ | ✅ | Daily | ~1min |
| **Regression** | ✅ | ✅ | ✅ | Daily | ~2min |
| **Load Tests** | ✅ | ❌ | ❌ | Weekly | ~5min |
| **UI Tests** | ✅ | ✅ | ✅ | Daily | ~3min |
| **Security** | ✅ | ✅ | ✅ | Daily | ~2min |
| **Code Review** | ✅ | ✅ | ✅ | Daily | ~1min |

**Total Pipeline Time**: ~10 minutes (without load tests)

---

## Roadmap to 95% Coverage

### Phase 1: Current (79%) ✅
- [x] Core unit tests
- [x] Basic integration tests
- [x] JWT and auth tests
- [x] User store tests

### Phase 2: Integration (Target: 85%)
- [ ] OAuth flow integration tests
- [ ] Token refresh flow tests
- [ ] User session tests
- [ ] API error handling tests

### Phase 3: Edge Cases (Target: 90%)
- [ ] Concurrency tests
- [ ] Rate limiting tests
- [ ] Error recovery tests
- [ ] Timeout handling tests

### Phase 4: Production Ready (Target: 95%)
- [ ] Database integration tests
- [ ] Caching tests
- [ ] WebSocket tests (if added)
- [ ] Background job tests (if added)

---

## Best Practices

### Test Naming
```python
# Backend
def test_{what}_{condition}_{expected}():
    # Example: test_create_user_with_valid_data_succeeds()
    pass

# Frontend
test('should {expected} when {condition}', async () => {
    // Example: test('should display error when login fails')
});
```

### Test Structure (AAA Pattern)
```python
def test_example():
    # Arrange: Set up test data
    user = create_test_user()
    
    # Act: Perform action
    result = authenticate_user(user)
    
    # Assert: Verify result
    assert result.is_authenticated
```

### Mocking
- **Backend**: Use `pytest-mock` for external services
- **Frontend**: Use `vi.mock()` for modules
- **Always mock**: External APIs, databases, time-dependent code

### Test Independence
- Each test must run independently
- No shared state between tests
- Use fixtures for setup/teardown

### Fast Feedback
- Unit tests: < 1 second each
- Integration tests: < 5 seconds each
- Entire suite: < 2 minutes

---

## CI/CD Integration

### Trigger Pipeline
```bash
# GitHub CLI
gh workflow run cp-pipeline.yml \
  --ref main \
  -f run_tests=true \
  -f run_regression_tests=true \
  -f run_load_tests=false \
  -f run_ui_tests=true \
  -f build_images=true
```

### GitHub UI
1. Go to Actions → "CP Build & Test Pipeline"
2. Click "Run workflow"
3. Configure options:
   - ✅ Run tests
   - ✅ Run regression tests
   - ⬜ Run load tests (only on staging)
   - ✅ Run UI tests
   - ✅ Build images

---

## Monitoring & Reporting

### Test Results
- **JUnit XML**: For test runners
- **Coverage XML**: For Codecov
- **HTML Reports**: For human review

### Artifacts Saved
- Test results (XML, JSON)
- Coverage reports (HTML)
- Load test results (CSV, HTML)
- UI test screenshots/videos
- Security scan reports (JSON)

### Notifications
- ✅ PR comments with results
- ✅ GitHub status checks
- ⚠️ Slack notifications (to add)
- ⚠️ Email on failures (to add)

---

## Questions?

See [PIPELINE.md](./PIPELINE.md) for pipeline documentation  
See [PIPELINE_STATUS.md](./PIPELINE_STATUS.md) for current status

**Maintainer**: DevOps Team  
**Last Review**: January 10, 2026
