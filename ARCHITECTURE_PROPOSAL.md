# WAOOAW Microservices Architecture Proposal

**Version**: 2.0 (Clean Slate)  
**Date**: 2026-01-07  
**Status**: Proposal for Session 3 Implementation

---

## 🎯 Executive Summary

Building microservices-first architecture with:
- **6 core microservices** (Agent Creation, Execution, Governance, Industry Knowledge, Learning, Admin Gateway)
- **Mobile-first governance** (Flutter app for Platform Governor)
- **GitHub Projects integration** (issues, milestones, automation)
- **Event-driven patterns** (Cloud Pub/Sub with causation tracking)
- **Cost-optimized** ($120-150/month target)

---

## 📁 Repository Structure (Monorepo)

```
WAOOAW/
├── README.md                          # NEW: Microservices overview, quick start
├── CONTRIBUTING.md                    # NEW: Contribution guidelines
├── CHANGELOG.md                       # NEW: Version history
│
├── services/                          # 🎯 6 Microservices
│   ├── agent-creation/                # Port 8001
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── requirements.txt
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                # FastAPI app
│   │   │   ├── api/                   # REST endpoints
│   │   │   │   ├── v1/
│   │   │   │   │   ├── agents.py      # POST /v1/agents (create)
│   │   │   │   │   ├── workflows.py   # GET /v1/workflows/{id}
│   │   │   ├── workflows/             # Temporal workflows
│   │   │   │   ├── agent_creation.py  # 7-stage pipeline
│   │   │   │   ├── activities/
│   │   │   │   │   ├── genesis_cert.py
│   │   │   │   │   ├── architect_review.py
│   │   │   │   │   ├── ethics_review.py
│   │   │   │   │   ├── governor_approval.py
│   │   │   ├── models/                # Pydantic models
│   │   │   ├── services/              # Business logic
│   │   │   ├── repositories/          # Data access
│   │   │   ├── config.py              # Settings
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   ├── integration/
│   │   │   ├── e2e/
│   │   ├── openapi.yaml               # API spec
│   │   ├── README.md
│   │
│   ├── agent-execution/               # Port 8002
│   │   ├── Dockerfile
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── api/
│   │   │   │   ├── v1/
│   │   │   │   │   ├── jobs.py        # POST /v1/jobs (execute)
│   │   │   │   │   ├── skills.py      # GET /v1/skills
│   │   │   ├── execution/             # Skill execution engine
│   │   │   │   ├── skill_runner.py
│   │   │   │   ├── think_act_observe.py
│   │   │   ├── ml/                    # ML inference
│   │   │   │   ├── models.py          # DistilBERT, BART, MiniLM
│   │   │   │   ├── fallbacks.py
│   │   │   ├── cache/                 # Agent caches
│   │   ├── tests/
│   │   ├── openapi.yaml
│   │   ├── README.md
│   │
│   ├── governance/                    # Port 8003
│   │   ├── Dockerfile
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── api/
│   │   │   │   ├── v1/
│   │   │   │   │   ├── approvals.py   # POST /v1/approvals
│   │   │   │   │   ├── seeds.py       # GET /v1/precedent-seeds
│   │   │   │   │   ├── vetoes.py      # POST /v1/vetoes
│   │   │   ├── rules/                 # Business rules engine
│   │   │   │   ├── query_routing.py
│   │   │   │   ├── budget_thresholds.py
│   │   │   │   ├── seed_matching.py
│   │   │   ├── mobile_api/            # Mobile-specific endpoints
│   │   │   │   ├── governor_dashboard.py
│   │   │   │   ├── notifications.py
│   │   ├── tests/
│   │   ├── openapi.yaml
│   │   ├── README.md
│   │
│   ├── industry-knowledge/            # Port 8004
│   │   ├── Dockerfile
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── api/
│   │   │   │   ├── v1/
│   │   │   │   │   ├── industries.py  # GET /v1/industries
│   │   │   │   │   ├── embeddings.py  # POST /v1/embeddings
│   │   │   ├── vector/                # Vector DB queries
│   │   │   │   ├── constitutional_db.py
│   │   │   │   ├── industry_db.py
│   │   │   │   ├── query_router.py
│   │   │   ├── ml/
│   │   │   │   ├── embeddings.py      # MiniLM embeddings
│   │   ├── tests/
│   │   ├── openapi.yaml
│   │   ├── README.md
│   │
│   ├── learning/                      # Port 8005
│   │   ├── Dockerfile
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── api/
│   │   │   │   ├── v1/
│   │   │   │   │   ├── seeds.py       # POST /v1/seeds (generate)
│   │   │   │   │   ├── patterns.py    # GET /v1/patterns
│   │   │   ├── learning/
│   │   │   │   ├── seed_generator.py
│   │   │   │   ├── pattern_detector.py
│   │   │   ├── ml/
│   │   │   │   ├── clustering.py      # Pattern detection
│   │   ├── tests/
│   │   ├── openapi.yaml
│   │   ├── README.md
│   │
│   └── admin-gateway/                 # Port 8006
│       ├── Dockerfile
│       ├── src/
│       │   ├── main.py
│       │   ├── api/
│       │   │   ├── v1/
│       │   │   │   ├── health.py      # GET /v1/health
│       │   │   │   ├── metrics.py     # GET /v1/metrics
│       │   │   │   ├── admin.py       # Admin operations
│       │   ├── gateway/
│       │   │   ├── router.py          # Route to services
│       │   │   ├── auth.py            # JWT validation
│       │   │   ├── rate_limiter.py
│       ├── tests/
│       ├── openapi.yaml
│       ├── README.md
│
├── libs/                              # 🔧 Shared Libraries
│   ├── common/                        # Common utilities
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   ├── waooaw_common/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── logging.py         # Structured logging
│   │   │   │   ├── metrics.py         # Prometheus metrics
│   │   │   │   ├── tracing.py         # OpenTelemetry
│   │   │   │   ├── config.py          # Config management
│   │   │   │   ├── auth.py            # JWT utilities
│   │   ├── tests/
│   │
│   ├── events/                        # Event schemas & pub/sub
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   ├── waooaw_events/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── publisher.py       # Pub/Sub publisher
│   │   │   │   ├── subscriber.py      # Pub/Sub subscriber
│   │   │   │   ├── schemas/
│   │   │   │   │   ├── agent_state_changed.py
│   │   │   │   │   ├── seed_approved.py
│   │   │   │   │   ├── governor_vetoed.py
│   │   │   │   ├── causation.py       # Causation tracking
│   │   ├── tests/
│   │
│   ├── ml/                            # ML model wrappers
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   ├── waooaw_ml/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── distilbert.py      # 66MB NER
│   │   │   │   ├── bart.py            # 140MB summarization
│   │   │   │   ├── minilm.py          # 22MB embeddings
│   │   │   │   ├── phi3.py            # 1GB LLM (4-bit)
│   │   │   │   ├── prophet.py         # 10MB forecasting
│   │   │   │   ├── fallbacks.py       # Fallback strategies
│   │   │   │   ├── cache.py           # Model caching
│   │   ├── models/                    # Pre-trained model files
│   │   ├── tests/
│   │
│   └── constitutional/                # Constitutional queries
│       ├── pyproject.toml
│       ├── src/
│       │   ├── waooaw_constitutional/
│       │   │   ├── __init__.py
│       │   │   ├── loader.py          # Load main/Foundation/ YAMLs
│       │   │   ├── validator.py       # Validate against constitution
│       │   │   ├── embeddings.py      # Constitutional embeddings
│       ├── tests/
│
├── mobile/                            # 📱 Mobile Apps
│   ├── governor-app/                  # Flutter app (Platform Governor)
│   │   ├── android/
│   │   ├── ios/
│   │   ├── lib/
│   │   │   ├── main.dart
│   │   │   ├── screens/
│   │   │   │   ├── dashboard.dart     # Governor dashboard
│   │   │   │   ├── approvals.dart     # Pending approvals
│   │   │   │   ├── veto.dart          # Veto interface
│   │   │   │   ├── precedents.dart    # Precedent seeds
│   │   │   ├── services/
│   │   │   │   ├── api_client.dart    # HTTP client
│   │   │   │   ├── auth_service.dart  # OAuth
│   │   │   │   ├── notifications.dart # Push notifications
│   │   │   ├── models/
│   │   │   │   ├── approval_request.dart
│   │   │   │   ├── agent.dart
│   │   │   │   ├── precedent_seed.dart
│   │   │   ├── widgets/
│   │   ├── pubspec.yaml
│   │   ├── README.md
│   │
│   └── README.md                      # Mobile development guide
│
├── infrastructure/                    # 🏗️ Infrastructure as Code
│   ├── terraform/
│   │   ├── main.tf                    # Root module
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── modules/
│   │   │   ├── services/              # Cloud Run services
│   │   │   ├── databases/             # Cloud SQL, Redis
│   │   │   ├── pubsub/                # Topics & subscriptions
│   │   │   ├── vector-db/             # Pinecone/Weaviate
│   │   │   ├── temporal/              # Temporal deployment
│   │   │   ├── networking/            # VPC, load balancers
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   ├── prod/
│   │
│   ├── docker/
│   │   ├── docker-compose.yml         # Local development
│   │   ├── docker-compose.test.yml    # Testing
│   │
│   ├── kubernetes/                    # K8s manifests (optional)
│   │   ├── base/
│   │   ├── overlays/
│   │
│   └── monitoring/
│       ├── prometheus/
│       ├── grafana/
│       ├── alertmanager/
│
├── docs/                              # 📚 Documentation
│   ├── README.md                      # Docs index
│   ├── architecture/
│   │   ├── adr/                       # Architecture Decision Records
│   │   │   ├── 001-microservices.md
│   │   │   ├── 002-event-driven.md
│   │   │   ├── 003-temporal.md
│   │   ├── c4/                        # C4 diagrams
│   │   │   ├── context.md
│   │   │   ├── container.md
│   │   │   ├── component.md
│   │   ├── sequence/                  # Sequence diagrams
│   │   │   ├── agent-creation.md
│   │   │   ├── governor-approval.md
│   │
│   ├── api/                           # API documentation
│   │   ├── README.md                  # API overview
│   │   ├── agent-creation.md
│   │   ├── agent-execution.md
│   │   ├── governance.md
│   │   ├── industry-knowledge.md
│   │   ├── learning.md
│   │   ├── admin-gateway.md
│   │
│   ├── runbooks/                      # Operational guides
│   │   ├── deployment.md
│   │   ├── incident-response.md
│   │   ├── rollback.md
│   │   ├── scaling.md
│   │
│   ├── development/                   # Developer guides
│   │   ├── local-setup.md
│   │   ├── testing.md
│   │   ├── debugging.md
│   │   ├── contributing.md
│   │
│   └── mobile/                        # Mobile app docs
│       ├── governor-app-setup.md
│       ├── api-integration.md
│       ├── push-notifications.md
│
├── .github/                           # 🤖 GitHub Automation
│   ├── workflows/
│   │   ├── ci-services.yml            # Test & build services
│   │   ├── ci-mobile.yml              # Test mobile apps
│   │   ├── deploy-dev.yml             # Deploy to dev
│   │   ├── deploy-staging.yml         # Deploy to staging
│   │   ├── deploy-prod.yml            # Deploy to production
│   │   ├── compliance-audit.yml       # Run audit_tech_stack.py
│   │   ├── security-scan.yml          # Trivy, Snyk
│   │   ├── performance-test.yml       # Load tests
│   │
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug.yml
│   │   ├── feature.yml
│   │   ├── agent-violation.yml
│   │   ├── architectural-deviation.yml
│   │
│   ├── PULL_REQUEST_TEMPLATE.md
│   │
│   └── project-config.yml             # GitHub Projects config
│
├── main/                              # 📜 Constitutional Design (PRESERVED)
│   ├── Foundation.md
│   ├── run_log.md
│   ├── Foundation/
│   │   ├── contracts/
│   │   │   └── data_contracts.yml
│   │   ├── template/
│   │   │   ├── foundation_constitution_engine.yaml
│   │   │   ├── governance_protocols.yaml
│   │   │   └── ... (40 more YAMLs)
│   │   └── ... (charters, amendments)
│
├── scripts/                           # 🔧 Utility Scripts
│   ├── setup-local.sh                 # Local environment setup
│   ├── generate-service.sh            # Scaffold new service
│   ├── run-tests.sh                   # Run all tests
│   ├── build-all.sh                   # Build all services
│   ├── db-migrate.sh                  # Database migrations
│   ├── seed-data.sh                   # Seed test data
│
├── archive/                           # 🗄️ Old Implementation (PRESERVED)
│   ├── backend/
│   ├── waooaw/
│   ├── tests/
│   ├── ... (all old code)
│
├── .devcontainer/
│   ├── devcontainer.json
│   └── Dockerfile
│
├── .env.example                       # Environment template
├── .gitignore
├── docker-compose.yml                 # Local dev stack
├── Makefile                           # Common tasks
├── pyproject.toml                     # Root Python config
└── package.json                       # Root JS config (mobile)
```

---

## 🎯 GitHub Project Management Integration

### Project Structure

**GitHub Project**: WAOOAW Microservices (Table view)

**Status Columns**:
- 📋 Backlog
- 🔍 Refinement
- ✅ Ready
- 🚧 In Progress
- 👀 Review
- ✔️ Done

**Custom Fields**:
- **Service** (select): Agent Creation, Agent Execution, Governance, Industry Knowledge, Learning, Admin Gateway, Mobile, Infrastructure, Shared
- **Priority** (select): P0 Critical, P1 High, P2 Medium, P3 Low
- **Effort** (number): Story points (1, 2, 3, 5, 8, 13)
- **Component** (select): API, Workflow, ML, Mobile, Infra, Docs
- **Sprint** (iteration): 2-week sprints
- **Constitutional** (checkbox): Requires constitutional review?

### Milestones

**M1: Infrastructure Foundation** (Week 1-2)
- Terraform modules (Cloud Run, Cloud SQL, Redis, Pub/Sub)
- Docker Compose local stack
- CI/CD pipelines
- Shared libs (common, events)

**M2: Core Services** (Week 3-5)
- Agent Creation service (7-stage workflow)
- Agent Execution service (skill runner)
- Governance service (approvals, vetoes)
- Admin Gateway (routing, auth)

**M3: Knowledge & Learning** (Week 6-7)
- Industry Knowledge service (vector DBs)
- Learning service (precedent seeds)
- ML model integration

**M4: Mobile & Polish** (Week 8-10)
- Governor mobile app (Flutter)
- API refinements
- Performance optimization
- Documentation

### Automation Rules

**Auto-label**:
- `service:agent-creation` if title contains "agent creation"
- `component:mobile` if files in `mobile/` changed
- `priority:p0` if title contains "[CRITICAL]"

**Auto-assign**:
- Assign to `@microservices-team` for `services/*` changes
- Assign to `@mobile-team` for `mobile/*` changes
- Assign to `@devops-team` for `infrastructure/*` changes

**Auto-move**:
- Move to "In Progress" when PR opened
- Move to "Review" when PR marked ready
- Move to "Done" when PR merged

**Auto-close**:
- Close issues when PR merged with "Fixes #123"

### Issue Templates

1. **Bug Report** (`bug.yml`)
   - Service affected
   - Steps to reproduce
   - Expected vs actual behavior
   - Logs

2. **Feature Request** (`feature.yml`)
   - User story
   - Acceptance criteria
   - Service impacted
   - Constitutional alignment check

3. **Architectural Deviation** (`architectural-deviation.yml`)
   - Deviation description
   - Reason for deviation
   - Impact analysis
   - Governor approval required

4. **Agent Violation** (`agent-violation.yml`)
   - Agent ID
   - Violation type (constitutional, budget, ethics)
   - Evidence
   - Remediation plan

---

## 📱 Mobile App Integration

### Governor App Features

**Dashboard**:
- Active agents count
- Pending approvals (notifications badge)
- Recent veto actions
- System health metrics

**Approvals Screen**:
- List of pending agent creation requests
- Agent details (ME-WoW, Genesis cert, Architect review)
- Timeline view (7-stage pipeline progress)
- Approve / Request Changes / Veto buttons
- Precedent seed matching suggestions

**Veto Interface**:
- 24-hour veto window countdown
- Veto reason categories (constitutional, safety, budget)
- Free-text explanation
- Attach supporting documents

**Precedent Seeds**:
- Browse active seeds (GEN-002, GEN-004, etc.)
- View seed conditions & auto-approval criteria
- Seed effectiveness metrics (match rate, veto rate)
- Create new seeds (form wizard)

**Notifications**:
- Push: Agent creation pending approval
- Push: Budget threshold exceeded (80%, 95%)
- Push: Agent violated constitutional rule
- Push: Seed match with auto-approval (FYI)

### API Endpoints for Mobile

**Governance Service** (port 8003):
```
GET  /v1/mobile/dashboard           # Dashboard metrics
GET  /v1/mobile/approvals           # Pending approvals list
POST /v1/mobile/approvals/{id}/approve
POST /v1/mobile/approvals/{id}/veto
GET  /v1/mobile/seeds               # Precedent seeds
POST /v1/mobile/seeds               # Create seed
GET  /v1/mobile/agents              # All agents summary
GET  /v1/mobile/violations          # Recent violations
```

**Authentication**:
- OAuth 2.0 (Google/GitHub)
- JWT tokens (15-min expiry, refresh tokens)
- Mobile-specific scopes: `governance:read`, `governance:write`, `veto:execute`

**Offline Support**:
- Cache dashboard data (5-min TTL)
- Queue veto actions (sync when online)
- Local SQLite for precedent seeds

---

## 🚀 Development Workflow

### Local Development

```bash
# 1. Setup
make setup                # Install dependencies
make infra-up             # Start Docker Compose stack
make migrate              # Run database migrations

# 2. Run services
make run-agent-creation   # Start on port 8001
make run-agent-execution  # Start on port 8002
# ... or run all at once:
make run-all

# 3. Mobile app
cd mobile/governor-app
flutter run               # Start on iOS simulator

# 4. Tests
make test-unit            # Unit tests all services
make test-integration     # Integration tests
make test-e2e             # E2E tests

# 5. Cleanup
make clean
make infra-down
```

### CI/CD Pipeline

**On Pull Request**:
1. Lint (Black, isort, Flake8)
2. Type check (mypy)
3. Unit tests (pytest)
4. Integration tests (docker-compose)
5. Security scan (Trivy)
6. Compliance audit (`audit_tech_stack.py`)
7. Build Docker images (no push)

**On Merge to main**:
1. Build & push Docker images
2. Deploy to dev environment
3. Run smoke tests
4. Notify #deployments Slack

**On Tag (v*.*.*)** :
1. Deploy to staging
2. Run full E2E tests
3. Wait for approval
4. Deploy to production
5. Monitor metrics (15 min)
6. Rollback on error rate >1%

---

## 🛠️ Technology Stack

### Backend Services
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.104+
- **Async**: asyncio, aiohttp
- **Database**: PostgreSQL 15 (Cloud SQL)
- **Cache**: Redis 7 (Memorystore)
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Workflow**: Temporal (self-hosted)
- **Event Bus**: Cloud Pub/Sub
- **Vector DB**: Pinecone or Weaviate

### ML & AI
- **Models**: DistilBERT, BART, MiniLM, Phi-3-mini, Prophet
- **Inference**: ONNX Runtime (CPU-optimized)
- **Embeddings**: sentence-transformers
- **Quantization**: 4-bit (Phi-3-mini)
- **Fallbacks**: Rule-based heuristics

### Mobile
- **Framework**: Flutter 3.16+
- **Language**: Dart 3.2+
- **State**: Riverpod
- **HTTP**: Dio
- **Auth**: flutter_appauth (OAuth)
- **Notifications**: Firebase Cloud Messaging

### Infrastructure
- **Cloud**: Google Cloud Platform
- **Compute**: Cloud Run (6 services)
- **IaC**: Terraform 1.6+
- **Containers**: Docker 24+
- **Orchestration**: Cloud Run (not K8s for MVP)
- **Monitoring**: Prometheus + Grafana
- **Logging**: Cloud Logging
- **Tracing**: OpenTelemetry

### CI/CD
- **Platform**: GitHub Actions
- **Container Registry**: Artifact Registry
- **Secrets**: Google Secret Manager
- **Testing**: pytest, Flutter test
- **Coverage**: codecov.io

---

## 💰 Cost Breakdown

**Infrastructure** ($120/month target):
- Cloud Run (6 services): $30-50/month (aggressive autoscale, min 0 instances)
- Cloud SQL (PostgreSQL): $20/month (db-f1-micro with HA disabled for dev)
- Redis Memorystore: $10/month (M1 tier, 1GB)
- Temporal (Cloud Run): $15/month (1 instance)
- Cloud Pub/Sub: $5-10/month (< 1M messages)
- Vector DB: $5-10/month (Pinecone free tier or Weaviate self-hosted)
- Cloud Storage: $2/month (ML models, backups)
- Cloud Logging: $3/month (< 50GB)
- Load Balancer: $20/month (global HTTPS)

**Total**: $110-140/month (within $150 budget)

**Cost Optimization**:
- Cloud Run min instances = 0 (cold start acceptable for dev)
- PostgreSQL connection pooling (PgBouncer, 100 real connections, 1000 virtual)
- Redis caching (L1: in-memory 1-min, L2: Redis 5-min, L3: DB)
- ML model caching (load once, reuse across requests)
- Pub/Sub batching (10 messages per publish)

---

## 🎯 Success Metrics

**Development Velocity**:
- Services deployed: 6/6
- Test coverage: >80%
- API uptime: >99.5%
- Deployment frequency: Daily (dev), Weekly (prod)

**Mobile App**:
- Governor app: iOS + Android
- Approval latency: <5 seconds (API call)
- Push notification delivery: <30 seconds

**Cost Efficiency**:
- Monthly spend: <$150
- Cost per request: <$0.001
- Cold start latency: <2 seconds

**Constitutional Compliance**:
- Audit violations: 0 critical
- Precedent seed match rate: >60%
- Governor veto rate: <5%

---

## 📋 Next Steps

1. **Approve Architecture** ✅
2. **Setup GitHub Project** → Create project, add milestones, configure automation
3. **Provision Infrastructure** → Run Terraform (Cloud Run, Cloud SQL, Redis, Pub/Sub)
4. **Generate Service Skeletons** → 6 FastAPI services with OpenAPI specs
5. **Implement Agent Creation** → 7-stage workflow with Temporal
6. **Build Mobile App MVP** → Governor dashboard + approvals
7. **Integrate & Test** → E2E tests, performance testing
8. **Deploy to Dev** → First production deployment

---

## 🤝 Team Structure

**Microservices Team** (Backend):
- Lead: Microservices architecture, FastAPI, Temporal
- Dev 1: Agent Creation + Execution services
- Dev 2: Governance + Industry Knowledge services
- Dev 3: Learning + Admin Gateway services

**Mobile Team**:
- Lead: Flutter, mobile architecture
- Dev: Governor app implementation

**DevOps Team**:
- Lead: Terraform, GCP, CI/CD
- SRE: Monitoring, incident response

**Platform Governor** (You):
- Constitutional oversight
- Approval/veto authority
- Mobile app primary user

---

## 📚 Reference Documents

**Constitutional Design** (Preserved in `main/`):
- [Foundation.md](main/Foundation.md) - Constitutional principles
- [data_contracts.yml](main/Foundation/contracts/data_contracts.yml) - Data schemas
- [governance_protocols.yaml](main/Foundation/template/governance_protocols.yaml) - Approval workflows

**Architecture Decisions** (Archived):
- [TECH_STACK_SELECTION_POLICY.md](archive/policy/TECH_STACK_SELECTION_POLICY.md)
- [tech_stack.yaml](archive/policy/tech_stack.yaml)
- [TOOLING_SELECTION_DECISION.md](main/Foundation/TOOLING_SELECTION_DECISION.md)

**Session Logs**:
- [run_log.md](main/run_log.md) - Complete session history

---

**Status**: Ready for implementation! 🚀

