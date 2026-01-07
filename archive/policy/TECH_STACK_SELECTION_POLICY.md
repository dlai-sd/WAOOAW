# Technology Stack Selection Policy

**Document Number:** POLICY-TECH-001  
**Version:** 1.0.0  
**Effective Date:** January 3, 2026  
**Review Cycle:** Monthly  
**Next Review Date:** February 3, 2026  
**Policy Owner:** Platform Architecture Team  
**Approval Required:** CTO/Technical Lead

---

## 1. Purpose & Scope

### 1.1 Purpose
This policy establishes the approved technology stack for WAOOAW platform applications to ensure cost optimization, development velocity, maintainability, and industry alignment.

### 1.2 Scope
This policy applies to:
- All frontend web applications (customer-facing and internal)
- All backend API services
- All new application development
- Major rewrites or migrations of existing applications

**Future Expansion Areas:** (To be added in subsequent revisions)
- Database selection criteria
- Message queue and caching technologies
- Monitoring and observability stack
- CI/CD and deployment tools

### 1.3 Applicability
Mandatory for all development teams, contractors, and third-party vendors working on WAOOAW platform.

---

## 2. Policy Statement

**WAOOAW shall adopt a hybrid technology stack optimized for cost efficiency, performance, and rapid deployment. Technology selection prioritizes total cost of ownership (TCO), industry maturity, and team capability over framework popularity or personal preference.**

---

## 3. Approved Technology Stack

### 3.1 Frontend Applications

| Application Type | Approved Technology | Use Case | Repository | Rationale |
|-----------------|---------------------|----------|------------|-----------|
| **Customer Portal** | React 18 + Vite | cp.waooaw.com | WaooawPortal/ | Performance, SEO, cost optimization |
| **Platform Portal** | Reflex (Python) | pp.waooaw.com | PlatformPortal/ | Development velocity, real-time features |
| **Marketing Sites** | Static HTML/CSS | Landing pages (future) | - | SEO, load speed, hosting cost |

### 3.2 Backend Services

| Service Type | Approved Technology | Use Case | Repository | Rationale |
|-------------|---------------------|----------|------------|-----------|
| **Portal API** | FastAPI (Python 3.11+) | OAuth + Agent API | WaooawPortal/backend/ | Lightweight, async, OAuth-focused |
| **Marketplace API** | FastAPI (Python 3.11+) | Agent marketplace, trials | backend/ | Full-featured platform API |
| **Agent Runtime** | Python CLI | Autonomous agents | waooaw/ | Agent execution engine |
| **Workflow Orchestration** | Temporal (self-hosted) | Agent creation, servicing, skill orchestration | infrastructure/temporal/ | Durable execution, Python-native, $15/month |
| **Business Rules Engine** | Python business-rules | Query routing, budget thresholds, seed matching | waooaw/rules/ | Lightweight, externalized rules, $0 cost |
| **Future Consideration** | Django REST Framework | If admin panel required | - | Mature ecosystem, optional addition |

### 3.3 Infrastructure

| Component | Approved Technology | Environment |
|-----------|---------------------|-------------|
| **Cloud Provider** | Google Cloud Platform (GCP) | Production, Staging |
| **Compute** | Cloud Run (Serverless Containers) | All services |
| **Load Balancing** | GCP Application Load Balancer | Multi-domain routing |
| **Container Registry** | GCP Artifact Registry | Container images |

---

## 4. Decision Matrix

### 4.1 Primary Selection Criteria (Weighted)

| Criterion | Weight | Measurement |
|-----------|--------|-------------|
| **Total Cost of Ownership** | 40% | Monthly GCP costs, licensing, dev time |
| **Performance** | 25% | Cold start time, response latency, SEO impact |
| **Industry Support** | 15% | Maturity, hiring pool, ecosystem size |
| **Development Velocity** | 10% | Time to ship, code reusability |
| **Maintainability** | 10% | Team capability, documentation, community |

### 4.2 Cost Optimization Principles

1. **Customer-facing applications** (www, customer portals):
   - Static builds preferred over server-rendered where possible
   - Target: <$10/month per service at low traffic (<100K req/month)
   - Optimize for cold start performance and minimal memory

2. **Internal applications** (pp, dp):
   - Development speed prioritized over marginal cost savings
   - Target: <$25/month per service at typical usage
   - Real-time features and developer productivity outweigh hosting cost

3. **Backend APIs**:
   - Async-first architecture for scalability
   - Target: <$20/month at low traffic, linear scaling
   - Optimize for request throughput over cold start

---

## 5. Cost Governance

### 5.1 Budget Bands

| Traffic Tier | Monthly Budget Ceiling | Services Included | Approval Level |
|-------------|----------------------|-------------------|----------------|
| **Startup Phase** | ≤$100/month | 3 core services + load balancer | Auto-approved |
| **Growth Phase** | $101-$400/month | Scaled services, additional features | CTO Review Required |
| **Scale Phase** | >$400/month | Multi-region, high availability | Executive Approval Required |

### 5.2 Cost Monitoring
- Monthly cost review mandatory
- Alert threshold: 20% variance from budget band
- Cost attribution by service/application required
- Quarterly cost optimization review

### 5.3 Cost Variance Procedure
If monthly costs exceed $100:
1. Engineering team documents cost drivers
2. Submit variance report (max 2 pages) to CTO
3. Propose optimization actions or budget increase justification
4. Obtain written approval before next billing cycle

---

## 6. Implementation Standards

### 6.1 Application-Specific Requirements

#### 6.1.1 Customer-Facing Applications (React)
- **Framework:** React 18+ with Vite or Next.js
- **Styling:** Tailwind CSS or Shadcn/ui (utility-first)
- **State Management:** React Context API or Zustand (lightweight preferred)
- **Build Target:** Static files served via Nginx in Cloud Run
- **Performance:** First Contentful Paint <1.5s, Lighthouse score >90
- **SEO:** React Helmet or Next.js metadata management

#### 6.1.2 Internal Portals (Reflex)
- **Framework:** Reflex v0.8.24+
- **Python Version:** 3.11+
- **State Management:** Reflex server-side state with Redis backing
- **Real-time:** WebSocket-based state sync (built-in)
- **Deployment:** Reflex export → Docker → Cloud Run

#### 6.1.3 Backend APIs (FastAPI)
- **Framework:** FastAPI v0.109+
- **Python Version:** 3.11+
- **API Style:** RESTful with OpenAPI documentation
- **Async:** All I/O operations must use async/await
- **Authentication:** OAuth 2.0 + JWT tokens
- **CORS:** Explicit origin whitelist (no wildcards in production)

### 6.2 Prohibited Technologies

The following technologies are **NOT approved** for new development without explicit CTO approval:

- ❌ PHP-based frameworks (Laravel, Symfony)
- ❌ Ruby on Rails
- ❌ Java/Spring Boot (cold start performance concerns)
- ❌ Angular (legacy versions <14)
- ❌ Vue.js (team capability gap)
- ❌ Server-side rendering without justification (cost vs SEO tradeoff)
- ❌ **Camunda/jBPM/Heavy BPMN Engines** (cost $50-80/month vs Temporal $15/month, Java-based, overkill for constitutional orchestrations) - Use Temporal for workflow orchestration unless visual BPMN design is critical requirement justifying 3-5x cost increase

---

## 7. Microservices Architecture

### 7.1 Service Boundaries (6 Microservices)

**Approved Services:**

| Service | Responsibility | Tech Stack | Port | Team Owner |
|---------|---------------|------------|------|------------|
| **Agent Creation Service** | Agent lifecycle (Genesis→Architect→Guardian→Governor workflow), agent registry writes, Temporal saga orchestration | FastAPI + Python 3.11+, Temporal SDK | 8001 | Platform |
| **Agent Execution Service** | Customer work execution, Manager orchestration, specialist coordination, job completion, seed draft extraction | FastAPI + Python 3.11+, BART-base ML | 8002 | Platform |
| **Governance Service** | Governor approvals, mobile notifications, veto workflows, constitutional compliance, approval audit trail | FastAPI + Python 3.11+, Multi-channel routing | 8003 | Governance |
| **Industry Knowledge Service** | Vector DB operations, embeddings generation, industry corpus management, cache updates, query routing | FastAPI + Python 3.11+, Chroma/Qdrant, OpenAI API | 8004 | Data |
| **Learning Service** | Precedent Seed lifecycle, Genesis review workflows, seed approval, feedback loop orchestration | FastAPI + Python 3.11+, Temporal SDK | 8005 | AI/ML |
| **Admin Gateway Service** | Admin operations aggregation, conversational admin interface, cross-service coordination, metrics dashboard | FastAPI + Python 3.11+, Phi-3-mini NLU | 8006 | Operations |

### 7.2 Service Communication Patterns

**Enforced Standards:**

- **Synchronous (REST):** Service-to-service calls orchestrated by Temporal workflows (Agent Creation → Genesis activity, Manager → Specialist calls)
- **Asynchronous (Pub/Sub):** Broadcast events (AgentStateChanged, SeedApproved, GovernorVetoed, EmbeddingsUpdated, IndustryAdded)
- **Protocol:** REST with OpenAPI 3.1 schemas, JSON payloads, gRPC prohibited unless proven bottleneck (>10K RPS)
- **Authentication:** GCP Workload Identity + JWT tokens, service-to-service mTLS deferred until >10 services

**Event Catalog (Pub/Sub Topics):**

| Topic | Publisher | Subscribers | Schema |
|-------|-----------|-------------|--------|
| `AgentStateChanged` | Agent Creation | All services | `{agent_id, old_state, new_state, timestamp}` |
| `SeedApproved` | Learning | Industry Knowledge, Agent Execution, Agent Creation | `{seed_id, correlation_id, vector_clock}` |
| `GovernorVetoed` | Governance | Agent Creation, Learning | `{approval_id, reason, affected_entities[]}` |
| `EmbeddingsUpdated` | Industry Knowledge | Agent Execution, Agent Creation | `{industry, version, causation_id}` |
| `IndustryAdded` | Industry Knowledge | All services | `{industry_id, name, state, embeddings_ready}` |
| `JobCompleted` | Agent Execution | Learning | `{job_id, result_summary, customer_feedback}` |

### 7.3 Data Management Strategy

**Database Architecture:**

- **Shared PostgreSQL:** Governance, agent registry, seed lifecycle (ACID critical for constitutional operations)
  - Schemas: `governance`, `agents`, `seeds`, `audit_log`
  - Connection pool: PgBouncer (100 real connections, 1000 virtual)
  - Per-service limits: Agent Execution 40, Industry Knowledge 20, Agent Creation 15, Governance 10, Learning 10, Admin 5
- **Separate PostgreSQL:** Industry Knowledge (vector operations, separate scaling)
  - Schema: `industry_embeddings`, `vector_cache`
- **Redis Memorystore:** Multi-level cache (L2), event idempotency tracking, connection queue buffers
  - TTL: L2 cache 5 minutes, idempotency keys 24 hours
- **Vector Database:** Chroma (dev) or Qdrant (prod), self-hosted on Cloud Run

**Event Sourcing:**
- Append-only `audit_log` table for constitutional traceability
- Each event includes: `causation_id`, `correlation_id`, `vector_clock`
- Not full event sourcing (complexity overhead), traditional state + event log

### 7.4 Deviation Detection Rules

**Prohibited Without Approval:**

❌ **New services beyond 6 approved** - Must justify bounded context not covered
❌ **Shared database tables across services** - Except governance/agents/seeds schemas
❌ **Synchronous chains >3 hops** - Use Temporal workflow or pub/sub events
❌ **gRPC without benchmark proof** - Must show REST <10K RPS bottleneck
❌ **Direct service-to-service calls** - Must go through Temporal or use pub/sub
❌ **Events without causation tracking** - All events require `causation_id`, `correlation_id`
❌ **Cache without invalidation strategy** - Must subscribe to relevant pub/sub topics
❌ **Admin operations bypassing Admin Gateway** - All admin calls via gateway for audit

## 8. ML Models Registry

### 8.1 Approved Small/Medium Models

**All models run on CPU, no GPU required. Inference <200ms. Open source.**

| Model | Size | Use Case | Service | Inference Time | Cost |
|-------|------|----------|---------|----------------|------|
| **DistilBERT** | 66MB | Agent prediction (cache warming), ETA estimation (seed processing) | Agent Execution | 50-100ms | $0 |
| **BART-base** | 140MB | Seed summarization (extract precedent from job results) | Agent Execution | 100-200ms | $0 |
| **all-MiniLM-L6-v2** | 22MB | Semantic cache (query embedding similarity matching) | Industry Knowledge | 30-50ms | $0 |
| **Phi-3-mini** (4-bit) | 1GB | Conversational admin (natural language → API calls) | Admin Gateway | 150-300ms | $0 |
| **Prophet** | 10MB | Time-series prediction (load forecasting, cache warming) | Agent Execution | 50ms | $0 |
| **Logistic Regression** | <1MB | Notification channel routing (predict Governor response time) | Governance | 5ms | $0 |
| **LSTM Tiny** | 5MB | Database connection load prediction | All services | 10ms | $0 |

**Total ML Infrastructure Cost:** $0/month (all models run in-service on Cloud Run CPU)

### 8.2 ML Usage Patterns

**Enforced Standards:**

- **Inference Location:** Models run within service process (no separate ML service unless >5 models)
- **Model Storage:** Models bundled in Docker image or loaded from GCS bucket at startup
- **Training:** Background jobs in service (Prophet daily, Logistic Regression daily, BART/DistilBERT pre-trained no retraining)
- **Monitoring:** Log inference time, accuracy metrics (where applicable), model version
- **Fallback:** All ML predictions have non-ML fallback (Prophet fails → use 7-day average, Phi-3 fails → show command palette)

### 8.3 Prohibited ML Patterns

❌ **Large models (>2GB)** - Cloud Run 2GB RAM limit, would require GPU instances ($100+/month)
❌ **Synchronous ML in request path** - Only async background (seed extraction, cache warming) or <100ms inference (MiniLM, Logistic Regression)
❌ **External ML APIs in hot path** - OpenAI embeddings only for admin operations (industry setup), not customer queries
❌ **Models without fallback** - System must function with degraded UX if model fails

## 9. Architectural Patterns

### 9.1 Enforced Patterns

**Saga Pattern (Rollback Coordination):**
- Use Temporal workflows with compensation activities
- Agent Creation workflow: Genesis → Architect → Guardian → Governor (with rollback steps)
- Governor veto triggers reverse compensations: Guardian rollback, Architect rollback, Genesis notify

**Event Sourcing (Audit Trail):**
- Append-only `audit_log` table for constitutional traceability
- Events include: `causation_id` (what triggered), `correlation_id` (original request), `vector_clock` (ordering)
- Services track processed event IDs in Redis (24-hour TTL) for idempotency

**Multi-Level Caching:**
- **L1 (Local):** In-memory per service instance, 1-minute TTL (hot queries)
- **L2 (Redis):** Shared across instances, 5-minute TTL (warm queries)
- **L3 (Source):** Vector DB, PostgreSQL (cold queries)
- Semantic cache: MiniLM embeddings for query similarity (cosine >0.95 = cache hit)

**Predictive Infrastructure:**
- Prophet predicts load 5 minutes ahead → pre-scale services
- Prophet predicts hot queries → pre-warm cache
- LSTM predicts DB connection spikes → adjust PgBouncer pool

**Circuit Breaker:**
- Connection wait >2s → open circuit → return 503
- Auto-close after 30s
- Downstream 429 Too Many Requests → exponential backoff (100ms → 200ms → 400ms)

**Feature Flags (Industry Lifecycle):**
- States: `draft` → `embeddings_generating` → `agents_pending` → `active` → `deprecated`
- Services check industry state before processing
- Customer query for `agents_pending` industry → offer waitlist

### 9.2 Prohibited Anti-Patterns

❌ **Two-Phase Commit (2PC)** - Use Temporal saga instead
❌ **Distributed Transactions** - Use eventual consistency + compensating transactions
❌ **Synchronous Cascading Calls** - Use Temporal orchestration or pub/sub
❌ **Timestamp-Based Ordering** - Use vector clocks for causal consistency
❌ **Polling for State Changes** - Use pub/sub events with polling fallback only (5-min reconciliation)
❌ **Hardcoded Retry Logic** - Use Temporal built-in retry policies

## 10. Deviation & Exception Process

### 10.1 When Deviation is Permitted
Deviations from this policy may be requested for:
- Specialized use cases not covered by approved stack
- Vendor/partner integration requirements
- Performance bottlenecks with documented evidence
- Significant cost savings (>30%) with alternative technology

### 10.2 Deviation Request Process
1. **Document Rationale** (max 3 pages):
   - Problem statement
   - Why approved stack is insufficient
   - Proposed alternative technology
   - Cost comparison (TCO over 12 months)
   - Performance benchmarks
   - Team capability assessment
   - Migration/rollback plan

2. **Submit to CTO** for review

3. **Approval Requirements:**
   - Low risk (<$50/month impact): CTO approval sufficient
   - Medium risk ($50-150/month impact): CTO + Architecture review
   - High risk (>$150/month or multi-service impact): Executive approval

4. **Documentation:**
   - Approved deviations logged in policy appendix
   - Annual review of all active deviations

### 10.3 Emergency Override
In production incidents, temporary deviations permitted with:
- Post-incident review within 48 hours
- Retroactive approval request within 1 week
- Permanent deviation or rollback plan within 2 weeks

---

## 11. Compliance & Audit

### 11.1 Audit Trail Requirements
All technology decisions must maintain:
- Decision date and rationale (max 1 page)
- Cost analysis supporting decision (max 2 pages)
- Stakeholder approval records
- Performance benchmarks (where applicable)

### 11.2 Compliance Checks
Quarterly audits shall verify:
- ✅ All production services use approved stack
- ✅ Monthly costs within budget bands
- ✅ No unapproved frameworks in production
- ✅ Documentation standards maintained
- ✅ Deviation approvals on file

### 11.3 Non-Compliance Remediation
- **First violation:** Warning + 30-day remediation plan
- **Repeat violation:** Service freeze until compliant
- **Critical violation:** Immediate rollback + incident review

---

## 12. Review & Amendment

### 12.1 Monthly Review
Architecture team reviews:
- Cost performance vs budget
- New framework versions or alternatives
- Developer feedback
- Industry trends

### 12.2 Policy Updates
- **Minor updates** (version bump, clarifications): CTO approval
- **Major changes** (new technology, stack change): Executive approval + team review
- All changes documented in version history

### 12.3 Effective Date of Changes
- Policy changes effective 30 days after approval (unless emergency)
- Active projects may complete under previous policy version
- New projects must use updated policy immediately

---

## 13. Repository Structure

### 13.1 Core Repositories

| Repository | Purpose | Technology | Status |
|------------|---------|------------|--------|
| **backend/** | Marketplace API (where customers buy agents) | FastAPI, PostgreSQL, Redis, Celery | ✅ Active (not deployed) |
| **waooaw/** | Agent Runtime (the actual AI workers) | Python CLI, Anthropic, GitHub API | ✅ Active |
| **WaooawPortal/** | Customer portal + OAuth API | React 18 + Vite, FastAPI | ✅ Deployed (cp.waooaw.com) |
| **PlatformPortal/** | Platform operations portal | Reflex (Python) | ✅ Deployed (pp.waooaw.com) |

### 13.2 Architecture Principles

1. **backend/** = Marketplace where customers buy agents (full-featured FastAPI platform)
2. **waooaw/** = Actual agents that do the work (autonomous execution engine)
3. **WaooawPortal/** = Customer-facing portal (self-contained: frontend + backend)
4. **PlatformPortal/** = Internal operations dashboard (Reflex)

### 13.3 Deployment Status

- **Deployed**: WaooawPortal, PlatformPortal
- **Development**: backend/ (marketplace API), waooaw/ (agent runtime)
- **Integration**: backend/ + waooaw/ will power full marketplace (future)

## 14. Approved Service Architecture

### 14.1 Production Domain Mapping

| Domain | Application | Technology | Repository | Monthly Budget Target |
|--------|-------------|------------|------------|---------------------|
| cp.waooaw.com | Customer portal | React 18 + Vite | WaooawPortal/ | $6-10 |
| pp.waooaw.com | Platform portal | Reflex (Python) | PlatformPortal/ | $18-25 |
| api.waooaw.com | Backend API | FastAPI (Python) | WaooawPortal/backend/ | $12-20 |
| **Total (Startup Phase)** | 3 core services + LB | - | **$45-80/month** |

### 14.2 Scaling Bands

| Traffic Level | Request Volume | Cost Band | Infrastructure Changes |
|---------------|---------------|-----------|----------------------|
| Startup | <100K req/month | $45-100 | Single region, scale-to-zero |
| Growth | 100K-1M req/month | $100-400 | Cloud CDN, min instances |
| Scale | >1M req/month | $400-1500 | Multi-region, managed DB |

---

## 15. Supporting Documentation

### 15.1 Reference Materials
This policy is supported by the following analysis documents (maintained separately):

1. **Technology Stack Analysis (Jan 2026)** - 3 pages
   - Reflex vs React comparison
   - Django vs FastAPI evaluation
   - Performance benchmarks
   - Cost projections

2. **GCP Architecture Decision Record** - 2 pages
   - Cloud Run vs GKE evaluation
   - Load Balancer configuration rationale
   - Multi-domain hosting strategy

3. **Budget Forecast Model** - 1 page
   - Cost modeling by traffic tier
   - Scaling assumptions
   - Cost optimization strategies

### 11.2 Living Documents
- Updated monthly with actual cost data
- Maintained in `/policy/supporting/` directory
- Max 3 pages per document (audit requirement)

---

## 12. Roles & Responsibilities

| Role | Responsibility |
|------|---------------|
| **CTO/Technical Lead** | Policy approval, deviation review, budget oversight |
| **Platform Architecture Team** | Policy maintenance, technology evaluation, compliance audits |
| **Engineering Teams** | Policy adherence, cost monitoring, deviation requests |
| **DevOps Team** | Infrastructure implementation, cost tracking, performance monitoring |

---

## 13. Definitions

| Term | Definition |
|------|------------|
| **TCO** | Total Cost of Ownership - includes hosting, development time, maintenance, and operational costs |
| **Cold Start** | Time from zero instances to first request served (serverless metric) |
| **Static Build** | Compiled JavaScript/CSS/HTML served without server-side rendering |
| **SPA** | Single Page Application - client-side rendered web application |
| **SSR** | Server-Side Rendering - HTML generated on server per request |

---

## Version History

| Version | Date | Changes | Approved By |
|---------|------|---------|-------------|
| 1.0.0 | Jan 3, 2026 | Initial policy creation | CTO |
| | | Hybrid React+Reflex stack approved | |
| | | Cost band <$150/month established | |
| 1.1.0 | Jan 4, 2026 | Architecture cleanup & clarification | CTO |
| | | Updated to v2 architecture (3 core services) | |
| | | Reduced budget target: $45-80/month | |
| | | Documented backend/ vs waooaw/ separation | |
| | | Removed deprecated portals (dp, www) | |

---

## Acknowledgment

By deploying applications on the WAOOAW platform, development teams acknowledge:
- ✅ Understanding of this policy
- ✅ Commitment to approved technology stack
- ✅ Responsibility for cost management
- ✅ Obligation to request deviations before implementation

---

**Policy Status:** ✅ **ACTIVE**  
**Document Version**: 2.0  
**Last Updated**: 2026-01-07 (Session 3 - Microservices Architecture & Gap Resolution)  
**Next Review:** February 3, 2026  
**Contact:** Platform Architecture Team

---

*This is a controlled document. Unauthorized modifications are prohibited. All changes must follow the amendment process outlined in Section 12.*
