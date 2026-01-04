# Target GCP Architecture - 5 Domain Setup

**Version:** 1.1  
**Status:** Design Complete - Implementation Pending  
**Region:** asia-south1 (Mumbai, India)  
**Multi-Zone Strategy:** Designed for HA, deployed single-zone initially  
**Policy Compliance:** Aligned with [POLICY-TECH-001](/policy/TECH_STACK_SELECTION_POLICY.md)  
**Estimated Cost (Phase 1):** $85-130/month (within $150 policy limit)

---

## 1. Architecture Overview

### 1.1 Domain Layout

```
                                GoDaddy DNS
                                     ↓
                         www.waooaw.com (A: 35.190.6.91)
                                     ↓
                         ┌──────────────────────────────────┐
                         │  GCP Global Load Balancer        │
                         │  IP: 35.190.6.91                 │
                         │  Region: asia-south1 (Mumbai)    │
                         │  SSL: Multi-domain cert          │
                         │  Multi-Zone: Designed, not active│
                         └──────────────────────────────────┘
                                     ↓
        ┌────────────┬───────────┬──────────┬──────────┬────────────┐
        │            │           │          │          │            │
   www.waooaw   pp.waooaw   dp.waooaw  yk.waooaw  api.waooaw
      .com         .com        .com       .com       .com
        │            │           │          │          │
        ↓            ↓           ↓          ↓          ↓
   ┌────────┐  ┌─────────┐ ┌─────────┐ ┌──────┐  ┌─────────┐
   │ React  │  │ Reflex  │ │ Reflex  │ │React │  │FastAPI  │
   │  SPA   │  │Platform │ │  Dev    │ │ Cust │  │Backend  │
   │Static  │  │ Portal  │ │ Portal  │ │Portal│  │  API    │
   └────────┘  └─────────┘ └─────────┘ └──────┘  └─────────┘
   Cloud Run   Cloud Run   Cloud Run   Cloud Run  Cloud Run
```

---

## 2. Service Specifications

### 2.1 www.waooaw.com - Customer Marketplace

**Purpose:** Public-facing marketing and agent marketplace  
**Technology:** React SPA (static build served via Nginx)  
**Policy Rationale:** Customer-facing requires fast load, SEO optimization, low cost

| Spec | Value | Rationale |
|------|-------|-----------|
| **Service Name** | waooaw-marketplace | Clear, non-staging name |
| **Region** | asia-south1 | Mumbai, India (low latency) |
| **Zone Strategy** | Single zone (a), multi-zone ready | Cost optimization |
| **Container** | Nginx + React static files | Fastest cold start, cheapest |
| **Memory** | 256 Mi | Static content, minimal needs |
| **CPU** | 1 vCPU | Sufficient for Nginx |
| **Min Instances** | 0 (Phase 1), 1 (Phase 2) | Scale to zero initially |
| **Max Instances** | 10 | Handle traffic spikes |
| **Port** | 8080 | Standard non-root port |
| **Ingress** | All | Public access |
| **Cold Start Target** | <500ms | Fast user experience |
| **Monthly Cost** | $6-10 (Phase 1) | Policy compliant |

**Environment Variables:**
```yaml
BACKEND_API_URL: https://api.waooaw.com
OAUTH_REDIRECT: https://www.waooaw.com/auth/callback
```

**Build Process:**
```bash
cd frontend/
npm run build              # Vite/React build
docker build -f Dockerfile.marketplace
```

---

### 2.2 pp.waooaw.com - Platform Portal

**Purpose:** Internal operator dashboard (Platform CoE)  
**Technology:** Reflex (Python → React)  
**Policy Rationale:** Internal tool, development velocity prioritized over cost

| Spec | Value | Rationale |
|------|-------|-----------|
| **Service Name** | waooaw-platform-portal | Rename from frontend-staging |
| **Region** | asia-south1 | Mumbai, India |
| **Zone Strategy** | Single zone (a) initially | Internal tool, cost priority |
| **Container** | Reflex app (Python + Node.js runtime) | Existing implementation |
| **Memory** | 2 Gi | Reflex compilation needs |
| **CPU** | 2 vCPU | Real-time WebSocket support |
| **Min Instances** | 0 (all phases) | Scale to zero, internal tool |
| **Max Instances** | 5 | Internal use, limited concurrency |
| **Port** | 3000 | Reflex default |
| **Ingress** | All | OAuth-protected |
| **Cold Start Target** | <3s | Acceptable for internal tool |
| **Monthly Cost** | $18-25 (all phases) | Policy compliant |

**Environment Variables:**
```yaml
ENV: production
BACKEND_URL: https://api.waooaw.com
REDIS_URL: <redis-connection-string>
OAUTH_CLIENT_ID: <from-secret>
```

**Notes:**
- Reuse existing `waooaw-frontend-staging` service, rename and remap
- WebSocket support required for real-time dashboard updates

---

### 2.3 dp.waooaw.com - Development Portal

**Purpose:** Internal development team dashboard  
**Technology:** Reflex (Python → React)  
**Policy Rationale:** Clone of Platform Portal, internal use only

| Spec | Value | Rationale |
|------|-------|-----------|
| **Service Name** | waooaw-dev-portal | New service |
| **Region** | asia-south1 | Mumbai, India |
| **Zone Strategy** | Single zone (a) only | Internal tool, minimal HA |
| **Container** | Reflex app (cloned from pp) | Code reuse |
| **Memory** | 1 Gi | Lighter than pp (fewer features) |
| **CPU** | 1 vCPU | Lower concurrency needs |
| **Min Instances** | 0 (all phases) | Always scale to zero |
| **Max Instances** | 3 | Small dev team |
| **Port** | 3000 | Reflex default |
| **Ingress** | All | OAuth-protected |
| **Cold Start Target** | <3s | Acceptable for internal |
| **Monthly Cost** | $15-20 (all phases) | Policy compliant |

**Environment Variables:**
```yaml
ENV: production
BACKEND_URL: https://api.waooaw.com
PORTAL_TYPE: development
OAUTH_CLIENT_ID: <from-secret>
```

**Implementation:**
```bash
# Clone Platform Portal codebase
cp -r PlatformPortal/ DevPortal/
# Customize branding, features
# Deploy separately
```

---

### 2.4 yk.waooaw.com - Customer Portal (YK Customer)

**Purpose:** Customer-specific agent dashboard  
**Technology:** React SPA (lightweight, customer-branded)  
**Policy Rationale:** Customer-facing, performance matters

| Spec | Value | Rationale |
|------|-------|-----------|
| **Service Name** | waooaw-customer-yk | Customer-specific instance |
| **Region** | asia-south1 | Mumbai, India |
| **Zone Strategy** | Single zone (a), multi-zone ready | Cost optimization |
| **Container** | React SPA (static build) | Fast, cheap |
| **Memory** | 256 Mi | Static content |
| **CPU** | 1 vCPU | Minimal needs |
| **Min Instances** | 0 (Phase 1-2), 1 (Phase 3 if needed) | Scale to zero initially |
| **Max Instances** | 5 | Single customer workload |
| **Port** | 8080 | Standard |
| **Ingress** | All | Customer-facing |
| **Cold Start Target** | <500ms | Good UX |
| **Monthly Cost** | $6-10 (all phases) | Policy compliant |

**Environment Variables:**
```yaml
BACKEND_API_URL: https://api.waooaw.com
CUSTOMER_ID: yk
BRANDING_THEME: custom-yk
OAUTH_REDIRECT: https://yk.waooaw.com/auth/callback
```

**Future Scaling:**
- Multi-tenant: Single service, customer ID routing
- Per-customer: Separate Cloud Run service per customer
- Hybrid: Shared service, customer-specific config

---

### 2.5 api.waooaw.com - Backend API

**Purpose:** Unified backend for all frontend applications  
**Technology:** FastAPI (Python)  
**Policy Rationale:** Existing investment, async performance

| Spec | Value | Rationale |
|------|-------|-----------|
| **Service Name** | waooaw-api | Rename from backend-staging |
| **Region** | asia-south1 | Mumbai, India |
| **Zone Strategy** | Single zone (a), multi-zone in Phase 3 | Critical service |
| **Container** | FastAPI app | Existing implementation |
| **Memory** | 1 Gi | API workload |
| **CPU** | 1 vCPU | Async handles concurrency |
| **Min Instances** | 0 (Phase 1), 1 (Phase 2-3) | Warm in Phase 2+ |
| **Max Instances** | 10 | Handle traffic from all frontends |
| **Port** | 8000 | FastAPI default |
| **Ingress** | All | Public API |
| **Cold Start Target** | <2s | Acceptable for API |
| **Monthly Cost** | $12-15 (Phase 1), $34-43 (Phase 2+) | Policy compliant |

**Environment Variables:**
```yaml
ENV: production
FRONTEND_URL: https://www.waooaw.com
GOOGLE_REDIRECT_URI: https://api.waooaw.com/auth/callback
GOOGLE_CLIENT_ID: <from-secret>
GOOGLE_CLIENT_SECRET: <from-secret>
CORS_ORIGINS: https://www.waooaw.com,https://pp.waooaw.com,https://dp.waooaw.com,https://yk.waooaw.com
```

**Notes:**
- Reuse existing `waooaw-backend-staging`, rename
- Update CORS to allow all 4 frontend domains

---

## 3. Load Balancer Configuration

### 3.1 URL Map Structure

```yaml
name: waooaw-lb
defaultService: waooaw-marketplace  # Changed from frontend

hostRules:
  - hosts:
      - www.waooaw.com
    pathMatcher: marketplace-matcher
    
  - hosts:
      - pp.waooaw.com
    pathMatcher: platform-portal-matcher
    
  - hosts:
      - dp.waooaw.com
    pathMatcher: dev-portal-matcher
    
  - hosts:
      - yk.waooaw.com
    pathMatcher: customer-yk-matcher
    
  - hosts:
      - api.waooaw.com
    pathMatcher: api-matcher

pathMatchers:
  # www.waooaw.com routes
  - name: marketplace-matcher
    defaultService: waooaw-marketplace
    
  # pp.waooaw.com routes
  - name: platform-portal-matcher
    defaultService: waooaw-platform-portal
    
  # dp.waooaw.com routes
  - name: dev-portal-matcher
    defaultService: waooaw-dev-portal
    
  # yk.waooaw.com routes
  - name: customer-yk-matcher
    defaultService: waooaw-customer-yk
    
  # api.waooaw.com routes
  - name: api-matcher
    defaultService: waooaw-api
```

### 3.2 Backend Services

Each service needs a Network Endpoint Group (NEG) pointing to Cloud Run:

```yaml
backendServices:
  - name: waooaw-marketplace
    backends:
      - group: waooaw-marketplace-neg (Cloud Run NEG)
    
  - name: waooaw-platform-portal
    backends:
      - group: waooaw-platform-portal-neg
    
  - name: waooaw-dev-portal
    backends:
      - group: waooaw-dev-portal-neg
    
  - name: waooaw-customer-yk
    backends:
      - group: waooaw-customer-yk-neg
    
  - name: waooaw-api
    backends:
      - group: waooaw-api-neg
```

---

## 4. SSL Certificate Configuration

### 4.1 Multi-Domain Certificate

**Certificate Name:** `waooaw-multi-domain-cert`  
**Type:** Google-managed  
**Domains:**
```
www.waooaw.com
pp.waooaw.com
dp.waooaw.com
yk.waooaw.com
api.waooaw.com
```

**Provisioning Time:** 15-60 minutes after domain verification  
**Auto-renewal:** Enabled (90 days before expiry)

### 4.2 Domain Verification Requirements

Each subdomain must be verified in GCP:
1. DNS A record pointing to 35.190.6.91
2. Load balancer configured with host rule
3. SSL certificate provisioning initiated
4. Wait for ACTIVE status

---

## 5. DNS Configuration (GoDaddy)

**Domain:** waooaw.com  
**Registrar:** GoDaddy

### 5.1 Required DNS Records

| Type | Name | Value | TTL | Status |
|------|------|-------|-----|--------|
| A | @ (root) | 35.190.6.91 | 600 | ❓ Check |
| A | www | 35.190.6.91 | 600 | ✅ Configured |
| A | pp | 35.190.6.91 | 600 | ❌ Add |
| A | dp | 35.190.6.91 | 600 | ❌ Add |
| A | yk | 35.190.6.91 | 600 | ❌ Add |
| A | api | 35.190.6.91 | 600 | ❌ Add |

**Note:** All subdomains point to same load balancer IP. Routing handled by URL map.

---

## 6. OAuth Configuration

### 6.1 Google Cloud Console Setup

**OAuth Consent Screen:**
- App name: WAOOAW Platform
- Support email: yogeshkhandge@gmail.com
- Authorized domains: waooaw.com
- Scopes: openid, email, profile

**OAuth Client ID:**
- Application type: Web application
- Name: WAOOAW Production

**Authorized Redirect URIs:**
```
https://api.waooaw.com/auth/callback         # Backend OAuth handler
https://www.waooaw.com/auth/callback         # Customer marketplace
https://pp.waooaw.com/auth/callback          # Platform portal
https://dp.waooaw.com/auth/callback          # Dev portal
https://yk.waooaw.com/auth/callback          # Customer portal
```

### 6.2 OAuth Flow

```
User clicks "Login" on any frontend
    ↓
Frontend redirects to: api.waooaw.com/auth/login
    ↓
Backend redirects to: Google OAuth consent
    ↓
User approves
    ↓
Google redirects to: api.waooaw.com/auth/callback?code=...
    ↓
Backend exchanges code for token
    ↓
Backend redirects to: <origin-frontend>/auth/callback?token=...
    ↓
Frontend stores token, redirects to dashboard
```

**Key Point:** Backend determines origin and redirects to correct frontend

---

## 7. Cost Projection - 3 Phase Strategy

### 7.1 Phase 1: Single Zone, Scale-to-Zero (Month 1-3)

**Deployment:** asia-south1-a only, min instances = 0

| Service | Requests | Memory | Runtime | Zone | Cost |
|---------|----------|--------|---------|------|------|
| www.waooaw.com | 50K | 256Mi | 12h | a | $6-8 |
| pp.waooaw.com | 20K | 2Gi | 8h | a | $18-22 |
| dp.waooaw.com | 10K | 1Gi | 5h | a | $15-18 |
| yk.waooaw.com | 10K | 256Mi | 5h | a | $6-8 |
| api.waooaw.com | 80K | 1Gi | 20h | a | $12-15 |
| Load Balancer | 170K | - | - | Global | $28-35 |
| Artifact Registry | 10GB | - | - | asia-south1 | $1 |
| **Total** | | | | | **$86-127/month** |

**Within policy limit:** ✅ Yes (<$150/month)  
**Trigger for Phase 2:** Traffic >50K req/day OR Revenue >$2K/month

### 7.2 Phase 2: Warm Instances, Single Zone (Month 4-6)

**Deployment:** asia-south1-a only, min instances for customer-facing

| Service | Min Instances | Zone | Additional Cost | Total Cost |
|---------|--------------|------|----------------|------------|
| www.waooaw.com | 1 | a | +$17-22 | $23-30 |
| pp.waooaw.com | 0 | a | $0 | $18-22 |
| dp.waooaw.com | 0 | a | $0 | $15-18 |
| yk.waooaw.com | 0 | a | $0 | $6-8 |
| api.waooaw.com | 1 | a | +$22-28 | $34-43 |
| Load Balancer | - | Global | $0 | $28-35 |
| Artifact Registry | - | asia-south1 | $0 | $1 |
| **Total** | | | **+$39-50** | **$125-177/month** |

**Within policy limit:** ⚠️ Yes, but close to $150 (borderline)  
**Benefit:** No cold starts for www and api  
**Trigger for Phase 3:** Customer SLA requirements OR Revenue >$5K/month

### 7.3 Phase 3: Multi-Zone HA (Month 7+)

**Deployment:** asia-south1 zones a + b, min 1 instance per zone for critical services

| Service | Min Instances/Zone | Zones | Total Instances | Cost |
|---------|-------------------|-------|----------------|------|
| www.waooaw.com | 1 | a, b | 2 | $34-44 |
| pp.waooaw.com | 0 | a | 0-5 | $18-25 |
| dp.waooaw.com | 0 | a | 0-3 | $15-20 |
| yk.waooaw.com | 0 | a | 0-5 | $6-10 |
| api.waooaw.com | 1 | a, b | 2 | $44-56 |
| Load Balancer | - | Global | - | $28-35 |
| Artifact Registry | - | asia-south1 | - | $1 |
| **Total** | | | | **$145-190/month** |

**Within policy limit:** ❌ Exceeds $150 at high end  
**Requires:** CTO approval per policy for >$150/month  
**Benefit:** Zone-level failover, <10s recovery time  
**RTO:** 5-10 seconds (automatic Cloud Run failover)

### 7.4 Phase Comparison Summary

| Phase | Zones | HA Level | Downtime Risk | Monthly Cost | Policy Status |
|-------|-------|----------|--------------|--------------|---------------|
| **Phase 1** | 1 (a) | None | Zone failure = 5-10s recovery | $86-127 | ✅ Compliant |
| **Phase 2** | 1 (a) | Warm instances | No cold starts, zone failure = 5-10s | $125-177 | ⚠️ Borderline |
| **Phase 3** | 2 (a,b) | Multi-zone | Zone failure = instant failover | $145-190 | ❌ Needs approval |

### 7.5 Traffic Scaling Projections

| Traffic Level | Requests/Month | Phase 1 Cost | Phase 2 Cost | Phase 3 Cost |
|---------------|----------------|-------------|-------------|-------------|
| Startup | 100K | $86-127 | $125-177 | $145-190 |
| Growth | 1M | $150-250 | $210-320 | $280-400 |
| Scale | 10M | $500-800 | $700-1000 | $900-1300 |

---

## 8. Security Configuration

### 8.1 IAM Roles

| Service | Service Account | Role |
|---------|----------------|------|
| All Cloud Run services | Default compute SA | Cloud Run Invoker |
| Cloud Build | Cloud Build SA | Editor, Secret Accessor |
| Load Balancer | N/A (built-in) | - |

### 8.2 Secret Access

Services accessing secrets:
- waooaw-platform-portal → google-client-id
- waooaw-dev-portal → google-client-id
- waooaw-api → google-client-id, google-client-secret

**IAM Binding:**
```bash
gcloud secrets add-iam-policy-binding google-client-id \
  --member=serviceAccount:<cloud-run-sa> \
  --role=roles/secretmanager.secretAccessor
```

---

## 9. Monitoring & Alerts

### 9.1 Cost Alerts

**Budget:** $150/month (policy limit)  
**Alert Thresholds:**
- 50% ($75) → Email notification
- 80% ($120) → Slack alert + email
- 100% ($150) → Urgent review required

### 9.2 Uptime Checks

| Service | Check URL | Interval | Alerting |
|---------|-----------|----------|----------|
| Customer Site | https://www.waooaw.com | 5 min | Email + Slack |
| API Health | https://api.waooaw.com/health | 1 min | Email + Slack |
| Platform Portal | https://pp.waooaw.com | 10 min | Email only |

### 9.3 Performance Targets

| Metric | Target | P95 Threshold | Alerting |
|--------|--------|---------------|----------|
| API Latency | <500ms | <1s | Email if >1s for 5min |
| Error Rate | <1% | <5% | Slack if >5% |
| Cold Starts | <3s | <5s | Track only |

---

## 10. Implementation Checklist

### Phase 1: DNS & SSL (Day 1)
- [ ] Add DNS A records for pp, dp, yk, api subdomains
- [ ] Create multi-domain SSL certificate
- [ ] Wait for certificate ACTIVE status
- [ ] Verify all 5 domains resolve to 35.190.6.91

### Phase 2: Load Balancer (Day 1-2)
- [ ] Update URL map with 5 host rules
- [ ] Create 5 backend services (1 per domain)
- [ ] Create Network Endpoint Groups for each service
- [ ] Update HTTPS proxy with new SSL cert
- [ ] Test routing: curl -H "Host: <domain>" http://35.190.6.91

### Phase 3: Cloud Run Services (Day 2-3)
- [ ] Build React marketplace app (www)
- [ ] Rename frontend-staging → platform-portal (pp)
- [ ] Clone and deploy dev-portal (dp)
- [ ] Build customer portal template (yk)
- [ ] Rename backend-staging → api
- [ ] Update environment variables for all services

### Phase 4: OAuth (Day 3-4)
- [ ] Add 5 redirect URIs in Google Cloud Console
- [ ] Update backend OAuth handler (detect origin)
- [ ] Fix frontend OAuth flows (remove hardcoded URLs)
- [ ] Test login flow on all 5 domains
- [ ] Verify token exchange and storage

### Phase 5: Testing (Day 4-5)
- [ ] End-to-end test: www → api → OAuth → dashboard
- [ ] Cross-domain session test
- [ ] Performance test (cold start, latency)
- [ ] Cost monitoring verification
- [ ] SSL certificate validation

### Phase 6: Documentation (Day 5)
- [ ] Deployment runbooks
- [ ] Troubleshooting guides
- [ ] Cost tracking setup
- [ ] Team handoff documentation

---

## 11. Rollback Plan

If issues arise:

1. **Quick Rollback:** Revert URL map to single www.waooaw.com rule
2. **Service Rollback:** Keep old services running, switch backend services
3. **DNS Rollback:** N/A (DNS unchanged, load balancer handles routing)
4. **OAuth Rollback:** Remove new redirect URIs, restore old URLs in code

**RTO (Recovery Time Objective):** 15 minutes  
**RPO (Recovery Point Objective):** 0 (no data loss)

---

## 12. Success Criteria

✅ **Functional:**
- All 5 domains accessible via HTTPS
- OAuth login works on all domains
- No hardcoded URLs in code
- Services scale to zero when idle

✅ **Performance:**
- www.waooaw.com loads in <1s
- API responds in <500ms (P95)
- Cold starts <3s for Reflex apps

✅ **Cost:**
- Monthly cost <$150 (within policy)
- Cost tracking dashboard active
- Alert emails configured

✅ **Documentation:**
- Runbooks complete
- Team trained on new architecture
- Incident response plan documented

---

*Architecture design completed: January 3, 2026*  
*Implementation start: TBD*  
*Estimated completion: 5-7 days*
