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

---

## 7. Deviation & Exception Process

### 7.1 When Deviation is Permitted
Deviations from this policy may be requested for:
- Specialized use cases not covered by approved stack
- Vendor/partner integration requirements
- Performance bottlenecks with documented evidence
- Significant cost savings (>30%) with alternative technology

### 7.2 Deviation Request Process
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

### 7.3 Emergency Override
In production incidents, temporary deviations permitted with:
- Post-incident review within 48 hours
- Retroactive approval request within 1 week
- Permanent deviation or rollback plan within 2 weeks

---

## 8. Compliance & Audit

### 8.1 Audit Trail Requirements
All technology decisions must maintain:
- Decision date and rationale (max 1 page)
- Cost analysis supporting decision (max 2 pages)
- Stakeholder approval records
- Performance benchmarks (where applicable)

### 8.2 Compliance Checks
Quarterly audits shall verify:
- ✅ All production services use approved stack
- ✅ Monthly costs within budget bands
- ✅ No unapproved frameworks in production
- ✅ Documentation standards maintained
- ✅ Deviation approvals on file

### 8.3 Non-Compliance Remediation
- **First violation:** Warning + 30-day remediation plan
- **Repeat violation:** Service freeze until compliant
- **Critical violation:** Immediate rollback + incident review

---

## 9. Review & Amendment

### 9.1 Monthly Review
Architecture team reviews:
- Cost performance vs budget
- New framework versions or alternatives
- Developer feedback
- Industry trends

### 9.2 Policy Updates
- **Minor updates** (version bump, clarifications): CTO approval
- **Major changes** (new technology, stack change): Executive approval + team review
- All changes documented in version history

### 9.3 Effective Date of Changes
- Policy changes effective 30 days after approval (unless emergency)
- Active projects may complete under previous policy version
- New projects must use updated policy immediately

---

## 10. Repository Structure

### 10.1 Core Repositories

| Repository | Purpose | Technology | Status |
|------------|---------|------------|--------|
| **backend/** | Marketplace API (where customers buy agents) | FastAPI, PostgreSQL, Redis, Celery | ✅ Active (not deployed) |
| **waooaw/** | Agent Runtime (the actual AI workers) | Python CLI, Anthropic, GitHub API | ✅ Active |
| **WaooawPortal/** | Customer portal + OAuth API | React 18 + Vite, FastAPI | ✅ Deployed (cp.waooaw.com) |
| **PlatformPortal/** | Platform operations portal | Reflex (Python) | ✅ Deployed (pp.waooaw.com) |

### 10.2 Architecture Principles

1. **backend/** = Marketplace where customers buy agents (full-featured FastAPI platform)
2. **waooaw/** = Actual agents that do the work (autonomous execution engine)
3. **WaooawPortal/** = Customer-facing portal (self-contained: frontend + backend)
4. **PlatformPortal/** = Internal operations dashboard (Reflex)

### 10.3 Deployment Status

- **Deployed**: WaooawPortal, PlatformPortal
- **Development**: backend/ (marketplace API), waooaw/ (agent runtime)
- **Integration**: backend/ + waooaw/ will power full marketplace (future)

## 11. Approved Service Architecture

### 11.1 Production Domain Mapping

| Domain | Application | Technology | Repository | Monthly Budget Target |
|--------|-------------|------------|------------|---------------------|
| cp.waooaw.com | Customer portal | React 18 + Vite | WaooawPortal/ | $6-10 |
| pp.waooaw.com | Platform portal | Reflex (Python) | PlatformPortal/ | $18-25 |
| api.waooaw.com | Backend API | FastAPI (Python) | WaooawPortal/backend/ | $12-20 |
| **Total (Startup Phase)** | 3 core services + LB | - | **$45-80/month** |

### 10.2 Scaling Bands

| Traffic Level | Request Volume | Cost Band | Infrastructure Changes |
|---------------|---------------|-----------|----------------------|
| Startup | <100K req/month | $45-100 | Single region, scale-to-zero |
| Growth | 100K-1M req/month | $100-400 | Cloud CDN, min instances |
| Scale | >1M req/month | $400-1500 | Multi-region, managed DB |

---

## 11. Supporting Documentation

### 11.1 Reference Materials
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
**Next Review:** February 3, 2026  
**Contact:** Platform Architecture Team

---

*This is a controlled document. Unauthorized modifications are prohibited. All changes must follow the amendment process outlined in Section 9.*
