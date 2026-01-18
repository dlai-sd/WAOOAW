# Phase 2 Quick Start Guide - Genesis Webhook Implementation

**Date:** January 14, 2026  
**Phase:** Phase 2 (Weeks 4-5) - Genesis Webhook & Certification Authority  
**Duration:** 2 weeks  
**User Stories:** US-0009 through US-0012  

---

## 🎯 Phase 2 Objectives

Implement Genesis Webhook service (Port 9001) - the L0/L1 compliance gate that certifies entities.

### Key Deliverables
1. **Genesis Webhook FastAPI Service** (port 9001)
   - 5 endpoints: /certify/skill, /certify/job, /validate/agent, /precedents/supersede, /certify/batch
   - 42-point Agent certification checklist
   - Pub/Sub integration (certification_results topic)

2. **Constitutional Compliance Engine**
   - L0 checks (5 foundational rules)
   - L1 entity-specific validation
   - Detailed failure reasons (no bypass possible)

3. **Multi-environment CICD**
   - Deployment to Cloud Run (demo, uat, prod)
   - Separate Genesis instances per environment
   - Secrets management (RSA keys via Secret Manager)

---

## 📋 User Stories (Phase 2)

### US-0009: Implement Genesis Webhook FastAPI Service
**Status:** Not Started  
**Priority:** CRITICAL  
**Estimated Effort:** 3 days  

**Description:**
As a System Architect, I want to create Genesis Webhook service (FastAPI on Cloud Run port 9001), so that entities can be certified against L0/L1 principles before production use.

**Acceptance Criteria:**
- [ ] FastAPI scaffold (main.py, routes.py)
- [ ] 5 endpoints implemented (certify/skill, certify/job, validate/agent, precedents/supersede, certify/batch)
- [ ] 42-point checklist logic
- [ ] PostgreSQL integration (store certification results)
- [ ] Redis caching (certification results TTL 24h)
- [ ] Pub/Sub publisher (certification_results topic)
- [ ] Health check endpoint (GET /health)
- [ ] Unit tests (all 5 endpoints + error cases)

**Blocked By:** None (but depends on Phase 0 completion)  
**Blocks:** US-0010, US-0011, US-0012

---

### US-0010: Implement L0 Compliance Checklist
**Status:** Not Started  
**Priority:** CRITICAL  
**Estimated Effort:** 2 days  

**Description:**
As a Product Manager, I want Genesis to validate entities against L0 foundational principles, so that no constitutional breaches reach production.

**Acceptance Criteria:**
- [ ] L0-01: governance_agent_id present
- [ ] L0-02: amendment_history tracked
- [ ] L0-03: append-only enforced
- [ ] L0-04: supersession chain preserved
- [ ] L0-05: compliance gate exportable
- [ ] Each L0 check returns detailed validation result
- [ ] L0 failures block certification (no bypass)
- [ ] Unit tests (all 5 L0 checks)

**Implementation File:** `src/Plant/BackEnd/services/genesis_checklist.py`

---

### US-0011: Implement Precedent Supersession Logic
**Status:** Not Started  
**Priority:** HIGH  
**Estimated Effort:** 2 days  

**Description:**
As a Vision Guardian, I want to supersede old precedent seeds with new ones, so that the constitutional foundation evolves without breaking existing agreements.

**Acceptance Criteria:**
- [ ] POST /precedents/supersede endpoint
- [ ] Validates authority (Vision Guardian only)
- [ ] Creates supersession record (old_seed_id → new_seed_id)
- [ ] Updates hash chain with supersession link
- [ ] Triggers Pub/Sub event (precedent_superseded)
- [ ] Unit tests (supersession flow + authority validation)

**Implementation File:** `src/Plant/BackEnd/services/genesis_supersession.py`

---

### US-0012: Implement Batch Certification API
**Status:** Not Started  
**Priority:** HIGH  
**Estimated Effort:** 1.5 days  

**Description:**
As a System Architect, I want to certify 1..50 entities in a batch, so that onboarding new agents is efficient without overwhelming Genesis.

**Acceptance Criteria:**
- [ ] POST /certify/batch endpoint (max 50 entities)
- [ ] Per-entity L0/L1 validation
- [ ] Partial success handling (some pass, some fail)
- [ ] Returns detailed results per entity
- [ ] Publishes Pub/Sub event per certified entity
- [ ] Unit tests (batch flow + partial failures)

**Implementation File:** `src/Plant/BackEnd/services/genesis_batch.py`

---

## 📁 Directory Structure (Phase 2)

```
src/Plant/BackEnd/
├── services/
│   ├── genesis_checklist.py      ← L0 validation rules
│   ├── genesis_supersession.py   ← Precedent management
│   ├── genesis_batch.py          ← Batch certification
│   └── genesis_webhook.py        ← Main certification orchestration (NEW)
├── api/
│   ├── v1/
│   │   ├── genesis_webhook.py    ← HTTP endpoints for Genesis (NEW)
│   │   └── router.py             ← Mount genesis_webhook routes
├── models/
│   ├── certification.py          ← Certification result model (NEW)
│   └── precedent_seed.py         ← Precedent seed model (NEW)
├── database/
│   └── migrations/
│       └── versions/
│           └── 006_genesis_tables.py  ← New tables: certifications, precedent_seeds (NEW)
└── main.py                       ← Mount genesis_webhook router
```

---

## 🔧 Implementation Plan

### Week 1 (Days 1-3): Core Genesis Service

**Day 1:**
- [ ] Create Genesis service scaffold (`services/genesis_webhook.py`)
- [ ] Implement L0 checklist (`services/genesis_checklist.py`)
- [ ] Add database models for certifications

**Day 2:**
- [ ] Implement HTTP endpoints (`api/v1/genesis_webhook.py`)
- [ ] Add Pub/Sub integration (publish certification events)
- [ ] Implement Redis caching (24h TTL)

**Day 3:**
- [ ] Add unit tests for all L0 checks
- [ ] Error handling (detailed failure reasons)
- [ ] API documentation (OpenAPI/Swagger)

### Week 2 (Days 4-5): Advanced Features

**Day 4:**
- [ ] Implement precedent supersession logic
- [ ] Implement batch certification
- [ ] Add integration tests

**Day 5:**
- [ ] Cloud Run deployment scripts
- [ ] Environment-specific configurations
- [ ] Performance benchmarks

---

## 🗂️ Files to Create

| File | Lines | Purpose |
|------|-------|---------|
| `src/Plant/BackEnd/services/genesis_webhook.py` | 150 | Main certification orchestration |
| `src/Plant/BackEnd/services/genesis_checklist.py` | 120 | L0 validation rules |
| `src/Plant/BackEnd/services/genesis_supersession.py` | 100 | Precedent management |
| `src/Plant/BackEnd/services/genesis_batch.py` | 80 | Batch certification |
| `src/Plant/BackEnd/api/v1/genesis_webhook.py` | 140 | HTTP endpoints |
| `src/Plant/BackEnd/models/certification.py` | 50 | Result schema |
| `src/Plant/BackEnd/models/precedent_seed.py` | 80 | Seed schema |
| `src/Plant/BackEnd/database/migrations/versions/006_genesis_tables.py` | 120 | DB migration |
| `tests/integration/test_genesis_webhook.py` | 200 | Integration tests |
| `tests/unit/test_genesis_checklist.py` | 150 | L0 validation tests |
| **Total** | **1,170** | **10 files** |

---

## 🔑 Key Implementation Details

### L0 Checklist (5 Checks)

```python
# In services/genesis_checklist.py

def check_l0_01_governance_agent_id(entity: BaseEntity) -> bool:
    """L0-01: governance_agent_id must be present"""
    return entity.governance_agent_id is not None

def check_l0_02_amendment_history(entity: BaseEntity) -> bool:
    """L0-02: amendment_history must be tracked"""
    return len(entity.amendment_history) > 0

def check_l0_03_append_only(entity: BaseEntity) -> bool:
    """L0-03: append-only enforcement"""
    # Check database trigger prevents UPDATE/DELETE on audit columns
    return entity.append_only is True

def check_l0_04_supersession_chain(entity: BaseEntity) -> bool:
    """L0-04: supersession chain preserved"""
    # If entity was superseded, validate chain link
    if entity.custom_attributes.get("superseded_by"):
        return validate_supersession_link(entity)
    return True

def check_l0_05_compliance_gate_exportable(entity: BaseEntity) -> bool:
    """L0-05: compliance gate must be exportable"""
    # Must be able to return JSON report
    return can_serialize_to_json(entity)
```

### HTTP Endpoints (5 Routes)

```python
# In api/v1/genesis_webhook.py

@router.post("/certify/skill")
async def certify_skill(skill_id: UUID) -> CertificationResult:
    """Certify individual Skill"""
    # 1. Load Skill from DB
    # 2. Run L0/L1 checks
    # 3. Store certification result
    # 4. Publish Pub/Sub event
    # 5. Return result (200 if pass, 400 if fail)

@router.post("/certify/job")
async def certify_job_role(job_role_id: UUID) -> CertificationResult:
    """Certify individual JobRole + required skills"""

@router.post("/validate/agent")
async def validate_agent(agent_id: UUID) -> CertificationResult:
    """Run 42-point Agent certification checklist"""

@router.post("/precedents/supersede")
async def supersede_precedent(old_seed_id: UUID, new_seed_id: UUID) -> SupersessionResult:
    """Apply precedent supersession (Vision Guardian only)"""

@router.post("/certify/batch")
async def batch_certify(entity_ids: List[UUID]) -> BatchCertificationResult:
    """Certify 1..50 entities with partial success handling"""

@router.get("/health")
async def health_check() -> HealthStatus:
    """Health check: return certification queue depth, cache hit rate"""
```

### Pub/Sub Integration

```python
# In services/genesis_webhook.py

from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(GCP_PROJECT_ID, "certification_results")

# Publish certification event
future = publisher.publish(
    topic_path,
    json.dumps({
        "certification_id": str(result.id),
        "entity_id": str(entity.id),
        "entity_type": entity.entity_type,
        "status": "certified" if result.passed else "rejected",
        "timestamp": datetime.utcnow().isoformat(),
    }).encode("utf-8"),
)
```

---

## 📊 Testing Strategy (Phase 2)

### Unit Tests (8 files, ~800 lines)
- test_genesis_checklist.py: All 5 L0 checks
- test_genesis_supersession.py: Precedent management
- test_genesis_batch.py: Batch certification
- test_certification_result.py: Result schemas

### Integration Tests (3 files, ~300 lines)
- test_genesis_webhook_endpoints.py: All 5 HTTP endpoints
- test_genesis_pubsub.py: Pub/Sub integration
- test_genesis_caching.py: Redis caching

### Coverage Target: 90%+ (critical path 95%+)

---

## 🚀 Deployment (Phase 2 Week 5)

### Local Testing
```bash
# 1. Start services
docker-compose up -d postgres redis pubsub-emulator

# 2. Run migrations + seed
cd src/Plant/BackEnd
./scripts/migrate-db.sh local
./scripts/seed-db.sh local

# 3. Start Genesis service
python main.py  # Starts port 9001

# 4. Test endpoint
curl -X POST http://localhost:9001/certify/skill \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "uuid-here"}'
```

### Demo Deployment (GitHub Actions)
```bash
# 1. Create Cloud Run service
gcloud run deploy plant-genesis-demo \
  --image gcr.io/PROJECT/plant-genesis:demo \
  --port 9001 \
  --memory 512MB \
  --cpu 1

# 2. GitHub Actions auto-deploys on push to main
# 3. Verify: curl https://plant-genesis-demo.run.app/health
```

---

## 📝 Documentation Updates (Phase 2)

Update these docs:
- [x] PLANT_BLUEPRINT.yaml - Section 2 (Genesis Webhook)
- [x] PLANT_USER_STORIES.yaml - US-0009 through US-0012
- [ ] README.md (Phase 2 development guide)
- [ ] API_DOCUMENTATION.md (Genesis endpoints reference)

---

## ⚠️ Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Certification timeout (>10s) | Implement async certification, timeout handler |
| Database connection issues | Add retry logic, circuit breaker |
| Pub/Sub message loss | Use dead-letter queue, idempotent processing |
| Performance regression | Run benchmarks, compare with Phase 0 baseline |
| L0 check failure in prod | Unit test all checks, integration test workflow |

---

## 📞 Blockers/Dependencies

**No blockers for Phase 2!**

Phase 0 completion provides:
- ✅ PostgreSQL schema (base_entity + migrations)
- ✅ RLS policies (security layer)
- ✅ BaseEntity model (constitutional alignment)
- ✅ CICD pipeline (GitHub Actions)

Ready to start Phase 2 immediately.

---

## 🎓 Key Learning Points

**Genesis Concept:**
- Genesis is NOT just a validator - it's the **immutable certification authority**
- L0 checks cannot be bypassed (this is the key security property)
- Each certification is cryptographically signed + stored in audit trail
- Pub/Sub events allow downstream services (PP Portal, etc.) to react to certifications

**Implementation Mindset:**
- Think "agent-maintained platform" not "developer-maintained software"
- Every failure should have a detailed remediation hint
- No silent failures (always log + alert)
- Cost awareness (Pub/Sub messages, database queries count)

---

## 📚 References

**Specifications:**
- PLANT_BLUEPRINT.yaml Section 2 (Genesis Webhook component)
- PLANT_USER_STORIES.yaml (US-0009 through US-0012)

**Phase 0 Outputs:**
- PLANT_BACKEND_SESSION_SUMMARY.md
- PLANT_ENVIRONMENT_CICD_SUMMARY.md

**Code Examples:**
- Phase 0 services (skill_service.py, agent_service.py for patterns)
- Phase 0 validators (constitutional_validator.py for L0 logic)

---

## ✅ Ready to Start Phase 2?

**YES** - All Phase 0 dependencies complete ✅  
**Dependencies Met:**
- ✅ BaseEntity with 7 sections
- ✅ PostgreSQL schema + migrations
- ✅ CICD pipeline (GitHub Actions)
- ✅ 4-environment strategy (local, demo, uat, prod)

**Next Action:** Start implementing US-0009 (Genesis Webhook FastAPI Service)

---

**Prepared:** January 14, 2026  
**Phase:** 2 (Weeks 4-5)  
**Status:** Ready for Implementation  

🚀 Let's build Genesis! 🚀
