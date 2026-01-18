# MVP Completion Plan - Post-Phase 3

**Date**: January 16, 2026  
**Branch**: `feature/gateway-implementation`  
**Context**: Phase 1, 2, 3 complete (11 stories). Now completing MVP blockers.  
**Total Effort**: 9 days  
**Payment Integration**: Deferred (not in scope)

---

## Overview

After completing the 11-story implementation plan (Phases 1-3), these critical items remain before MVP launch:

1. **Backend Trial Endpoints** (3 days) - CP cannot persist trial data
2. **JWT Authentication** (3 days) - No auth on CP routes
3. **React Router** (1 day) - Using window.location.href hack
4. **Agent Pricing & Ratings** (2 days) - Hardcoded values

**Total**: 9 days (excluding payment integration)

---

## Task Breakdown

### MVP-001: Backend Trial Endpoints (3 days)

**Priority**: P0 (Blocker - CP trial flow broken)  
**Effort**: 3 days  
**Files**: 8 new/modified files

#### Subtasks (Atomic Commits)

**MVP-001.1: Trial Database Schema & Model** (0.5 days)
- Create `src/Plant/BackEnd/models/trial.py`
- SQLAlchemy model: Trial, TrialDeliverable
- Fields: id, agent_id, customer_name, customer_email, company, phone, start_date, end_date, status, created_at, updated_at
- Alembic migration: `alembic revision --autogenerate -m "Add trial tables"`
- Status enum: active, converted, cancelled, expired

**MVP-001.2: Trial Pydantic Schemas** (0.5 days)
- Create `src/Plant/BackEnd/schemas/trial.py`
- TrialCreate, TrialUpdate, TrialResponse schemas
- Validation: email format, date range (end_date > start_date)
- Compute days_remaining property

**MVP-001.3: Trial Service Layer** (1 day)
- Create `src/Plant/BackEnd/services/trial_service.py`
- Methods: create_trial(), get_trial(), list_trials(), update_trial_status(), cancel_trial()
- Business logic: Set end_date = start_date + 7 days
- Status transitions: active → converted/cancelled/expired

**MVP-001.4: Trial API Endpoints** (1 day)
- Create `src/Plant/BackEnd/api/trials.py`
- POST /api/v1/trials - Create trial
- GET /api/v1/trials - List trials (TODO: filter by customer_email after auth)
- GET /api/v1/trials/{id} - Get trial details
- PATCH /api/v1/trials/{id} - Update trial status
- Register router in main.py

**Dependencies**: None (can start immediately)

**Validation**:
```bash
# Test create trial
curl -X POST http://localhost:8000/api/v1/trials \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-uuid",
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "company": "Example Corp",
    "phone": "+91 98765 43210"
  }'

# Expected response:
{
  "id": "trial-uuid",
  "agent_id": "agent-uuid",
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "company": "Example Corp",
  "start_date": "2026-01-16T10:00:00Z",
  "end_date": "2026-01-23T10:00:00Z",
  "status": "active",
  "days_remaining": 7
}
```

---

### MVP-002: JWT Authentication on CP Routes (3 days)

**Priority**: P0 (Security - anyone can create trials)  
**Effort**: 3 days  
**Files**: 6 new/modified files

#### Subtasks (Atomic Commits)

**MVP-002.1: JWT Utility & Dependencies** (0.5 days)
- Add `python-jose[cryptography]` and `passlib[bcrypt]` to requirements.txt
- Create `src/CP/BackEnd/core/security.py`
- Functions: create_access_token(), verify_token(), get_password_hash(), verify_password()
- JWT settings in config: SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

**MVP-002.2: User Model & Auth Schemas** (0.5 days)
- Create `src/CP/BackEnd/models/user.py`
- SQLAlchemy model: User (id, email, hashed_password, full_name, created_at)
- Create `src/CP/BackEnd/schemas/auth.py`
- Schemas: UserCreate, UserLogin, Token, TokenData

**MVP-002.3: Auth Service & Dependencies** (1 day)
- Create `src/CP/BackEnd/services/auth_service.py`
- Methods: register_user(), authenticate_user(), get_current_user()
- Create `src/CP/BackEnd/dependencies/auth.py`
- Dependency: get_current_user (verifies JWT token)

**MVP-002.4: Auth API Endpoints** (1 day)
- Create `src/CP/BackEnd/api/auth.py`
- POST /api/v1/auth/register - User signup
- POST /api/v1/auth/login - Get JWT token
- GET /api/v1/auth/me - Get current user
- Protect trial routes with `current_user: User = Depends(get_current_user)`

**Dependencies**: MVP-001 (trial endpoints need protection)

**Validation**:
```bash
# Register user
curl -X POST http://localhost:8002/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "secret123", "full_name": "John Doe"}'

# Login
curl -X POST http://localhost:8002/api/v1/auth/login \
  -d "username=john@example.com&password=secret123"

# Expected response:
{"access_token": "eyJhbGc...", "token_type": "bearer"}

# Access protected route
curl http://localhost:8002/api/v1/trials \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### MVP-003: React Router Integration (1 day)

**Priority**: P1 (UX improvement - page reloads on navigation)  
**Effort**: 1 day  
**Files**: 4 modified files

#### Subtasks (Atomic Commits)

**MVP-003.1: Install React Router & Setup** (0.25 days)
- Add `react-router-dom` to CP frontend package.json
- Install: `npm install react-router-dom`
- Update `src/CP/FrontEnd/src/main.tsx` to wrap App with BrowserRouter

**MVP-003.2: Add Routes to App.tsx** (0.5 days)
- Update `src/CP/FrontEnd/src/App.tsx`
- Import Routes, Route from react-router-dom
- Add routes:
  - `/` - Home/Landing page (TODO: create)
  - `/discover` - AgentDiscovery
  - `/agent/:agentId` - AgentDetail
  - `/trials` - TrialDashboard
  - `/login` - Login page (TODO: create after MVP-002)
  - `/register` - Signup page (TODO: create after MVP-002)

**MVP-003.3: Replace window.location.href** (0.25 days)
- Update AgentDiscovery.tsx: `window.location.href = ...` → `navigate(...)`
- Update AgentDetail.tsx: `window.location.href = ...` → `navigate(...)`
- Update BookingModal.tsx: Already uses navigate() (no change)

**Dependencies**: None (can do in parallel with MVP-001/002)

**Validation**:
```typescript
// Test navigation without page reload
// 1. Open DevTools Network tab
// 2. Navigate from /discover to /agent/123
// 3. Verify: No full page reload (no HTML request)
// 4. Back button works (browser history preserved)
```

---

### MVP-004: Agent Pricing & Ratings (2 days)

**Priority**: P1 (Better UX - removes hardcoded values)  
**Effort**: 2 days  
**Files**: 5 modified files

#### Subtasks (Atomic Commits)

**MVP-004.1: Add Price & Rating to Agent Model** (0.5 days)
- Update `src/Plant/BackEnd/models/agent.py`
- Add fields: price_per_month (Integer, default 12000), rating (Float, default 0.0), review_count (Integer, default 0)
- Alembic migration: `alembic revision --autogenerate -m "Add agent pricing and ratings"`

**MVP-004.2: Update Agent Schemas** (0.5 days)
- Update `src/Plant/BackEnd/schemas/agent.py`
- Add price_per_month, rating, review_count to AgentResponse
- Add to AgentCreate (optional, defaults to 12000/0.0/0)

**MVP-004.3: Update CP Plant Types** (0.5 days)
- Update `src/CP/FrontEnd/src/types/plant.types.ts`
- Add to Agent interface: `price_per_month?: number`, `rating?: number`, `review_count?: number`

**MVP-004.4: Update CP Frontend Components** (0.5 days)
- Update AgentCard.tsx: Show `agent.price_per_month` or "Contact for pricing"
- Update AgentCard.tsx: Show `agent.rating` and stars (⭐) or "No reviews yet"
- Update AgentDetail.tsx: Show real price instead of hardcoded ₹12,000
- Update AgentDetail.tsx: Show real rating instead of placeholder 4.8

**Dependencies**: None (can do in parallel)

**Validation**:
```python
# Create agent with custom price
agent = Agent(
    name="Premium Marketing Agent",
    price_per_month=25000,
    rating=4.9,
    review_count=127
)

# Frontend displays:
# - Price: ₹25,000/month
# - Rating: ⭐ 4.9 (127 reviews)
```

---

## Implementation Schedule

### Day 1-3: Backend Trial Endpoints (MVP-001)
- Day 1: MVP-001.1 + MVP-001.2 (models + schemas)
- Day 2: MVP-001.3 (service layer)
- Day 3: MVP-001.4 (API endpoints + testing)

### Day 4-6: JWT Authentication (MVP-002)
- Day 4: MVP-002.1 + MVP-002.2 (JWT utils + user model)
- Day 5: MVP-002.3 (auth service)
- Day 6: MVP-002.4 (auth endpoints + protect trial routes)

### Day 7: React Router (MVP-003)
- Day 7 Morning: MVP-003.1 + MVP-003.2 (install + routes)
- Day 7 Afternoon: MVP-003.3 (replace navigation)

### Day 8-9: Agent Pricing & Ratings (MVP-004)
- Day 8: MVP-004.1 + MVP-004.2 (backend model + schemas)
- Day 9: MVP-004.3 + MVP-004.4 (frontend types + components)

---

## Atomic Commit Strategy

Each subtask = 1 atomic commit (~0.25-1 day of work, ~100-300 lines):

1. **MVP-001.1**: `feat(plant): Add trial database models`
2. **MVP-001.2**: `feat(plant): Add trial Pydantic schemas`
3. **MVP-001.3**: `feat(plant): Add trial service layer`
4. **MVP-001.4**: `feat(plant): Add trial API endpoints`
5. **MVP-002.1**: `feat(cp): Add JWT utility & dependencies`
6. **MVP-002.2**: `feat(cp): Add user model & auth schemas`
7. **MVP-002.3**: `feat(cp): Add auth service & dependencies`
8. **MVP-002.4**: `feat(cp): Add auth endpoints & protect routes`
9. **MVP-003.1**: `feat(cp): Install React Router`
10. **MVP-003.2**: `feat(cp): Add routes to App.tsx`
11. **MVP-003.3**: `refactor(cp): Replace window.location with navigate`
12. **MVP-004.1**: `feat(plant): Add price & rating to agent model`
13. **MVP-004.2**: `feat(plant): Update agent schemas for pricing`
14. **MVP-004.3**: `feat(cp): Update Plant types for pricing`
15. **MVP-004.4**: `feat(cp): Display real pricing & ratings`

**Total**: 15 commits over 9 days

---

## Deferred Items (Post-MVP)

These are NOT in this plan (will do later):

1. **Payment Integration** (5 days) - Razorpay/Stripe
2. **Email Notifications** (3 days) - Trial start/expiry emails
3. **Deliverables Storage** (5 days) - S3/GCS for trial files
4. **Backend Search** (2 days) - Full-text search on agents
5. **Testing** (10 days) - Unit/integration/E2E tests
6. **PP React Migration** (7 days) - Convert PP to React
7. **PP Authentication** (3 days) - JWT on PP routes
8. **Advanced Filters** (2 days) - Job role, price range, etc.

**Total Deferred**: 37 days (~7-8 weeks)

---

## Success Criteria

### MVP Launch Ready When:

✅ **Trial Flow Works End-to-End**:
1. Customer discovers agent (/discover)
2. Views agent details (/agent/:id)
3. Fills trial form (BookingModal)
4. Trial created in database (POST /api/v1/trials)
5. Views trial in dashboard (/trials)
6. Sees countdown (7 days remaining)

✅ **Authentication Works**:
1. User registers (/auth/register)
2. User logs in (/auth/login)
3. JWT token stored in localStorage
4. Protected routes reject unauthenticated requests
5. Trial data filtered by user email

✅ **Navigation Works**:
1. No page reloads on click
2. Browser back/forward works
3. URLs update in address bar
4. Bookmarkable URLs work

✅ **Pricing/Ratings Display**:
1. Agent cards show real prices
2. Agent cards show real ratings
3. Agent detail shows real price
4. Agent detail shows real rating

---

## Risk Mitigation

### Risk 1: Database Migrations Fail
**Mitigation**: Test migrations on dev database first, backup prod before apply

### Risk 2: JWT Secret Compromised
**Mitigation**: Use environment variable, rotate regularly, long random string (64+ chars)

### Risk 3: React Router Breaking Changes
**Mitigation**: Pin react-router-dom version, test all routes after install

### Risk 4: Price/Rating Schema Change Breaks Frontend
**Mitigation**: Make fields optional with defaults, regenerate TypeScript types

---

## Next Steps

1. ✅ Update implementation plan with MVP tasks
2. ⏳ Start MVP-001.1 (Trial database models)
3. ⏳ Commit atomically after each subtask
4. ⏳ Test integration after each day
5. ⏳ Push to feature branch daily
6. ⏳ Create MVP Completion Report after Day 9

---

**Status**: Ready to start MVP-001.1  
**Next Action**: Create trial database models in Plant backend
