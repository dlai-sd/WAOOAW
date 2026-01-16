# API Gateway Implementation - Test Plan

**Version**: 1.0  
**Date**: January 16, 2026  
**Coverage**: MVP-001 (Trial Endpoints), MVP-002 (JWT Auth), MVP-003 (React Router)

---

## Overview

This test plan covers comprehensive testing for the API Gateway implementation across Plant Backend, CP Backend, and CP Frontend. Tests are organized by type (unit, integration, regression, load, UI) and distributed across existing test suites for maintainability.

---

## Test Summary

| Test Type | Plant Backend | CP Backend | CP Frontend | Total |
|-----------|--------------|------------|-------------|-------|
| **Unit** | 3 files, ~50 tests | 3 files, ~40 tests | 2 files, ~20 tests | **~110 tests** |
| **Integration** | 1 file, ~15 tests | 1 file, ~12 tests | - | **~27 tests** |
| **Load/Performance** | 1 file, ~5 tests | 1 file, ~6 tests | - | **~11 tests** |
| **E2E/UI** | - | - | 1 file, ~20 tests | **~20 tests** |
| **Total** | **~70 tests** | **~58 tests** | **~40 tests** | **~168 tests** |

---

## 1. Unit Tests

### Plant Backend (`src/Plant/BackEnd/tests/unit/`)

#### **test_trial_models.py** (MVP-001)
- **Purpose**: Test Trial and TrialDeliverable SQLAlchemy models
- **Coverage**: 
  - Model creation and validation
  - Computed properties (days_remaining, is_expired)
  - Status enum values
  - Optional field handling
  - Timestamp management
- **Marker**: `@pytest.mark.unit`
- **Run**: `pytest tests/unit/test_trial_models.py -v`

#### **test_trial_schemas.py** (MVP-001)
- **Purpose**: Test Pydantic validation schemas
- **Coverage**:
  - TrialCreate validation (email, required fields)
  - TrialUpdate status transitions
  - TrialResponse serialization
  - TrialListResponse pagination
  - Deliverable schemas
- **Marker**: `@pytest.mark.unit`
- **Run**: `pytest tests/unit/test_trial_schemas.py -v`

#### **test_trial_service.py** (MVP-001)
- **Purpose**: Test trial business logic (mocked DB)
- **Coverage**:
  - create_trial() - 7-day duration logic
  - list_trials() - filtering by email, status
  - update_trial_status() - valid/invalid transitions
  - cancel_trial() / convert_trial()
  - check_and_expire_trials() - cron job logic
  - add_deliverable()
- **Marker**: `@pytest.mark.unit`, `@pytest.mark.asyncio`
- **Run**: `pytest tests/unit/test_trial_service.py -v`

### CP Backend (`src/CP/BackEnd/tests/`)

#### **test_auth_models.py** (MVP-002)
- **Purpose**: Test authentication Pydantic schemas
- **Coverage**:
  - UserRegister validation (email, password, full_name)
  - UserLogin validation
  - Token/TokenData schemas
  - Email normalization
- **Marker**: `@pytest.mark.unit`, `@pytest.mark.auth`
- **Run**: `pytest tests/test_auth_models.py -v -m auth`

#### **test_security.py** (MVP-002)
- **Purpose**: Test password hashing utilities (bcrypt)
- **Coverage**:
  - hash_password() - bcrypt format, salt
  - verify_password() - correct/incorrect passwords
  - Special characters and unicode support
  - Case sensitivity
- **Marker**: `@pytest.mark.unit`, `@pytest.mark.auth`
- **Run**: `pytest tests/test_security.py -v -m auth`

#### **test_auth_service.py** (MVP-002)
- **Purpose**: Test auth business logic (mocked DB)
- **Coverage**:
  - register_user() - success, duplicate email
  - authenticate_user() - valid/invalid credentials
  - login_user() - JWT token generation
  - get_user_by_email() / get_user_by_id()
- **Marker**: `@pytest.mark.unit`, `@pytest.mark.auth`, `@pytest.mark.asyncio`
- **Run**: `pytest tests/test_auth_service.py -v -m auth`

### CP Frontend (`src/CP/FrontEnd/src/__tests__/`)

#### **ReactRouter.test.tsx** (MVP-003)
- **Purpose**: Test React Router integration
- **Coverage**:
  - Public routes (/, /auth/callback)
  - Protected route redirects
  - Route parameter handling (/agent/:id)
  - Catch-all redirect
  - Routing history
- **Framework**: Vitest + React Testing Library
- **Run**: `npm run test -- ReactRouter.test.tsx`

#### **Navigation.test.tsx** (MVP-003)
- **Purpose**: Test useNavigate hook usage
- **Coverage**:
  - Programmatic navigation (navigate())
  - Link component rendering
  - Navigation state preservation
  - Back/forward navigation
- **Framework**: Vitest + React Testing Library
- **Run**: `npm run test -- Navigation.test.tsx`

---

## 2. Integration Tests

### Plant Backend (`src/Plant/BackEnd/tests/integration/`)

#### **test_trial_api.py** (MVP-001)
- **Purpose**: End-to-end API testing with database
- **Coverage**:
  - POST /api/v1/trials - Create trial (success, validation errors)
  - GET /api/v1/trials - List with filters (email, status, pagination)
  - GET /api/v1/trials/{id} - Get by ID (success, not found)
  - PATCH /api/v1/trials/{id} - Update status (valid/invalid transitions)
  - DELETE /api/v1/trials/{id} - Cancel trial
  - GET /api/v1/trials/{id}/deliverables - List deliverables
  - Full lifecycle: create → active → converted
- **Marker**: `@pytest.mark.integration`, `@pytest.mark.asyncio`
- **Database**: Uses test PostgreSQL database
- **Run**: `pytest tests/integration/test_trial_api.py -v -m integration`

### CP Backend (`src/CP/BackEnd/tests/`)

#### **test_auth_email_integration.py** (MVP-002)
- **Purpose**: End-to-end auth API testing with database
- **Coverage**:
  - POST /api/v1/auth/register - Register user (success, duplicate, validation)
  - POST /api/v1/auth/login - Login (success, wrong password, not found)
  - GET /api/v1/auth/me - Get current user (with token, without token, invalid token)
  - POST /api/v1/auth/logout - Logout (stateless JWT)
  - Full flow: register → login → get profile → logout
- **Marker**: `@pytest.mark.integration`, `@pytest.mark.auth`, `@pytest.mark.asyncio`
- **Database**: Uses test PostgreSQL database
- **Run**: `pytest tests/test_auth_email_integration.py -v -m integration`

---

## 3. Regression Tests

### Strategy
- **Automated**: All unit and integration tests serve as regression tests
- **Pre-commit**: Run unit tests before commit (`pre-commit` hook)
- **CI/CD**: Run full test suite on PR and merge to main
- **Regression Markers**: Use `@pytest.mark.regression` for critical paths

### Key Regression Test Scenarios

#### Trial API Regression
```bash
# Test that existing trial functionality still works
pytest tests/unit/test_trial*.py tests/integration/test_trial_api.py -v
```

#### Auth API Regression
```bash
# Test that authentication still works after changes
pytest tests/test_auth*.py -v -m auth
```

#### Frontend Regression
```bash
# Test that routing and navigation still work
npm run test -- __tests__
```

### Regression Test Matrix

| Feature | Test File | Critical Scenarios |
|---------|-----------|-------------------|
| Trial Creation | `test_trial_api.py` | Create with valid data, validate 7-day duration |
| Trial Status | `test_trial_service.py` | Valid transitions, reject invalid transitions |
| User Registration | `test_auth_email_integration.py` | Register new user, reject duplicate email |
| User Login | `test_auth_email_integration.py` | Login with valid credentials, reject wrong password |
| JWT Validation | `test_auth_service.py` | Validate token, reject expired token |
| React Router | `ReactRouter.test.tsx` | Protected routes redirect, public routes accessible |
| Navigation | `Navigation.test.tsx` | useNavigate works, no window.location.href usage |

---

## 4. Load/Performance Tests

### Plant Backend (`src/Plant/BackEnd/tests/performance/`)

#### **test_trial_load.py** (MVP-001)
- **Purpose**: Test trial API under load
- **Coverage**:
  - 50 concurrent trial creations (95% success rate, avg < 2s)
  - 100 concurrent trial reads (100% success, avg < 1s)
  - Response time SLA validation (create < 2s, get < 500ms, list < 1s)
  - 20 concurrent status updates
- **Marker**: `@pytest.mark.performance`, `@pytest.mark.slow`
- **Run**: `pytest tests/performance/test_trial_load.py -v -m performance`

### CP Backend (`src/CP/BackEnd/tests/`)

#### **test_auth_load.py** (MVP-002)
- **Purpose**: Test auth API under load
- **Coverage**:
  - 30 concurrent registrations (avg < 3s due to bcrypt)
  - 50 concurrent logins (avg < 2s)
  - Auth API SLA validation (register < 5s, login < 3s, get user < 500ms)
  - 100 concurrent JWT validations (avg < 500ms)
  - Password hashing performance (bcrypt intentionally slow)
- **Marker**: `@pytest.mark.performance`, `@pytest.mark.slow`, `@pytest.mark.auth`
- **Run**: `pytest tests/test_auth_load.py -v -m "performance and auth"`

### Performance SLA Targets

| Endpoint | Metric | Target | Load Test |
|----------|--------|--------|-----------|
| POST /api/v1/trials | Response Time | < 2s | 50 concurrent |
| GET /api/v1/trials/{id} | Response Time | < 500ms | Single request |
| GET /api/v1/trials | Response Time | < 1s | 100 concurrent |
| POST /api/v1/auth/register | Response Time | < 5s | 30 concurrent |
| POST /api/v1/auth/login | Response Time | < 3s | 50 concurrent |
| GET /api/v1/auth/me | Response Time | < 500ms | 100 concurrent |

---

## 5. UI/E2E Tests

### CP Frontend (`src/CP/FrontEnd/e2e/`)

#### **api-gateway.spec.ts** (MVP-001, MVP-002, MVP-003)
- **Purpose**: End-to-end user flows
- **Framework**: Playwright
- **Coverage**:

##### Trial Flow (MVP-001)
- Create trial end-to-end (navigate → select agent → fill form → submit)
- List trials in dashboard
- Filter trials by status
- **Scenarios**: 3 tests

##### Authentication Flow (MVP-002)
- Register new user with email/password
- Login existing user
- Show error for invalid credentials
- Logout user (clear localStorage)
- **Scenarios**: 4 tests

##### Navigation Flow (MVP-003)
- Navigate without page reload (SPA behavior)
- Use browser back/forward buttons
- Protected route redirect when logged out
- Preserve state during navigation
- **Scenarios**: 4 tests

##### Integration Tests
- Full trial workflow (register → discover → start trial → view dashboard → logout)
- **Scenarios**: 1 test

##### Performance Tests
- Load agent discovery within 2 seconds
- Handle rapid navigation (5 rapid clicks)
- **Scenarios**: 2 tests

**Run**: 
```bash
cd src/CP/FrontEnd
npx playwright test e2e/api-gateway.spec.ts
```

**UI Test Environment**:
- **Browser**: Chromium, Firefox, WebKit (cross-browser)
- **Viewport**: Desktop (1280x720), Mobile (375x667)
- **Base URL**: http://localhost:3000
- **Backend**: http://localhost:8000 (Plant), http://localhost:8080 (CP)

---

## Test Execution

### Quick Test Commands

#### Run All Unit Tests
```bash
# Plant Backend
cd src/Plant/BackEnd
pytest tests/unit/ -v

# CP Backend
cd src/CP/BackEnd
pytest tests/ -v -m unit

# CP Frontend
cd src/CP/FrontEnd
npm run test
```

#### Run All Integration Tests
```bash
# Plant Backend
cd src/Plant/BackEnd
pytest tests/integration/ -v -m integration

# CP Backend
cd src/CP/BackEnd
pytest tests/ -v -m integration
```

#### Run All Performance Tests
```bash
# Plant Backend
cd src/Plant/BackEnd
pytest tests/performance/ -v -m performance

# CP Backend
cd src/CP/BackEnd
pytest tests/ -v -m "performance and auth"
```

#### Run All E2E Tests
```bash
cd src/CP/FrontEnd
npx playwright test
```

#### Run Full Test Suite
```bash
# From workspace root
./scripts/run_all_tests.sh
```

### CI/CD Integration

#### GitHub Actions Workflow

```yaml
name: API Gateway Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Plant Backend Unit Tests
        run: cd src/Plant/BackEnd && pytest tests/unit/ -v
      - name: CP Backend Unit Tests
        run: cd src/CP/BackEnd && pytest tests/ -v -m unit
      - name: CP Frontend Unit Tests
        run: cd src/CP/FrontEnd && npm test

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Integration Tests
        run: |
          cd src/Plant/BackEnd && pytest tests/integration/ -v
          cd src/CP/BackEnd && pytest tests/ -v -m integration

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - name: Install Playwright
        run: cd src/CP/FrontEnd && npx playwright install --with-deps
      - name: E2E Tests
        run: cd src/CP/FrontEnd && npx playwright test
```

---

## Coverage Goals

### Target Coverage
- **Unit Tests**: 90% code coverage
- **Integration Tests**: 100% API endpoint coverage
- **E2E Tests**: Critical user paths (100% of MVP features)

### Coverage Reports

#### Python (Backend)
```bash
cd src/Plant/BackEnd
pytest --cov=models --cov=schemas --cov=services --cov=api --cov-report=html

cd src/CP/BackEnd
pytest --cov=models --cov=services --cov=api --cov-report=html
```

#### JavaScript (Frontend)
```bash
cd src/CP/FrontEnd
npm run test:coverage
```

### Coverage Thresholds

| Component | File | Target |
|-----------|------|--------|
| Plant Backend | models/trial.py | 95% |
| Plant Backend | schemas/trial.py | 90% |
| Plant Backend | services/trial_service.py | 90% |
| Plant Backend | api/trials.py | 85% |
| CP Backend | core/security.py | 100% |
| CP Backend | services/auth_service.py | 90% |
| CP Backend | api/auth_email.py | 85% |
| CP Frontend | App.tsx | 80% |
| CP Frontend | pages/*.tsx | 70% |

---

## Test Data Management

### Test Database Setup

#### Plant Backend
```sql
-- Test database: waooaw_plant_test
CREATE DATABASE waooaw_plant_test;

-- Run migrations
cd src/Plant/BackEnd
alembic upgrade head
```

#### CP Backend
```sql
-- Test database: waooaw_cp_test
CREATE DATABASE waooaw_cp_test;

-- Run migrations
cd src/CP/BackEnd
alembic upgrade head
```

### Test Data Fixtures

#### Pytest Fixtures (Backend)
- `async_client`: HTTP client for API testing
- `mock_db_session`: Mocked database session for unit tests
- `sample_agent_id`: Test agent ID for trial creation
- `test_user`: Test user for auth testing

#### Mock Data (Frontend)
- `MockAuthProvider`: Mocked authentication context
- `MockPlantService`: Mocked Plant API responses

---

## Known Issues & Limitations

### Current Limitations
1. **Database**: Integration tests use local dev database (not isolated test containers yet)
2. **OAuth**: E2E tests don't cover Google OAuth flow (requires mocking)
3. **Email**: No email verification tests (not implemented in MVP-002)
4. **Payment**: No payment integration tests (explicitly excluded)
5. **Deliverables**: No file upload tests (storage not implemented)

### Future Enhancements
1. Use `testcontainers-python` for isolated database tests
2. Add `Locust` for load testing (beyond pytest)
3. Add visual regression testing (Percy, Chromatic)
4. Add contract testing (Pact) for API Gateway
5. Add mutation testing (mutmut) for test quality

---

## Test Maintenance

### Adding New Tests
1. **Unit Tests**: Add to `tests/unit/` with descriptive name
2. **Integration Tests**: Add to `tests/integration/`
3. **Markers**: Use appropriate pytest markers (`@pytest.mark.unit`, `@pytest.mark.integration`, etc.)
4. **Documentation**: Update this test plan with new test details

### Test Review Checklist
- [ ] Test name clearly describes what is tested
- [ ] Test is independent (no order dependency)
- [ ] Test has assertions (not just checking for no errors)
- [ ] Test uses appropriate markers
- [ ] Test handles async operations correctly (if applicable)
- [ ] Test cleans up resources (database, files, etc.)
- [ ] Test has docstring explaining purpose

---

## Appendix

### Test File Locations

#### Plant Backend Tests
```
src/Plant/BackEnd/tests/
├── unit/
│   ├── test_trial_models.py (NEW - MVP-001)
│   ├── test_trial_schemas.py (NEW - MVP-001)
│   └── test_trial_service.py (NEW - MVP-001)
├── integration/
│   └── test_trial_api.py (NEW - MVP-001)
└── performance/
    └── test_trial_load.py (NEW - MVP-001)
```

#### CP Backend Tests
```
src/CP/BackEnd/tests/
├── test_auth_models.py (NEW - MVP-002)
├── test_security.py (NEW - MVP-002)
├── test_auth_service.py (NEW - MVP-002)
├── test_auth_email_integration.py (NEW - MVP-002)
└── test_auth_load.py (NEW - MVP-002)
```

#### CP Frontend Tests
```
src/CP/FrontEnd/
├── src/__tests__/
│   ├── ReactRouter.test.tsx (NEW - MVP-003)
│   └── Navigation.test.tsx (NEW - MVP-003)
└── e2e/
    └── api-gateway.spec.ts (NEW - MVP-001, MVP-002, MVP-003)
```

### Dependencies

#### Python Testing Libraries
- `pytest==8.3.4`
- `pytest-asyncio==0.25.2`
- `pytest-cov==6.0.0`
- `httpx==0.28.1` (async HTTP client)
- `pytest-mock==3.14.0`

#### JavaScript Testing Libraries
- `vitest==3.2.4`
- `@testing-library/react==16.3.1`
- `@testing-library/user-event==14.6.1`
- `@playwright/test==1.57.0`

---

**End of Test Plan**
