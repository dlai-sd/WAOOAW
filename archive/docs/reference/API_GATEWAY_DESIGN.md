# API Gateway Architecture - Multi-Gateway Federation

**Version**: 1.1  
**Date**: December 28, 2025  
**Status**: Design Complete  
**Pattern**: API Bank with Central + Domain-Specific Gateways  
**Inspiration**: Netflix Zuul, AWS API Gateway Federation, Kong Gateway

---

## Executive Summary

The **API Gateway** is the entry point for all external traffic to the WAOOAW platform, designed as a **federated API bank** with:
- **Central Gateway**: Platform-wide security, rate limiting, routing
- **Domain Gateways**: Domain-specific security, schema validation, business logic
- **Clear Separation**: Platform API (1 endpoint) vs Domain APIs (Marketing, Education, Sales, Agent Management)

**v1.1 Changes:** Added Common Components Library integration (SecurityLayer for JWT/HMAC validation, ResourceManager for rate limiting, ObservabilityStack for API metrics). See [COMMON_COMPONENTS_LIBRARY_DESIGN.md](COMMON_COMPONENTS_LIBRARY_DESIGN.md).

### Why Multi-Gateway Federation?

| Pattern | Single Gateway | Multi-Gateway Federation |
|---------|---------------|--------------------------|
| **Security** | One policy for all | Domain-specific policies |
| **Scalability** | Bottleneck at scale | Independent scaling |
| **Blast Radius** | One failure = all down | Isolated failures |
| **Complexity** | Simple initially | Higher upfront cost |
| **Team Autonomy** | Centralized control | Domain teams own policies |
| **Best For** | <100 endpoints | >100 endpoints, multi-domain |

**WAOOAW Scale**: 19 agents × 10 endpoints/agent = **190+ endpoints** → Multi-gateway is correct choice

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL CLIENTS                               │
│  (Web App, Mobile App, Partners, Webhooks)                              │
└─────────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    CENTRAL API GATEWAY                                  │
│  • SSL Termination                                                      │
│  • DDoS Protection (Rate Limiting: Global)                              │
│  • Authentication (JWT Validation)                                      │
│  • Request Routing (to domain gateways)                                 │
│  • Audit Logging (all requests)                                         │
│  • Analytics (traffic patterns)                                         │
└─────────────────────────────────────────────────────────────────────────┘
                            ↓
      ┌─────────────┬───────────────┬───────────────┬─────────────────┐
      ↓             ↓               ↓               ↓                 ↓
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────────┐
│Platform │  │Marketing│  │Education│  │  Sales  │  │Agent Mgmt    │
│Gateway  │  │Gateway  │  │Gateway  │  │Gateway  │  │Gateway       │
│         │  │         │  │         │  │         │  │              │
│1 endpoint│ │7 agents │  │7 agents │  │5 agents │  │14 CoEs       │
│         │  │         │  │         │  │         │  │              │
│Separate │  │Domain   │  │Domain   │  │Domain   │  │Internal      │
│Security │  │Security │  │Security │  │Security │  │Security      │
└─────────┘  └─────────┘  └─────────┘  └─────────┘  └──────────────┘
      ↓             ↓               ↓               ↓                 ↓
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────────┐
│Platform │  │Marketing│  │Education│  │  Sales  │  │Orchestration │
│Services │  │Agents   │  │Agents   │  │Agents   │  │Engine        │
└─────────┘  └─────────┘  └─────────┘  └─────────┘  └──────────────┘
```

---

## 1. Central Gateway (Tier 1)

### Responsibilities

**Security**:
- SSL/TLS termination (all external traffic)
- DDoS protection (rate limiting: 1000 req/min global)
- JWT validation (verify signature, expiration)
- IP whitelisting (partner APIs)
- API key validation (external integrations)

**Routing**:
- Path-based routing: `/api/platform/*` → Platform Gateway
- Path-based routing: `/api/marketing/*` → Marketing Gateway
- Path-based routing: `/api/education/*` → Education Gateway
- Path-based routing: `/api/sales/*` → Sales Gateway
- Path-based routing: `/api/agents/*` → Agent Management Gateway

**Observability**:
- Request logging (all traffic)
- Response time tracking (p50, p95, p99)
- Error rate monitoring (5xx, 4xx)
- Audit trail (who accessed what, when)

**NOT Responsible For**:
- ❌ Domain-specific validation (delegated to domain gateways)
- ❌ Business logic (handled by services)
- ❌ Data transformation (handled by services)

### Implementation

**Technology**: Kong Gateway (open source) or Nginx + Lua

**Configuration** (`infrastructure/kong/central-gateway.yaml`):
```yaml
_format_version: "3.0"

services:
  - name: platform-gateway
    url: http://platform-gateway:8000
    routes:
      - name: platform-routes
        paths:
          - /api/platform
        strip_path: false
        
  - name: marketing-gateway
    url: http://marketing-gateway:8001
    routes:
      - name: marketing-routes
        paths:
          - /api/marketing
        strip_path: false
        
  - name: education-gateway
    url: http://education-gateway:8002
    routes:
      - name: education-routes
        paths:
          - /api/education
        strip_path: false
        
  - name: sales-gateway
    url: http://sales-gateway:8003
    routes:
      - name: sales-routes
        paths:
          - /api/sales
        strip_path: false
        
  - name: agents-gateway
    url: http://agents-gateway:8004
    routes:
      - name: agents-routes
        paths:
          - /api/agents
        strip_path: false

plugins:
  - name: rate-limiting
    config:
      minute: 1000
      policy: cluster
      
  - name: jwt
    config:
      key_claim_name: kid
      secret_is_base64: false
      
  - name: prometheus
    config:
      per_consumer: true
      
  - name: correlation-id
    config:
      header_name: X-Request-ID
      generator: uuid
```

**Cost**: $0 (Kong Community) or $50/month (Kong Konnect Starter)

---

## 2. Platform Gateway (Tier 2)

### Purpose

Single endpoint for **platform-wide operations** (health, metrics, admin):
- `/api/platform/health` - System health check
- `/api/platform/metrics` - Platform metrics
- `/api/platform/admin` - Admin operations

**NOT marketplace/agent endpoints** (those are domain gateways)

### Security Policy

**Separate from Domain Gateways**:
- **Authentication**: Admin JWT tokens (separate issuer)
- **Rate Limiting**: 100 req/min (lower than domains)
- **IP Whitelist**: Admin dashboard only (internal network)
- **Audit**: All operations logged to `admin_audit_logs` table

### Implementation

**Technology**: FastAPI (Python)

**File**: `backend/app/gateways/platform_gateway.py`

```python
"""
Platform Gateway - Admin & System Operations

Single endpoint with strict security:
- Admin-only access
- Lower rate limits
- Comprehensive audit logging
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/platform", tags=["platform"])

# Security
security = HTTPBearer()

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin JWT token"""
    token = credentials.credentials
    
    # TODO: Implement JWT validation with admin claim
    # if not jwt.decode(token).get('role') == 'admin':
    #     raise HTTPException(403, "Admin access required")
    
    return token

async def audit_log(request: Request, endpoint: str, status: str):
    """Log all admin operations"""
    logger.info(
        "admin_operation",
        endpoint=endpoint,
        method=request.method,
        ip=request.client.host,
        user_agent=request.headers.get("user-agent"),
        status=status,
        timestamp=datetime.utcnow().isoformat()
    )
    # TODO: Store in admin_audit_logs table

@router.get("/health")
async def health_check(request: Request):
    """
    System health check (public, but rate-limited)
    
    Returns:
        - status: healthy/degraded/down
        - components: database, redis, agents
        - timestamp
    """
    await audit_log(request, "/health", "success")
    
    # TODO: Check all components
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "healthy",
            "redis": "healthy",
            "agents": "healthy"
        }
    }

@router.get("/metrics", dependencies=[Depends(verify_admin_token)])
async def get_metrics(request: Request):
    """
    Platform metrics (admin only)
    
    Returns:
        - requests_per_minute: int
        - active_agents: int
        - error_rate: float
        - p95_latency: float
    """
    await audit_log(request, "/metrics", "success")
    
    # TODO: Fetch from Prometheus/PostgreSQL
    return {
        "requests_per_minute": 450,
        "active_agents": 19,
        "error_rate": 0.02,
        "p95_latency": 120.5
    }

@router.post("/admin/restart-agent", dependencies=[Depends(verify_admin_token)])
async def restart_agent(agent_id: str, request: Request):
    """
    Restart specific agent (admin only)
    
    High-privilege operation, full audit trail
    """
    await audit_log(request, f"/admin/restart-agent/{agent_id}", "initiated")
    
    # TODO: Send restart command to agent via message bus
    
    await audit_log(request, f"/admin/restart-agent/{agent_id}", "success")
    
    return {"status": "restarting", "agent_id": agent_id}
```

**Security Config** (`infrastructure/kong/platform-gateway.yaml`):
```yaml
services:
  - name: platform-service
    url: http://backend:8000
    
    routes:
      - name: platform-health
        paths:
          - /api/platform/health
        strip_path: false
        plugins:
          - name: rate-limiting
            config:
              minute: 100  # Lower than domains
              
      - name: platform-admin
        paths:
          - /api/platform/admin
        strip_path: false
        plugins:
          - name: jwt
            config:
              claims_to_verify:
                - role: admin  # Must have admin role
          - name: rate-limiting
            config:
              minute: 50  # Even stricter
          - name: ip-restriction
            config:
              allow:
                - 10.0.0.0/8  # Internal network only
```

---

## 3. Domain Gateways (Tier 2)

### Marketing Gateway

**Endpoints** (7 agents):
- `/api/marketing/content` - Content Marketing agent
- `/api/marketing/social` - Social Media agent
- `/api/marketing/seo` - SEO agent
- `/api/marketing/email` - Email Marketing agent
- `/api/marketing/ppc` - PPC Advertising agent
- `/api/marketing/brand` - Brand Strategy agent
- `/api/marketing/influencer` - Influencer Marketing agent

**Domain-Specific Security**:
- **Authentication**: Customer JWT (marketing scope)
- **Rate Limiting**: 500 req/min (business tier), 100 req/min (free tier)
- **Schema Validation**: Marketing request schema (campaign, content, keywords)
- **Business Rules**: 
  - Free tier: 10 requests/day
  - Business tier: Unlimited
  - Enterprise tier: Dedicated rate limit

**Implementation**: FastAPI router

```python
# backend/app/gateways/marketing_gateway.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/marketing", tags=["marketing"])

class ContentRequest(BaseModel):
    """Marketing content request schema"""
    topic: str
    tone: str  # professional, casual, technical
    length: int  # words
    keywords: list[str]

@router.post("/content")
async def request_content(
    req: ContentRequest,
    customer: dict = Depends(verify_customer_token)
):
    """
    Request content from Content Marketing agent
    
    Domain-specific validation:
    - topic: non-empty, <200 chars
    - tone: enum validation
    - length: 100-5000 words
    - keywords: max 10
    """
    # Validate business rules
    if customer['tier'] == 'free' and customer['requests_today'] >= 10:
        raise HTTPException(429, "Daily limit reached (upgrade to Business)")
    
    # Forward to agent orchestration
    # TODO: Send to orchestration engine
    
    return {"status": "processing", "request_id": "req_123"}
```

### Education Gateway

**Endpoints** (7 agents):
- `/api/education/math` - Math Tutor (JEE/NEET specialist)
- `/api/education/science` - Science Tutor (CBSE specialist)
- `/api/education/english` - English Language
- `/api/education/test-prep` - Test Prep
- `/api/education/career` - Career Counseling
- `/api/education/study` - Study Planning
- `/api/education/homework` - Homework Help

**Domain-Specific Security**:
- **Authentication**: Student/Parent JWT (education scope)
- **Rate Limiting**: 1000 req/min (students have high query volume)
- **Schema Validation**: Education request schema (subject, grade, question)
- **Business Rules**:
  - Age verification (COPPA compliance for <13)
  - Parent consent required for <13
  - Content filtering (no exam leaks, plagiarism)

### Sales Gateway

**Endpoints** (5 agents):
- `/api/sales/sdr` - SDR Agent (B2B SaaS specialist)
- `/api/sales/ae` - Account Executive
- `/api/sales/enablement` - Sales Enablement
- `/api/sales/crm` - CRM Management
- `/api/sales/leads` - Lead Generation

**Domain-Specific Security**:
- **Authentication**: Company JWT (sales scope)
- **Rate Limiting**: 200 req/min (B2B has lower volume, higher value)
- **Schema Validation**: Sales request schema (lead, opportunity, account)
- **Business Rules**:
  - PII protection (GDPR compliance)
  - CRM integration validation
  - Lead scoring constraints

### Agent Management Gateway (Internal)

**Endpoints** (14 CoEs):
- `/api/agents/orchestration` - Workflow engine
- `/api/agents/coordinator` - CoE coordinators
- `/api/agents/vision` - WowVision Prime
- ... (internal agent communication)

**Security**:
- **Authentication**: Agent-to-agent HMAC signatures (NOT JWT)
- **Rate Limiting**: 10,000 req/min (high internal traffic)
- **Schema Validation**: Message bus schema
- **Business Rules**: NONE (internal only, no customer access)

**Access**: Internal network only (no external exposure)

---

## 4. Security Architecture

### Multi-Layer Security Model

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: Central Gateway                            │
│ • SSL/TLS termination                               │
│ • DDoS protection (global rate limit)              │
│ • JWT validation (signature, expiration)           │
│ • IP whitelisting (partners)                        │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ Layer 2: Domain Gateway                             │
│ • Domain-specific rate limits                       │
│ • Schema validation (per domain)                    │
│ • Business rules (tier limits, COPPA, GDPR)        │
│ • Audit logging (domain-specific)                   │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ Layer 3: Service                                    │
│ • Business logic validation                         │
│ • Database access control                           │
│ • Multi-tenant isolation                            │
└─────────────────────────────────────────────────────┘
```

### Authentication Matrix

| Gateway | Auth Method | Token Type | Issuer | Expiry | Scope |
|---------|------------|------------|--------|--------|-------|
| **Central** | JWT | Access Token | Auth0/Keycloak | 1 hour | Platform-wide |
| **Platform** | JWT | Admin Token | Auth0/Keycloak | 1 hour | Admin-only |
| **Marketing** | JWT | Customer Token | Auth0/Keycloak | 1 hour | marketing:* |
| **Education** | JWT | Student Token | Auth0/Keycloak | 1 hour | education:* |
| **Sales** | JWT | Company Token | Auth0/Keycloak | 1 hour | sales:* |
| **Agent Mgmt** | HMAC | N/A (signature) | Agent secrets | N/A | Internal |

### Rate Limiting Strategy

| Gateway | Free Tier | Business Tier | Enterprise | Internal |
|---------|-----------|---------------|------------|----------|
| **Central** | 1000/min | 5000/min | Custom | 100K/min |
| **Platform** | N/A (admin only) | N/A | N/A | 100/min |
| **Marketing** | 100/min (10/day) | 500/min | Custom | N/A |
| **Education** | 200/min | 1000/min | Custom | N/A |
| **Sales** | 50/min | 200/min | Custom | N/A |
| **Agent Mgmt** | N/A (internal) | N/A | N/A | 10K/min |

**Burst Allowance**: 2x sustained rate for 10 seconds

---

## 5. Implementation Roadmap

### Phase 1: Central Gateway (Week 13-14)

**Goal**: Single entry point with basic routing

**Deliverables**:
- [ ] Kong Gateway deployed (Docker Compose)
- [ ] SSL/TLS termination
- [ ] Path-based routing to backend
- [ ] Global rate limiting (1000 req/min)
- [ ] JWT validation (signature only)
- [ ] Health check endpoint

**Files**:
- NEW: `infrastructure/kong/docker-compose.yml`
- NEW: `infrastructure/kong/central-gateway.yaml`
- NEW: `infrastructure/kong/README.md`

**Testing**:
- [ ] 1000 req/min load test
- [ ] Invalid JWT rejection
- [ ] SSL certificate validation

---

### Phase 2: Platform Gateway (Week 15-16)

**Goal**: Admin operations with strict security

**Deliverables**:
- [ ] Platform gateway (FastAPI router)
- [ ] Admin JWT validation (role claim)
- [ ] IP whitelisting
- [ ] Audit logging to database
- [ ] Health/metrics endpoints
- [ ] Admin operations (restart agent, view logs)

**Files**:
- NEW: `backend/app/gateways/platform_gateway.py`
- NEW: `backend/app/gateways/security.py`
- NEW: `backend/app/models/admin_audit_log.py`
- NEW: `backend/database/migrations/020_admin_audit_logs.sql`

**Testing**:
- [ ] Admin role verification
- [ ] IP whitelist enforcement
- [ ] Audit log creation

---

### Phase 3: Domain Gateways (Week 17-20)

**Goal**: Marketing, Education, Sales gateways with domain-specific rules

**Deliverables**:
- [ ] Marketing gateway (FastAPI router)
- [ ] Education gateway (FastAPI router)
- [ ] Sales gateway (FastAPI router)
- [ ] Schema validation (Pydantic models)
- [ ] Tier-based rate limiting
- [ ] Business rules (COPPA, GDPR, tier limits)

**Files**:
- NEW: `backend/app/gateways/marketing_gateway.py`
- NEW: `backend/app/gateways/education_gateway.py`
- NEW: `backend/app/gateways/sales_gateway.py`
- NEW: `backend/app/schemas/marketing_schemas.py`
- NEW: `backend/app/schemas/education_schemas.py`
- NEW: `backend/app/schemas/sales_schemas.py`

**Testing**:
- [ ] Schema validation (valid/invalid requests)
- [ ] Tier limit enforcement
- [ ] COPPA age verification

---

### Phase 4: Agent Management Gateway (Week 21-22)

**Goal**: Internal agent communication with HMAC security

**Deliverables**:
- [ ] Agent management gateway (internal only)
- [ ] HMAC signature validation
- [ ] High rate limits (10K req/min)
- [ ] Message bus integration
- [ ] Network isolation (no external access)

**Files**:
- NEW: `backend/app/gateways/agent_gateway.py`
- EDIT: `waooaw/messaging/message_bus.py` (integrate with gateway)
- NEW: `infrastructure/kong/agent-gateway.yaml`

**Testing**:
- [ ] HMAC signature verification
- [ ] 10K req/min load test
- [ ] External access blocked

---

### Phase 5: Observability & Monitoring (Week 23-24)

**Goal**: Full visibility into gateway performance

**Deliverables**:
- [ ] Prometheus metrics (Kong plugin)
- [ ] Grafana dashboards (requests, latency, errors)
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Alerting (rate limit violations, errors)
- [ ] Cost tracking (by domain, by tier)

**Files**:
- NEW: `infrastructure/grafana/gateway-dashboard.json`
- NEW: `infrastructure/alerting/gateway-alerts.yaml`
- EDIT: `infrastructure/kong/central-gateway.yaml` (add prometheus plugin)

**Testing**:
- [ ] Metrics collection
- [ ] Dashboard visualization
- [ ] Alert triggering

---

## 6. Cost Analysis

### Infrastructure Costs

| Component | Technology | Tier | Cost |
|-----------|-----------|------|------|
| **Central Gateway** | Kong Community | Free | $0 |
| **Domain Gateways** | FastAPI | Free | $0 |
| **Load Balancer** | Nginx | Free | $0 |
| **SSL Certificates** | Let's Encrypt | Free | $0 |
| **Monitoring** | Prometheus/Grafana | Self-hosted | $0 |
| **Total (Phase 1)** | - | - | **$0/month** |

### Upgrade Path

**When traffic > 100K req/month**:
- Kong Konnect Starter: $50/month (managed, SLA, support)
- OR AWS API Gateway: $3.50/million requests

**When need advanced features**:
- Kong Enterprise: $3,000/year (rate limiting++, auth plugins, dev portal)
- OR AWS API Gateway + WAF: $5/month + usage

**Recommendation**: Start with Kong Community ($0), upgrade when revenue justifies ($10K+ MRR)

---

## 7. Security Best Practices

### JWT Token Management

**Token Structure**:
```json
{
  "sub": "user_12345",
  "email": "user@example.com",
  "role": "customer",
  "tier": "business",
  "scopes": ["marketing:read", "marketing:write"],
  "iss": "https://auth.waooaw.ai",
  "aud": "https://api.waooaw.ai",
  "exp": 1735401600,
  "iat": 1735398000
}
```

**Validation**:
- ✅ Signature (RS256 or HS256)
- ✅ Expiration (1 hour)
- ✅ Issuer (auth.waooaw.ai)
- ✅ Audience (api.waooaw.ai)
- ✅ Claims (role, tier, scopes)

**Refresh Token Flow**:
1. Access token expires (1 hour)
2. Client sends refresh token (httpOnly cookie)
3. Auth service issues new access token
4. Client retries original request

### API Key Management (Partners)

**Format**: `waw_live_sk_1234567890abcdef` (32 chars)

**Storage**: 
- Hashed (SHA256) in database
- Never exposed in logs
- Rotated every 90 days

**Scope**: Partner-specific (e.g., `partner:acme:marketing:read`)

---

## 8. Testing Strategy

### Load Testing

**Tool**: Locust (Python)

**Scenarios**:
1. **Sustained Load**: 1000 req/min for 1 hour (p95 < 200ms)
2. **Spike Test**: 5000 req/min for 5 minutes (p95 < 500ms)
3. **Stress Test**: Increase until failure (find breaking point)

**Example** (`tests/load/test_gateway.py`):
```python
from locust import HttpUser, task, between

class MarketingUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def request_content(self):
        self.client.post("/api/marketing/content", json={
            "topic": "AI agents",
            "tone": "professional",
            "length": 500,
            "keywords": ["AI", "automation"]
        }, headers={"Authorization": f"Bearer {self.token}"})
```

**Run**:
```bash
locust -f tests/load/test_gateway.py --host=https://api.waooaw.ai --users=1000 --spawn-rate=100
```

### Security Testing

**Tool**: OWASP ZAP

**Tests**:
- [ ] SQL injection (schema validation)
- [ ] JWT tampering (signature validation)
- [ ] Rate limit bypass (429 errors)
- [ ] CORS misconfiguration (Origin header)
- [ ] API key leakage (logs, error messages)

---

## 9. Migration Strategy

### From Current (v0.2.x) to Multi-Gateway (v0.8)

**Current State**:
- Single FastAPI app (`backend/app/main.py`)
- No gateway (direct backend access)
- Basic CORS, health check

**Phase 1: Add Central Gateway** (no breaking changes):
1. Deploy Kong in front of existing backend
2. Route all traffic: `/*` → `backend:8000`
3. Enable SSL/TLS
4. Enable JWT validation (optional, default allow)
5. Monitor for 1 week

**Phase 2: Add Platform Gateway** (admin only, isolated):
1. Create `/api/platform` routes
2. Restrict to admin JWT
3. No impact on existing endpoints

**Phase 3: Add Domain Gateways** (gradual rollout):
1. Create `/api/marketing` routes (new, no migration)
2. Create `/api/education` routes (new)
3. Create `/api/sales` routes (new)
4. Keep existing `/api/agents` for backward compatibility
5. Deprecate `/api/agents` in v1.0

**Zero Downtime**: Use blue-green deployment

---

## 10. Documentation & Support

### API Documentation

**Tool**: OpenAPI/Swagger (auto-generated from FastAPI)

**Endpoints**:
- `/api/docs` - Interactive Swagger UI
- `/api/redoc` - ReDoc documentation
- `/api/openapi.json` - OpenAPI schema

**Per-Domain Docs**:
- `/api/marketing/docs` - Marketing API docs
- `/api/education/docs` - Education API docs
- `/api/sales/docs` - Sales API docs

### Developer Portal

**Features**:
- API key management
- Usage analytics
- Code examples (Python, JavaScript, cURL)
- Webhook configuration
- Rate limit status

**Technology**: Kong Developer Portal OR custom React app

---

## Summary

**Multi-Gateway Federation Benefits**:
1. ✅ **Security Isolation**: Platform vs Domain vs Internal
2. ✅ **Scalability**: Independent scaling per domain
3. ✅ **Blast Radius**: One domain failure doesn't affect others
4. ✅ **Team Autonomy**: Domain teams own security policies
5. ✅ **Cost**: $0 for Phase 1-4 (open source)

**Implementation Timeline**:
- Week 13-14: Central Gateway
- Week 15-16: Platform Gateway
- Week 17-20: Domain Gateways (Marketing, Education, Sales)
- Week 21-22: Agent Management Gateway
- Week 23-24: Observability

**Total Effort**: 12 weeks (Phase 2: Marketplace Go-Live)

**Next Steps**:
1. Review and approve this design
2. Set up Kong Gateway (Week 13)
3. Implement Platform Gateway (Week 15)
4. Roll out domain gateways (Week 17-20)

---

**Version**: 1.0  
**Last Updated**: December 28, 2025  
**Author**: GitHub Copilot + dlai-sd architectural guidance  
**Status**: Ready for Review
