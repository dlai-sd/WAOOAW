# Plant-CP-PP Architecture Analysis & Integration Blueprint

**Date**: January 15, 2026  
**Status**: Architecture Design (Post-SSL-Incident Recovery)  
**Purpose**: Define how Plant (data layer) bridges with CP (customer UI) and PP (admin portal)

---

## Executive Summary

**Current State:**
- **CP** (Customer Portal): Auth-only (~24 Python files), frontend-focused, NO backend database
- **PP** (Platform Portal): Admin skeleton with database setup, empty API endpoints (~2K files mostly deps)
- **Plant**: Complete domain layer (3 routers, 6 entities, full services, ~4.3K files)

**Emerging Architecture:**
```
Plant = Data/Domain Layer (source of truth)
  ↓
├─ CP (Customer Marketplace UI) ← Read-only APIs
│  └─ Browse agents, skills, job roles
│
└─ PP (Admin Portal) ← Full CRUD APIs
   └─ Manage agents, certify skills, audit operations
```

---

## Detailed Component Analysis

### 1. CP (Customer Portal) - Frontend-Focused, Auth-only

**Current Structure:**
```
src/CP/BackEnd/
├── api/
│   └── auth/
│       ├── routes.py (7 endpoints: login, callback, verify, refresh, logout, me, health)
│       ├── google_oauth.py
│       ├── user_store.py
│       └── dependencies.py
├── models/
│   └── user.py (User, Token models only)
├── core/
│   ├── config.py
│   └── jwt_handler.py
├── main.py
└── tests/
```

**API Endpoints:**
- `GET /auth/google/login` - OAuth flow initiation
- `GET /auth/google/callback` - OAuth callback handler
- `POST /auth/google/verify` - Verify ID token
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - Logout
- `GET /auth/me` - Current user info
- `GET /auth/health` - Health check

**Key Characteristics:**
- ✅ Google OAuth integrated
- ✅ JWT token management
- ✅ Frontend-focused (no domain logic)
- ❌ Zero domain models or services
- ❌ No database backend beyond user session

**What CP Needs from Plant:**
- **Read-only endpoints** for marketplace discovery
- Agent listings, skills, job roles, specializations
- Agent ratings, availability, recent activity
- Search & filter capabilities

---

### 2. PP (Platform Portal) - Admin Skeleton with DB Ready

**Current Structure:**
```
src/PP/BackEnd/
├── api/
│   └── auth.py (1 endpoint: /auth/me)
├── models/ (EMPTY - no domain models)
├── core/
│   ├── config.py
│   ├── database.py (SQLAlchemy setup)
│   └── exceptions.py
├── main.py
└── requirements.txt (includes SQLAlchemy, PostgreSQL, Redis, Alembic)
```

**API Endpoints:**
- `GET /auth/me` - Current user info

**Key Characteristics:**
- ✅ Database infrastructure ready (SQLAlchemy, PostgreSQL, Redis, Alembic)
- ✅ Dependencies installed for full CRUD apps
- ✅ Environment isolated from CP/Plant
- ❌ Zero API endpoints beyond auth placeholder
- ❌ No domain services or models

**What PP Needs from Plant:**
- **Write-enabled endpoints** for admin operations
- Create/edit skills, job roles, agent profiles
- Certify agents, manage specializations
- Audit and tampering detection endpoints
- Full read access to all domain data

---

### 3. Plant - Complete Domain Layer

**Current Structure:**
```
src/Plant/BackEnd/
├── api/
│   └── v1/
│       ├── genesis.py (7 endpoints: skill CRUD, role CRUD, certify)
│       ├── agents.py (4 endpoints: agent CRUD, assign team)
│       ├── audit.py (3 endpoints: run audit, check tampering, export)
│       └── router.py (consolidates all routers)
├── models/
│   ├── entities.py (6 models: BaseEntity, Skill, JobRole, Team, Agent, Industry)
│   ├── schemas.py (Pydantic request/response models)
│   ├── database.py (ORM definitions)
├── services/
│   ├── skill_service.py
│   ├── job_role_service.py
│   ├── agent_service.py
│   ├── audit_service.py
│   └── team_service.py
├── security/
│   ├── hash_chain.py
│   └── cryptography.py
├── core/
│   ├── database.py (PostgreSQL + VPC)
│   ├── exceptions.py
│   └── config.py
├── main.py
├── create_tables.py (database initialization)
└── requirements.txt (SQLAlchemy, PostgreSQL, Redis, FastAPI)
```

**API Endpoints (13 total):**

**Genesis Router:**
- `POST /api/v1/genesis/skills` - Create skill
- `GET /api/v1/genesis/skills` - List skills
- `GET /api/v1/genesis/skills/{skill_id}` - Get skill
- `POST /api/v1/genesis/skills/{skill_id}/certify` - Certify skill
- `POST /api/v1/genesis/job-roles` - Create job role
- `GET /api/v1/genesis/job-roles` - List job roles
- `GET /api/v1/genesis/job-roles/{role_id}` - Get job role

**Agents Router:**
- `POST /api/v1/agents` - Create agent
- `GET /api/v1/agents` - List agents
- `GET /api/v1/agents/{agent_id}` - Get agent
- `POST /api/v1/agents/{agent_id}/assign-team` - Assign team

**Audit Router:**
- `POST /api/v1/audit/run` - Run audit
- `GET /api/v1/audit/tampering/{entity_id}` - Check tampering
- `GET /api/v1/audit/export` - Export audit log

**Key Characteristics:**
- ✅ Complete domain services with business logic
- ✅ Security (hash chain, cryptography)
- ✅ Audit & tampering detection
- ✅ PostgreSQL with VPC connector
- ✅ Pydantic schema validation
- ✅ Full ORM models with relationships
- ✅ Exception handling with custom errors

---

## Integration Architecture

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│           WAOOAW Load Balancer + DNS                │
│                                                      │
│  cp.demo.waooaw.com  pp.demo.waooaw.com  plant...   │
└──────────────────┬──────────────────┬────────────────┘
                   │                  │
         ┌─────────▼──────────┐  ┌───▼──────────────┐
         │  CP (Frontend)     │  │  PP (Admin)      │
         │                    │  │                  │
         │ Auth only:         │  │ Auth + Admin API │
         │ - Login/Logout     │  │ - User mgmt      │
         │ - Token refresh    │  │ - Agent mgmt     │
         │ - User profile     │  │ - Audit          │
         └────────────┬───────┘  └───────┬──────────┘
                      │                  │
                      └──────┬───────────┘
                             │
                    ┌────────▼───────────┐
                    │  Plant (Domain)    │
                    │                    │
                    │ Complete API:      │
                    │ - Skills CRUD      │
                    │ - Agents CRUD      │
                    │ - Job Roles CRUD   │
                    │ - Audit + Security │
                    │ - Certification    │
                    │                    │
                    │ PostgreSQL (VPC)   │
                    └────────────────────┘
```

### Data Ownership & Access Patterns

| Domain | Owner | CP Access | PP Access | Storage |
|--------|-------|-----------|-----------|---------|
| **User (Auth)** | CP + PP | Read (self) | Read + Write | CP DB |
| **Skill** | Plant | Read-only | Read + Write | Plant DB |
| **Job Role** | Plant | Read-only | Read + Write | Plant DB |
| **Agent** | Plant | Read + Rating | Read + Write | Plant DB |
| **Team** | Plant | None | Read + Write | Plant DB |
| **Industry** | Plant | Read-only | Read + Write | Plant DB |
| **Audit Log** | Plant | None | Read-only | Plant DB |

---

## Implementation Roadmap

### Phase 1: CP Integration (Read-only Marketplace)

**Add to CP:**
1. New router: `api/marketplace/router.py`
2. HTTP client for Plant API calls
3. New endpoints:
   - `GET /api/marketplace/agents` - List agents
   - `GET /api/marketplace/agents/{id}` - Agent details
   - `GET /api/marketplace/skills` - All available skills
   - `GET /api/marketplace/job-roles` - All job roles
   - `GET /api/marketplace/search?q=&industry=&rating=` - Search agents
4. Cache layer (Redis) for marketplace data (low frequency reads)
5. Error handling for Plant API failures

**Dependencies to add to CP:**
```
httpx==0.26.0  # For async HTTP calls to Plant
redis==5.0.1   # For caching
```

**No database changes needed for CP**

---

### Phase 2: PP Integration (Admin CRUD)

**Add to PP:**
1. Copy Plant's models/services to PP:
   - `models/entities.py` (Skill, Agent, JobRole, etc.)
   - `services/skill_service.py`, `agent_service.py`, etc.
   - `security/hash_chain.py` (for audit validation)
2. New routers mirroring Plant:
   - `api/admin/skills.py` (POST, PUT, DELETE in addition to GET)
   - `api/admin/agents.py` (manage agent assignments, policies)
   - `api/admin/audit.py` (view audit logs, run compliance checks)
3. Database initialization:
   - Run `create_tables.py` equivalent for PP schema
   - Alembic migrations for future schema changes
4. Admin-specific logic:
   - RBAC checks (admin-only endpoints)
   - Admin audit trail
   - Bulk operations (CSV import/export)

**Dependencies already in PP:**
```
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1
redis==5.0.1
```

**New dependencies for PP:**
```
# Auth enforcement
python-jose[cryptography]==3.3.0  # Already in requirements
passlib[bcrypt]==1.7.4             # Already in requirements

# CSV operations (optional for bulk management)
pandas==2.1.3
```

---

### Phase 3: Plant as Shared Service

**Ensure Plant remains clean:**
1. All domain logic stays in Plant services
2. Plant APIs are the source of truth
3. Plant database is owned by Plant only
4. CP/PP don't modify Plant data directly
5. Plant manages all consistency & validation

**Plant API Requirements:**
- ✅ Already implemented (13 endpoints ready)
- Ensure error responses are consistent (HTTP status codes, error messages)
- Add request validation middleware
- Implement rate limiting for admin endpoints (PP)
- Add audit logging for all mutations

---

## Deployment Sequence

1. **Verify All 3 Services Running** (already done):
   - cp.demo.waooaw.com → 200 ✅
   - pp.demo.waooaw.com → 200 ✅
   - plant.demo.waooaw.com → 200 ✅

2. **Phase 1: CP Marketplace** (1-2 weeks):
   - Add read-only Plant API client
   - Deploy new CP endpoints
   - Test marketplace browsing
   - Deploy to demo, then uat, then prod

3. **Phase 2: PP Admin Portal** (2-3 weeks):
   - Migrate Plant models/services to PP
   - Build admin CRUD endpoints
   - Add RBAC and audit logging
   - Test with admin workflows
   - Deploy to demo, then uat, then prod

4. **Phase 3: Production Hardening** (ongoing):
   - Error handling & resilience
   - Performance optimization
   - Security review (auth, RBAC, audit)
   - Monitoring & alerting

---

## Key Decisions & Rationale

### Why Plant as Data Layer?

- ✅ **Domain complexity**: Skills, agents, roles, teams, audit—all belong in one place
- ✅ **Single source of truth**: Both CP and PP read from same data
- ✅ **Consistency**: Business rules (skill certification, agent policy) enforced once
- ✅ **Auditability**: All changes logged in Plant's audit table
- ✅ **Future-proof**: Easy to add more frontends (mobile, web3, etc.)

### Why CP Stays Auth-only?

- ✅ **Separation of concerns**: Frontend UI logic separate from domain logic
- ✅ **Customer-facing**: No admin features to expose
- ✅ **Performance**: Lightweight, fast—no domain processing
- ✅ **Security**: Minimal surface area for customer-facing APIs

### Why PP Gets Full Access?

- ✅ **Admin needs**: PP staff manage agents, skills, policies
- ✅ **Audit trail**: Admin changes must be logged and audited
- ✅ **RBAC**: Different admin roles have different permissions
- ✅ **Bulk operations**: Need CSV import/export for large-scale updates

---

## API Contract Examples

### CP → Plant (Read-only)

```bash
# List all agents (public marketplace)
curl https://plant.demo.waooaw.com/api/v1/agents

# Get agent details
curl https://plant.demo.waooaw.com/api/v1/agents/{agent_id}

# List skills for agent profile
curl https://plant.demo.waooaw.com/api/v1/genesis/skills?filter=active
```

### PP → Plant (Full CRUD)

```bash
# Create new agent (admin only)
curl -X POST https://plant.demo.waooaw.com/api/v1/agents \
  -H "Authorization: Bearer {admin_token}" \
  -d '{"name":"...", "specialization":"..."}'

# Certify skill (admin only)
curl -X POST https://plant.demo.waooaw.com/api/v1/genesis/skills/{skill_id}/certify \
  -H "Authorization: Bearer {admin_token}"

# Run audit compliance check
curl -X POST https://plant.demo.waooaw.com/api/v1/audit/run \
  -H "Authorization: Bearer {admin_token}"
```

---

## Testing Strategy

### CP Testing:
- Mock Plant API responses
- Test error handling when Plant is unavailable
- Cache invalidation when data stale
- Load test marketplace endpoints

### PP Testing:
- Test RBAC (admin vs non-admin)
- Test data consistency (can't create duplicate agents)
- Test audit trail (all changes logged)
- Test Plant API integration with real data

### Integration Testing:
- CP can browse agents created by PP
- PP audit logs Plant mutations
- CP sees latest data from Plant (cache miss handling)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Plant API downtime → CP/PP fail | Implement circuit breaker, cache fallback |
| CP/PP send invalid data | Validate at Plant API layer (single validation point) |
| Admin changes in PP not logged | Audit trail in Plant required for all mutations |
| Race conditions (CP reads while PP writes) | PostgreSQL ACID transactions, proper isolation |
| Schema changes to Plant break CP/PP | Version Plant API (v1, v2), support multiple versions |

---

## Success Criteria

- ✅ CP can display agent marketplace (read Plant data)
- ✅ PP can manage agents and skills (write to Plant)
- ✅ All changes logged in Plant audit table
- ✅ Responses < 500ms (p95) even under load
- ✅ Zero data consistency issues (ACID compliance)
- ✅ 100% API uptime SLA (Plant as critical service)

---

## Next Steps

1. **Code Review**: Review Plant API implementation (13 endpoints)
2. **CP Development**: Add marketplace browsing endpoints
3. **PP Development**: Migrate models/services from Plant, build admin UI
4. **Integration Testing**: Verify CP/PP can call Plant APIs
5. **Deployment**: Roll out to demo → uat → prod
