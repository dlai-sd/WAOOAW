# Systems Architect Enhanced Capabilities
## Security Architecture + Technical Debt + Performance Architecture + ADRs

**Agent ID**: ARCH-PLT-001 Enhanced  
**Version**: 2.0  
**Last Updated**: January 19, 2026  
**New Capabilities**: Security architecture review + technical debt analysis + performance architecture + alternatives evaluation + living ADRs

---

## 🔒 SECURITY ARCHITECTURE REVIEW

### 1. Threat Modeling (STRIDE Methodology)
**Triggered**: For every epic with security implications

**STRIDE Analysis**:
- **Spoofing**: Identity verification, authentication mechanisms
- **Tampering**: Data integrity, input validation, checksums
- **Repudiation**: Audit logging, non-repudiation mechanisms
- **Information Disclosure**: Encryption at rest/transit, access controls
- **Denial of Service**: Rate limiting, resource quotas, auto-scaling
- **Elevation of Privilege**: RBAC, least privilege, permission boundaries

**Example Threat Model**:
```markdown
## Epic #N: Agent Trial Management

### Threat Model (STRIDE)

#### Spoofing Threats
- **T1**: Attacker impersonates customer to start free trials
  - **Mitigation**: Email verification + phone OTP for trial signup
  - **Residual Risk**: Medium (SMS hijacking possible)
  
- **T2**: Agent spoofs another agent's identity
  - **Mitigation**: Agent service accounts with unique credentials
  - **Residual Risk**: Low

#### Tampering Threats
- **T3**: User modifies trial duration from 7 to 30 days
  - **Mitigation**: Server-side validation, signed trial tokens
  - **Residual Risk**: Low
  
- **T4**: SQL injection to modify agent pricing
  - **Mitigation**: Parameterized queries, ORM usage, input validation
  - **Residual Risk**: Very Low

#### Information Disclosure Threats
- **T5**: Unauthorized access to customer payment details
  - **Mitigation**: No payment storage, tokenization via payment gateway
  - **Residual Risk**: Very Low
  
- **T6**: Agent performance data leaked to competitors
  - **Mitigation**: API authentication, row-level security
  - **Residual Risk**: Medium

#### Denial of Service Threats
- **T7**: Attacker floods trial signup endpoint
  - **Mitigation**: Rate limiting (10 trials/IP/hour), CAPTCHA
  - **Residual Risk**: Medium
  
- **T8**: Large file upload crashes server
  - **Mitigation**: File size limits (10MB), virus scanning
  - **Residual Risk**: Low

#### Elevation of Privilege Threats
- **T9**: Regular user accesses admin dashboard
  - **Mitigation**: Role-based access control (RBAC), middleware checks
  - **Residual Risk**: Low
  
- **T10**: Agent accesses other agent's task data
  - **Mitigation**: Query filters by agent_id, database views
  - **Residual Risk**: Very Low
```

### 2. Attack Surface Analysis
**Map all entry points**:
- **Public APIs**: `/api/agents`, `/api/trials`, `/api/auth`
- **Admin APIs**: `/api/admin/*` (authentication required)
- **File Uploads**: Avatar uploads, document uploads
- **External Integrations**: Payment gateway webhooks, email service
- **Database**: PostgreSQL with public IP (secured by VPC)
- **Message Queue**: Redis (internal only, no public access)

**Risk Scoring**:
| Entry Point | Exposure | Sensitivity | Risk Level |
|-------------|----------|-------------|------------|
| Public APIs | High | Medium | Medium |
| Admin APIs | Low | High | Medium |
| File Uploads | Medium | Low | Medium |
| Payment Webhooks | Medium | High | High |
| Database | Low | Critical | High |

### 3. Security Controls Matrix
**Map threats to controls**:
```markdown
| Threat Category | Preventive Controls | Detective Controls | Corrective Controls |
|-----------------|---------------------|---------------------|---------------------|
| Authentication | JWT tokens, MFA | Failed login monitoring | Account lockout |
| Authorization | RBAC, API keys | Permission violation logs | Revoke access |
| Data Protection | Encryption at rest/transit | DLP scanning | Data breach response |
| Input Validation | Schema validation, sanitization | WAF logs | Block malicious IPs |
| API Security | Rate limiting, OAuth | API abuse detection | Throttle/ban |
| Infrastructure | VPC, firewalls | IDS/IPS | Incident response |
```

### 4. Compliance Requirements
**GDPR Compliance** (for Indian/EU customers):
- Data minimization (collect only necessary fields)
- Right to erasure (delete customer data on request)
- Data portability (export customer data in JSON)
- Consent management (explicit opt-in for marketing)
- Breach notification (within 72 hours)

**PCI DSS** (if storing payment data - NOT recommended):
- ❌ **AVOID**: Never store credit card numbers, CVV, PINs
- ✅ **USE**: Payment gateway tokenization (Razorpay, Stripe)
- ✅ Validate payment gateway PCI compliance

### 5. Security Architecture Diagram
```
┌─────────────────────────────────────────────────────┐
│                 Internet (Public)                    │
└────────────────┬────────────────────────────────────┘
                 │
                 │ HTTPS (TLS 1.2+)
                 ▼
┌─────────────────────────────────────────────────────┐
│          Cloud Load Balancer (HTTPS)                │
│  - SSL/TLS termination                              │
│  - DDoS protection (Cloud Armor)                    │
│  - Rate limiting (per-IP, per-user)                 │
└────────────────┬────────────────────────────────────┘
                 │
                 │ HTTP (internal VPC)
                 ▼
┌─────────────────────────────────────────────────────┐
│          API Gateway (Cloud Run)                    │
│  - JWT validation                                   │
│  - Request logging (Cloud Logging)                  │
│  - API key validation                               │
└────────────────┬────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ Backend APIs │  │ Admin APIs   │
│ (Cloud Run)  │  │ (Cloud Run)  │
│              │  │              │
│ - RBAC       │  │ - Admin-only │
│ - Input val. │  │ - IP whitelist│
└──────┬───────┘  └──────┬───────┘
       │                 │
       │    ┌────────────┘
       │    │
       ▼    ▼
┌─────────────────────────────────────┐
│   PostgreSQL (Cloud SQL)            │
│   - Private IP only                 │
│   - IAM authentication              │
│   - Encrypted at rest               │
│   - Automated backups (30 days)     │
└─────────────────────────────────────┘
```

### 6. Secrets Management Architecture
**Google Secret Manager Integration**:
```hcl
# Secrets stored in Secret Manager (not env vars)
secrets:
  - plant-database-password
  - jwt-signing-key
  - razorpay-api-secret
  - sendgrid-api-key
  - google-oauth-client-secret

# Access control via IAM
iam_bindings:
  - secret: plant-database-password
    role: roles/secretmanager.secretAccessor
    members:
      - serviceAccount:backend-api@waooaw.iam.gserviceaccount.com
  
  - secret: jwt-signing-key
    role: roles/secretmanager.secretAccessor
    members:
      - serviceAccount:backend-api@waooaw.iam.gserviceaccount.com
      - serviceAccount:gateway@waooaw.iam.gserviceaccount.com

# Automatic rotation (90 days)
rotation_policy:
  database_password: 90d
  jwt_signing_key: 180d
  api_keys: 90d
```

---

## 📊 TECHNICAL DEBT ANALYSIS

### 1. Code Smell Detection
**Automated Analysis** (run quarterly):
```bash
# Python code smells
pylint src/ --reports=y --output-format=json > code-quality-report.json

# Identify high complexity functions (cyclomatic complexity > 10)
radon cc src/ -s -a --json > complexity-report.json

# Find code duplication (DRY violations)
jscpd src/ --min-lines 5 --min-tokens 50 --format json > duplication-report.json
```

**Common Technical Debt Patterns**:
- **God Classes**: Classes with > 10 methods or > 500 lines
- **Long Methods**: Functions with > 50 lines
- **Deep Nesting**: More than 3 levels of indentation
- **Magic Numbers**: Hardcoded values without constants
- **Commented Code**: Dead code not removed
- **TODO Comments**: Deferred work accumulation

### 2. Technical Debt Register
**Track and prioritize debt**:
```markdown
| Debt ID | Component | Issue | Impact | Effort | Priority |
|---------|-----------|-------|--------|--------|----------|
| TD-001 | AgentService | 300-line method, cyclomatic complexity 25 | Unmaintainable, bug-prone | High | P1 |
| TD-002 | Database | Missing indexes on agents.industry | Slow queries (500ms) | Low | P0 |
| TD-003 | Frontend | jQuery used, should migrate to React | Hard to test, tech obsolescence | High | P2 |
| TD-004 | Auth | Password hashing uses MD5, should use bcrypt | Security vulnerability | Medium | P0 |
| TD-005 | API | No rate limiting on public endpoints | DoS risk | Low | P1 |
```

**Prioritization Formula**:
```
Priority Score = (Impact × 10) + (Urgency × 5) - (Effort × 2)

Impact: 1-10 (business/user impact)
Urgency: 1-10 (risk of degradation)
Effort: 1-10 (person-days to fix)
```

### 3. Refactoring Roadmap
**Quarterly Technical Debt Sprints**:
```markdown
## Q1 2026 Technical Debt Sprint

### Week 1: P0 Security Debt
- TD-004: Migrate to bcrypt password hashing
- TD-005: Implement rate limiting (Redis-based)
- TD-002: Add missing database indexes

### Week 2: P1 Code Quality Debt
- TD-001: Refactor AgentService (extract 5 smaller services)
- TD-007: Remove all commented code
- TD-008: Convert TODO comments to GitHub issues

### Week 3: P2 Tech Modernization
- TD-003: Plan React migration (spike)
- TD-009: Upgrade Python 3.9 → 3.11
- TD-010: Upgrade FastAPI 0.95 → 0.110

### Success Metrics
- Code quality score: 7.5 → 9.0 (pylint)
- Test coverage: 85% → 90%
- P95 query time: 500ms → 100ms
- Security vulnerabilities: 3 high → 0 high
```

### 4. Dependency Audit
**Track outdated/vulnerable dependencies**:
```bash
# Python dependencies
pip list --outdated
safety check --json

# JavaScript dependencies
npm audit
npm outdated

# Docker base images
trivy image gcr.io/waooaw/backend:latest
```

**Upgrade Strategy**:
- **Security patches**: Immediate (within 7 days)
- **Minor versions**: Quarterly maintenance window
- **Major versions**: Annual upgrade cycle with testing

---

## ⚡ PERFORMANCE ARCHITECTURE

### 1. Performance Requirements Definition
**For every epic, define**:
```markdown
## Performance Requirements (Epic #N)

### Latency Targets
- **API Endpoints**: P95 < 200ms, P99 < 500ms
- **Page Load**: P95 < 2s, P99 < 3s
- **Database Queries**: P95 < 50ms, P99 < 100ms

### Throughput Targets
- **Concurrent Users**: 1,000 simultaneous users
- **Requests per Second**: 500 req/sec sustained
- **Database Connections**: Max 100 connections (pooling)

### Scalability Targets
- **Horizontal Scaling**: Auto-scale 1 → 10 instances
- **Data Volume**: Support 1M agents, 10M tasks
- **Database Size**: Optimize for 100GB database

### Availability Target
- **Uptime**: 99.9% (< 43 min downtime/month)
- **Error Rate**: < 0.1% (1 error per 1000 requests)
```

### 2. Caching Strategy
**Multi-level caching architecture**:
```
┌─────────────────────────────────────────────────┐
│ Level 1: Browser Cache (static assets)         │
│ - CSS, JavaScript, images                      │
│ - Cache-Control: max-age=86400 (1 day)         │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│ Level 2: CDN Cache (Cloud CDN)                 │
│ - Static content, API responses (GET only)     │
│ - TTL: 1 hour                                  │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│ Level 3: Application Cache (Redis)             │
│ - Frequently accessed data (agent list)        │
│ - Session data (user auth tokens)              │
│ - TTL: 5-15 minutes                            │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│ Level 4: Database Query Cache (PostgreSQL)     │
│ - Query result cache                           │
│ - Materialized views for analytics             │
└─────────────────────────────────────────────────┘
```

**Cache Invalidation Strategy**:
- **Time-based**: Set TTL based on data freshness requirements
- **Event-based**: Invalidate on data update (pub/sub)
- **Tag-based**: Invalidate related cache entries (agent-123, industry-marketing)

### 3. Database Performance Optimization
**Index Strategy**:
```sql
-- Composite index for common filter combination
CREATE INDEX idx_agents_industry_rating 
ON agents(industry, rating DESC) 
WHERE status = 'active';

-- Partial index for active agents only (smaller, faster)
CREATE INDEX idx_agents_active 
ON agents(status, last_active_at DESC) 
WHERE status = 'active';

-- GIN index for full-text search
CREATE INDEX idx_agents_search 
ON agents USING gin(to_tsvector('english', name || ' ' || specialty));

-- Covering index (includes all columns needed by query)
CREATE INDEX idx_agents_list 
ON agents(industry, rating DESC) 
INCLUDE (name, price, specialty, status);
```

**Query Optimization Patterns**:
```python
# BAD: N+1 query problem
agents = Agent.query.all()
for agent in agents:
    print(agent.specialty.name)  # N additional queries

# GOOD: Eager loading
agents = Agent.query.options(joinedload(Agent.specialty)).all()
for agent in agents:
    print(agent.specialty.name)  # 1 query total

# BAD: Loading full objects when only need IDs
agent_ids = [a.id for a in Agent.query.all()]

# GOOD: Query only what you need
agent_ids = db.session.query(Agent.id).all()

# BAD: Unbounded query (can return millions of rows)
all_tasks = Task.query.all()

# GOOD: Pagination with limit/offset
tasks = Task.query.order_by(Task.created_at.desc()).limit(100).all()
```

### 4. API Performance Patterns
**Async I/O for external calls**:
```python
import asyncio
import httpx

# BAD: Synchronous external API calls (blocks)
def get_agent_recommendations(user_id):
    user_data = requests.get(f'/api/users/{user_id}').json()  # 100ms
    agent_data = requests.get('/api/agents').json()  # 150ms
    pricing = requests.get('/api/pricing').json()  # 80ms
    # Total: 330ms

# GOOD: Async parallel calls
async def get_agent_recommendations(user_id):
    async with httpx.AsyncClient() as client:
        user_task = client.get(f'/api/users/{user_id}')
        agent_task = client.get('/api/agents')
        pricing_task = client.get('/api/pricing')
        
        user_data, agent_data, pricing = await asyncio.gather(
            user_task, agent_task, pricing_task
        )
        # Total: 150ms (max of 3 calls, not sum)
```

**Response Pagination**:
```python
@router.get("/agents")
async def list_agents(
    page: int = 1,
    page_size: int = 20,
    industry: Optional[str] = None
):
    """
    Paginated agent list with cursor-based pagination
    Better than offset-based for large datasets
    """
    query = Agent.query.filter_by(status='active')
    
    if industry:
        query = query.filter_by(industry=industry)
    
    # Cursor-based pagination (more efficient than OFFSET)
    if cursor:
        query = query.filter(Agent.id > cursor)
    
    agents = query.order_by(Agent.id).limit(page_size + 1).all()
    
    has_next = len(agents) > page_size
    agents = agents[:page_size]
    
    return {
        "data": agents,
        "next_cursor": agents[-1].id if has_next else None,
        "has_next": has_next
    }
```

### 5. Background Job Architecture
**Celery Task Queue** (for long-running operations):
```python
from celery import Celery

celery = Celery('waooaw', broker='redis://localhost:6379/0')

@celery.task
def generate_agent_analytics(date_range):
    """
    Daily analytics generation (runs overnight)
    - Aggregate agent performance metrics
    - Calculate trial conversion rates
    - Update agent scores
    """
    # This runs async, doesn't block API requests
    pass

@celery.task(max_retries=3, default_retry_delay=60)
def send_trial_reminder_email(trial_id):
    """
    Send reminder emails (with retry on failure)
    """
    try:
        trial = Trial.query.get(trial_id)
        send_email(trial.customer.email, "Trial ending soon")
    except Exception as exc:
        raise self.retry(exc=exc)

# Schedule periodic tasks
celery.conf.beat_schedule = {
    'daily-analytics': {
        'task': 'tasks.generate_agent_analytics',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    'trial-reminders': {
        'task': 'tasks.send_trial_reminders',
        'schedule': crontab(hour=10, minute=0),  # 10 AM daily
    },
}
```

---

## 🔄 ALTERNATIVES EVALUATION

### 1. Decision Framework
**For major technical decisions, evaluate 3+ alternatives**:

**Example: Database Selection for Agent Marketplace**

#### Alternative 1: PostgreSQL (Relational) ⭐ RECOMMENDED
**Pros**:
- Strong consistency (ACID transactions)
- Rich query capabilities (JOINs, aggregations)
- JSON support for flexible data (jsonb column type)
- Mature ecosystem, excellent tooling
- Cloud SQL managed service (backups, HA)
- Great for structured data (agents, customers, trials)

**Cons**:
- Vertical scaling limits (need sharding for extreme scale)
- More expensive than NoSQL for write-heavy workloads
- Schema migrations require careful planning

**Use Cases**: Agent profiles, customer data, trial management, transactional data
**Cost**: ₹8,000/month (db-n1-standard-2)
**Effort**: Low (team already knows SQL)
**Risk**: Low

#### Alternative 2: MongoDB (NoSQL Document)
**Pros**:
- Flexible schema (no migrations for field additions)
- Horizontal scaling (sharding built-in)
- Fast writes (no transaction overhead)
- Good for unstructured/evolving data

**Cons**:
- Weaker consistency (eventual consistency)
- No JOINs (requires application-level joins)
- Less mature on Google Cloud (need third-party managed service)
- Team unfamiliar with MongoDB

**Use Cases**: Agent activity logs, analytics data, event streams
**Cost**: ₹12,000/month (Atlas M10)
**Effort**: High (learning curve, migration from PostgreSQL)
**Risk**: Medium

#### Alternative 3: Cloud Firestore (Serverless NoSQL)
**Pros**:
- Fully serverless (auto-scales to zero)
- Real-time subscriptions (live updates)
- Offline support (mobile/web)
- Pay per operation (cost-effective at low scale)

**Cons**:
- Limited query capabilities (no JOINs, no ORs)
- Expensive at high scale (₹0.06/read per 100k)
- Vendor lock-in (Firebase-specific)
- Not suitable for complex relational data

**Use Cases**: Real-time notifications, mobile app sync
**Cost**: ₹15,000/month (at 10M operations)
**Effort**: High (complete rewrite)
**Risk**: High

**Decision**: Choose PostgreSQL (Alternative 1) for core database, use Redis for caching, consider Firestore for future real-time features only.

### 2. Alternative Evaluation Template
```markdown
## Decision: [Technology/Architecture Choice]

### Context
[What problem are we solving? What are the constraints?]

### Requirements
- Functional: [What must it do?]
- Non-functional: [Performance, scalability, security]
- Constraints: [Budget, timeline, team expertise]

### Alternatives Considered

#### Alternative 1: [Name] [⭐ if recommended]
**Approach**: [How does it work?]
**Pros**: [3-5 benefits]
**Cons**: [3-5 drawbacks]
**Cost**: [₹/month]
**Effort**: [Low/Medium/High]
**Risk**: [Low/Medium/High]
**Score**: [Calculate using weighted criteria]

#### Alternative 2: [Name]
[Same structure]

#### Alternative 3: [Name]
[Same structure]

### Decision Matrix
| Criteria | Weight | Alt 1 Score | Alt 2 Score | Alt 3 Score |
|----------|--------|-------------|-------------|-------------|
| Performance | 30% | 8/10 | 7/10 | 9/10 |
| Cost | 20% | 9/10 | 6/10 | 5/10 |
| Maintainability | 25% | 9/10 | 5/10 | 7/10 |
| Team Expertise | 15% | 10/10 | 3/10 | 4/10 |
| Scalability | 10% | 7/10 | 10/10 | 9/10 |
| **Weighted Total** | | **8.5** | **5.8** | **7.0** |

### Recommendation
[Chosen alternative with rationale]

### Implementation Plan
[How will we implement this decision?]

### Rollback Plan
[What if this doesn't work?]
```

---

## 📝 ARCHITECTURE DECISION RECORDS (ADRs)

### 1. ADR Template
**Location**: `/main/Foundation/architecture-decisions/ADR-{NNNN}-{title}.md`

```markdown
# ADR-0001: Use PostgreSQL for Primary Database

**Status**: Accepted  
**Date**: 2026-01-19  
**Deciders**: Systems Architect, Governor  
**Context**: Epic #5 - Agent Marketplace Database

## Context and Problem Statement
We need to choose a primary database for storing agent profiles, customer data, and trial information. The database must support complex queries, transactions, and scale to 1M agents.

## Decision Drivers
- Strong consistency required for trial/payment data
- Complex queries (filtering, aggregation, analytics)
- Team expertise (SQL vs NoSQL)
- Cost efficiency at our scale (1-10k agents currently)
- Integration with Google Cloud

## Considered Options
1. PostgreSQL (Cloud SQL)
2. MongoDB (Atlas)
3. Cloud Firestore

## Decision Outcome
**Chosen option**: PostgreSQL (Cloud SQL)

**Rationale**:
- Best fit for relational data (agents ↔ customers ↔ trials)
- Team already knows SQL (zero learning curve)
- Cloud SQL provides managed service (backups, HA, monitoring)
- jsonb columns provide flexibility for unstructured data
- Cost-effective at our scale (₹8k/month vs ₹12k MongoDB)

### Positive Consequences
- Developers productive immediately (familiar tech)
- ACID transactions ensure data consistency
- Rich query capabilities (JOINs, window functions)
- Excellent tooling (DBeaver, pgAdmin, Alembic migrations)

### Negative Consequences
- Vertical scaling limits (need sharding beyond 10M rows)
- Schema migrations require planning (not schema-less)
- Slightly slower writes than NoSQL (ACID overhead)

## Pros and Cons of Alternatives

### MongoDB
- ✅ Flexible schema, horizontal scaling
- ❌ Weaker consistency, team unfamiliar, more expensive

### Cloud Firestore
- ✅ Serverless, real-time updates
- ❌ Limited queries, expensive at scale, vendor lock-in

## Links
- [Database Comparison Spreadsheet](https://docs.google.com/spreadsheets/d/...)
- [Performance Benchmark Results](./benchmarks/database-comparison.md)
- Related ADRs: ADR-0002 (Redis Caching Strategy)

## Notes
- Revisit if we hit 5M agents or need multi-region deployment
- Consider read replicas if read traffic exceeds 1000 QPS
- Monitor query performance monthly (P95 < 50ms)
```

### 2. ADR Repository Structure
```
/main/Foundation/architecture-decisions/
├── README.md (index of all ADRs)
├── ADR-0001-postgresql-primary-database.md
├── ADR-0002-redis-caching-strategy.md
├── ADR-0003-fastapi-web-framework.md
├── ADR-0004-cloud-run-deployment.md
├── ADR-0005-jwt-authentication.md
├── ADR-0006-terraform-infrastructure.md
├── templates/
│   └── adr-template.md
└── superseded/
    └── ADR-0002-memcached-caching.md (replaced by Redis ADR)
```

### 3. ADR Status Lifecycle
```
Proposed → Accepted → Deprecated → Superseded
          ↓
       Rejected
```

**Status Definitions**:
- **Proposed**: Under consideration, not yet approved
- **Accepted**: Approved and currently in use
- **Deprecated**: Still in use but discouraged for new work
- **Superseded**: Replaced by newer ADR
- **Rejected**: Considered but not chosen

### 4. Living Documentation Process
**ADRs are living documents**:
- Review ADRs quarterly (check if still valid)
- Update ADRs when assumptions change (cost, scale, technology)
- Create new ADR to supersede old one (don't delete history)
- Link related ADRs (dependencies, conflicts)
- Tag ADRs by domain (database, infrastructure, security, frontend)

**Example ADR Review Schedule**:
```markdown
## Q1 2026 ADR Review

### ADR-0001: PostgreSQL
- ✅ Still valid (working well at current scale)
- Current load: 2M agents, 50GB database
- Next review: When we hit 5M agents

### ADR-0003: FastAPI Framework
- ⚠️ Needs update (upgraded from 0.95 to 0.110)
- Performance improved (20% faster response times)
- Add performance benchmark results

### ADR-0007: AWS Deployment
- ❌ SUPERSEDED by ADR-0012 (migrated to Google Cloud)
- Mark as superseded, update links
```

---

## 🎯 SUCCESS METRICS

### Security Architecture
- 100% epics have threat model (STRIDE analysis)
- Zero high-severity security findings in production
- All secrets in Secret Manager (zero hardcoded)
- PCI compliance maintained (payment gateway audit)

### Technical Debt
- Code quality score: ≥9.0/10 (pylint)
- Cyclomatic complexity: <10 (all functions)
- Test coverage: ≥90%
- Quarterly debt sprint completed (3 weeks/quarter)

### Performance Architecture
- P95 latency: <200ms (all APIs)
- Database query performance: P95 <50ms
- Cache hit rate: >80%
- Zero scalability incidents (auto-scaling working)

### Decision Quality
- 100% major decisions have 3+ alternatives evaluated
- All ADRs created within 1 week of decision
- ADRs reviewed quarterly (living documentation)
- Zero "why did we choose this?" questions (documented rationale)

---

**See also**:
- [Coding Agent Enhanced](coding_agent_enhanced_capabilities.md) - Performance optimization
- [Testing Agent Enhanced](testing_agent_enhanced_capabilities.md) - Security testing
- [Deployment Agent Enhanced](deployment_agent_enhanced_capabilities.md) - Infrastructure security
