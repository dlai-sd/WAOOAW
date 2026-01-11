# CP Testing Strategy

**Coverage Target**: 95% (Progressive improvement from current 79%)  
**Last Updated**: January 10, 2026  
**Status**: ✅ All tests passing in CI

---

## Testing Pyramid

```
         /\
        /UI\          10% - UI/E2E Tests (Playwright) ✅
       /----\
      / API  \        15% - API/Integration Tests
     /--------\
    /   Unit   \      75% - Unit Tests (Fast, Isolated)
   /------------\
```

**Current Distribution:**
- Unit Tests: 46 backend + frontend unit tests
- Integration Tests: 3 basic integration tests
- UI/E2E Tests: 10 Playwright scenarios ✅
- Load Tests: Locust configuration ready

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

## 5. UI Tests (E2E) ✅

**Status**: ✅ 10/10 tests passing  
**Duration**: ~1m14s in CI  
**Tools**: Playwright with Chromium  
**Last Updated**: January 10, 2026

**Location**: `src/CP/FrontEnd/e2e/app.spec.ts`

### Current Test Coverage (10 Scenarios)

**1. Landing Page** (3 tests)
- ✅ Page loads correctly with title
- ✅ Theme toggle functionality
- ✅ Sign In button visible

**2. Authentication Flow** (2 tests)
- ✅ Sign in button opens modal
- ✅ Modal closes with Escape key (fixed Jan 10)

**3. Responsive Design** (3 tests)
- ✅ Mobile viewport (375x667)
- ✅ Tablet viewport (768x1024)
- ✅ Desktop viewport (1920x1080)

**4. Accessibility** (1 test)
- ✅ No accessibility violations
- ✅ Keyboard navigation works

**5. Performance** (1 test)
- ✅ Page load < 3 seconds

### Browser Coverage in CI
- ✅ **Chromium** (Primary - used in CI for speed)
- ⚠️ Firefox, WebKit, Mobile browsers (available locally, not in CI to prevent hanging)

### Recent Fixes (January 10, 2026)

**Issue**: Modal close test timing out  
**Root Cause**: Looking for backdrop element with `role="presentation"` that doesn't exist in Fluent UI Dialog  
**Solution**: Use Escape key (standard UX pattern)  
**Commit**: d7acbec

**Issue**: Tests hanging on multiple browser projects  
**Root Cause**: CI only installs Chromium but config defines 7 browser projects  
**Solution**: Added `--project=chromium` flag to CI workflow  
**Commit**: dd4c05f

**Issue**: Port 4173 conflict  
**Root Cause**: Both workflow and Playwright trying to start preview server  
**Solution**: Set `reuseExistingServer: !!process.env.CI` in playwright.config.ts  
**Commit**: ebcd8aa

### Configuration

**`playwright.config.ts`**:
```typescript
export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:4173',
  },
  webServer: {
    command: 'npm run preview -- --port 4173',
    port: 4173,
    reuseExistingServer: !!process.env.CI, // ✅ Fixed
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    // Other browsers available locally
  ],
});
```

**Run Locally**:
```bash
cd src/CP/FrontEnd

# Install browsers (first time)
npx playwright install chromium --with-deps

# Run tests
npm run build
npm run preview -- --port 4173 &
npx playwright test --project=chromium

# Interactive mode
npx playwright test --ui

# View report
npx playwright show-report
```

**Run in CI**:
```yaml
- Workflow: .github/workflows/cp-pipeline.yml
- Job: ui-tests
- Command: npx playwright test --project=chromium --reporter=html
- Artifacts: playwright-report (HTML with screenshots/videos)
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
Actions → CP Build & Test Pipeline → Run workflow

---

## Current Status Summary (January 10, 2026)

### ✅ Completed
- **Unit Tests**: 46 tests (79% coverage)
- **Integration Tests**: 3 basic tests
- **UI/E2E Tests**: 10 Playwright scenarios ✅
- **CI/CD Pipeline**: Fully automated, ~3-4 min duration
- **Security Scans**: Frontend & Backend
- **Docker Builds**: Multi-stage optimized

### 🔄 In Progress
- Increasing coverage from 79% to 95%
- Adding more integration tests
- Performance/load testing setup

### 📋 Next Steps
1. Add database integration tests (when DB implemented)
2. Increase unit test coverage to 95%
3. Add visual regression testing
4. Implement load testing with Locust
5. Add more authenticated portal E2E tests

### Key Metrics
- **Build Success Rate**: 100% (after Jan 10 fixes)
- **Test Duration**: ~1m14s for UI tests, <1m for unit tests
- **Coverage**: Backend 79%, Frontend tracked
- **Pipeline Duration**: ~3-4 minutes total

---

## References

- **Pipeline Config**: `.github/workflows/cp-pipeline.yml`
- **Backend Tests**: `src/CP/BackEnd/tests/`
- **Frontend Tests**: `src/CP/FrontEnd/src/__tests__/`, `src/CP/FrontEnd/src/test/`
- **UI Tests**: `src/CP/FrontEnd/e2e/app.spec.ts`
- **Playwright Config**: `src/CP/FrontEnd/playwright.config.ts`
- **Documentation**: `infrastructure/CI_Pipeline/PIPELINE.md`
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
