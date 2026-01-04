# CI/CD Environments Analysis - Demo & UAT

**Analysis Date:** January 3, 2026  
**Status:** Proposal - Awaiting Approval  
**Requested By:** User  
**Analyzed By:** GitHub Copilot

---

## 1. Requirement Summary

**Objective:** Add demo and UAT (User Acceptance Testing) environments as subdomains for CI/CD pipeline testing before production deployment.

**Use Cases:**
1. **Demo Environment:** Showcase new features to stakeholders, sales demos, customer previews
2. **UAT Environment:** QA testing, user acceptance testing, pre-production validation
3. **CI/CD Integration:** Automated deployment pipelines (feature → demo → UAT → prod)

---

## 2. Subdomain Strategy Options

### Option 1: Environment Prefix (RECOMMENDED)

**Pattern:** `{env}-{app}.waooaw.com`

| Environment | Marketplace | Platform Portal | Dev Portal | Customer YK | API |
|-------------|-------------|-----------------|------------|-------------|-----|
| **Production** | www.waooaw.com | pp.waooaw.com | dp.waooaw.com | yk.waooaw.com | api.waooaw.com |
| **UAT** | uat-www.waooaw.com | uat-pp.waooaw.com | uat-dp.waooaw.com | uat-yk.waooaw.com | uat-api.waooaw.com |
| **Demo** | demo-www.waooaw.com | demo-pp.waooaw.com | demo-dp.waooaw.com | demo-yk.waooaw.com | demo-api.waooaw.com |

**Pros:**
- ✅ Clear environment identification
- ✅ Consistent pattern across all apps
- ✅ Easy to automate in CI/CD (env prefix = branch name)
- ✅ DNS wildcard possible: `*.waooaw.com` → Load Balancer
- ✅ Standard industry practice

**Cons:**
- ❌ 10 additional subdomains (5 apps × 2 envs)
- ❌ 10 additional OAuth redirect URIs
- ❌ 10 additional SSL certificate SANs

---

### Option 2: Simplified Environment Domains

**Pattern:** `{env}.waooaw.com` with path-based routing

| Environment | URL Pattern |
|-------------|-------------|
| **Demo** | demo.waooaw.com/marketplace<br>demo.waooaw.com/portal<br>demo.waooaw.com/api |
| **UAT** | uat.waooaw.com/marketplace<br>uat.waooaw.com/portal<br>uat.waooaw.com/api |

**Pros:**
- ✅ Only 2 additional domains (demo, uat)
- ✅ Simpler SSL certificate (only 2 more SANs)
- ✅ Easier OAuth configuration (only 2 more redirect URIs)
- ✅ Lower DNS management overhead

**Cons:**
- ❌ Path-based routing adds complexity to Load Balancer
- ❌ Cannot serve different apps at root (/)
- ❌ OAuth redirects get messy with paths
- ❌ Reflex apps expect to be at root, not /portal

---

### Option 3: Dedicated Environment Subdomains

**Pattern:** Simplified app naming in non-prod

| Environment | URLs |
|-------------|------|
| **Demo** | demo.waooaw.com (marketplace)<br>demo-portal.waooaw.com (platform portal)<br>demo-api.waooaw.com (API only) |
| **UAT** | uat.waooaw.com (marketplace)<br>uat-portal.waooaw.com (platform portal)<br>uat-api.waooaw.com (API only) |

**Pros:**
- ✅ Fewer domains than Option 1 (6 total: demo, demo-portal, demo-api, uat, uat-portal, uat-api)
- ✅ Marketplace at root (best UX for demos)
- ✅ Simpler mental model (demo = customer view)

**Cons:**
- ❌ Inconsistent with production naming (www vs demo)
- ❌ Still 6 additional domains to manage
- ❌ Internal tools (pp, dp, yk) not available in non-prod

---

## 3. RECOMMENDATION: Hybrid Approach

**Strategy:** Option 1 for critical paths, simplified for others

### 3.1 Essential Testing Environments

**Deploy in Demo & UAT:**
- ✅ Marketplace (www) - Customer-facing, highest priority
- ✅ Platform Portal (pp) - Operations team, critical workflows
- ✅ API - Backend, all functionality

**Skip in Demo & UAT (initially):**
- ❌ Dev Portal (dp) - Internal dev tool, low testing value
- ❌ Customer YK Portal (yk) - Not built yet, defer

**Subdomain Layout:**

| Environment | Marketplace | Platform Portal | API | Total |
|-------------|-------------|-----------------|-----|-------|
| Production | www.waooaw.com | pp.waooaw.com | api.waooaw.com | 3 |
| UAT | uat-www.waooaw.com | uat-pp.waooaw.com | uat-api.waooaw.com | 3 |
| Demo | demo-www.waooaw.com | demo-pp.waooaw.com | demo-api.waooaw.com | 3 |
| **TOTAL** | | | | **9 domains** |

**Additional When Ready:**
- dp.waooaw.com, yk.waooaw.com (production only)
- uat-dp, uat-yk, demo-dp, demo-yk (if needed later)

---

## 4. Cost Analysis

### 4.1 Current Production Cost (Phase 1)

| Service | Monthly Cost |
|---------|-------------|
| waooaw-api | $25-35 |
| waooaw-marketplace | $15-20 |
| waooaw-platform-portal | $25-35 |
| waooaw-dev-portal | $10-15 |
| waooaw-customer-yk | $10-15 |
| Load Balancer | $18 |
| **TOTAL** | **$103-138** |

### 4.2 With Demo + UAT (Recommended Setup)

| Environment | Services | Scale Config | Monthly Cost | Notes |
|-------------|----------|--------------|--------------|-------|
| **Production** | 5 services | min=0, warm cache | $103-138 | As above |
| **UAT** | 3 services (www, pp, api) | min=0, no warm cache | $30-45 | Testing only, low traffic |
| **Demo** | 3 services (www, pp, api) | min=0, cold start OK | $20-30 | Sporadic use |
| **Load Balancer** | 1 (shared) | Handles all 11 domains | $18 | No extra cost |
| **SSL Certificate** | 1 multi-domain | 11 SANs | $0 | Google-managed, free |
| **Artifact Registry** | 1 (shared) | 3 images × 3 tags | +$2-5 | Storage for demo/uat images |
| | | | | |
| **TOTAL** | **11 services** | **3 environments** | **$153-216** | **+$50-78/month** |

### 4.3 Cost Optimization Strategies

**Scale-to-Zero Aggressively:**
```yaml
# Demo services (only active during demos)
min-instances: 0
max-instances: 2
timeout: 300s  # 5 min

# UAT services (active during business hours)
min-instances: 0
max-instances: 5
timeout: 300s
```

**Expected Real Cost:**
- Demo: $10-15/month (5-10 hours usage/month)
- UAT: $25-35/month (40-60 hours usage/month, QA cycles)
- **Total Addition:** $35-50/month

**Revised Total Budget:** $138-188/month

**Policy Impact:** Exceeds $150 ceiling → **Requires CTO approval per POLICY-TECH-001**

---

## 5. CI/CD Pipeline Integration

### 5.1 Proposed Git Branch Strategy

```
main (production)
  ↓
  └─ release/* (UAT)
       ↓
       └─ feature/* (Demo)
```

**Deployment Flow:**

1. **Feature Branch → Demo Environment**
   - PR opened on feature branch
   - Auto-deploy to demo-{app}.waooaw.com
   - Smoke tests run
   - Stakeholders review at demo URLs

2. **Merge to release/* → UAT Environment**
   - Feature branch merged to release/v1.x
   - Auto-deploy to uat-{app}.waooaw.com
   - Full test suite runs
   - QA team performs acceptance testing
   - Performance/load testing

3. **Merge to main → Production**
   - Release branch merged to main (with approvals)
   - Auto-deploy to production (www, pp, api, etc.)
   - Smoke tests in production
   - Rollback available if needed

### 5.2 Cloud Build Configuration

**Update cloudbuild.yaml:**

```yaml
substitutions:
  _BRANCH_NAME: ${BRANCH_NAME}
  _ENV: |
    $(if [ "${BRANCH_NAME}" = "main" ]; then
        echo "production"
      elif [[ "${BRANCH_NAME}" =~ ^release/ ]]; then
        echo "uat"
      else
        echo "demo"
      fi)
  _DOMAIN_PREFIX: |
    $(if [ "${_ENV}" = "production" ]; then
        echo ""
      else
        echo "${_ENV}-"
      fi)

steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-backend:${_ENV}-latest'
      - './backend'

  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'waooaw-api-${_ENV}'
      - '--image=asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-backend:${_ENV}-latest'
      - '--region=asia-south1'
      - '--set-env-vars=ENV=${_ENV},FRONTEND_URL=https://${_DOMAIN_PREFIX}www.waooaw.com'
```

### 5.3 GitHub Actions Alternative

**Pros vs Cloud Build:**
- ✅ Better secret management (GitHub Secrets)
- ✅ More flexible workflows (matrix builds)
- ✅ Free for public repos (2000 min/month)
- ✅ Native GitHub integration (PR comments, status checks)

**Sample Workflow:**

```yaml
# .github/workflows/deploy.yml
name: Deploy to GCP

on:
  push:
    branches: [main, 'release/*', 'feature/*']
  pull_request:
    branches: [main, 'release/*']

jobs:
  determine-environment:
    runs-on: ubuntu-latest
    outputs:
      env: ${{ steps.set-env.outputs.env }}
    steps:
      - id: set-env
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "env=production" >> $GITHUB_OUTPUT
          elif [[ "${{ github.ref }}" =~ refs/heads/release/ ]]; then
            echo "env=uat" >> $GITHUB_OUTPUT
          else
            echo "env=demo" >> $GITHUB_OUTPUT
          fi

  deploy:
    needs: determine-environment
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api, marketplace, platform-portal]
    steps:
      - uses: actions/checkout@v3
      
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Deploy to Cloud Run
        run: |
          ENV=${{ needs.determine-environment.outputs.env }}
          SERVICE=${{ matrix.service }}
          PREFIX=$([ "$ENV" = "production" ] && echo "" || echo "${ENV}-")
          
          gcloud run deploy waooaw-${SERVICE}-${ENV} \
            --image=asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-${SERVICE}:${ENV} \
            --region=asia-south1 \
            --set-env-vars=ENV=${ENV}
```

---

## 6. Infrastructure Requirements

### 6.1 DNS Configuration (GoDaddy)

**Add A Records:**

| Subdomain | Type | Value | TTL |
|-----------|------|-------|-----|
| uat-www | A | 35.190.6.91 | 600 |
| uat-pp | A | 35.190.6.91 | 600 |
| uat-api | A | 35.190.6.91 | 600 |
| demo-www | A | 35.190.6.91 | 600 |
| demo-pp | A | 35.190.6.91 | 600 |
| demo-api | A | 35.190.6.91 | 600 |

**Alternative: Wildcard (Simpler)**

| Subdomain | Type | Value | TTL |
|-----------|------|-------|-----|
| * | A | 35.190.6.91 | 600 |

Covers all subdomains with one record (demo-*, uat-*, staging-*, etc.)

### 6.2 SSL Certificate Update

**Current:** www.waooaw.com only  
**Required:** Multi-domain certificate

```bash
gcloud compute ssl-certificates create waooaw-multi-env-cert \
    --domains=www.waooaw.com,pp.waooaw.com,dp.waooaw.com,yk.waooaw.com,api.waooaw.com,\
uat-www.waooaw.com,uat-pp.waooaw.com,uat-api.waooaw.com,\
demo-www.waooaw.com,demo-pp.waooaw.com,demo-api.waooaw.com \
    --global
```

**Cost:** $0 (Google-managed certificates are free)  
**Limit:** 100 SANs per certificate (we'll use 11)

### 6.3 Load Balancer Host Rules

**Update existing LB (waooaw-lb):**

```bash
# Add URL maps for UAT
gcloud compute url-maps add-path-matcher waooaw-lb \
    --path-matcher-name=uat-api \
    --default-service=waooaw-api-uat \
    --new-hosts=uat-api.waooaw.com

# Add URL maps for Demo
gcloud compute url-maps add-path-matcher waooaw-lb \
    --path-matcher-name=demo-api \
    --default-service=waooaw-api-demo \
    --new-hosts=demo-api.waooaw.com

# Repeat for uat-www, uat-pp, demo-www, demo-pp
```

### 6.4 OAuth Configuration

**Google Cloud Console → OAuth Credentials → Add Redirect URIs:**

```
https://uat-api.waooaw.com/auth/callback
https://uat-www.waooaw.com/auth/callback
https://uat-pp.waooaw.com/auth/callback
https://demo-api.waooaw.com/auth/callback
https://demo-www.waooaw.com/auth/callback
https://demo-pp.waooaw.com/auth/callback
```

**Total OAuth Redirect URIs:** 11 (5 prod + 6 non-prod)

---

## 7. Data & Database Strategy

### 7.1 Database Separation

**Option A: Separate Databases per Environment (RECOMMENDED)**

```
Production:   waooaw-prod-db    (Cloud SQL, always on)
UAT:          waooaw-uat-db     (Cloud SQL, can stop overnight)
Demo:         waooaw-demo-db    (Cloud SQL, stop when not in use)
```

**Pros:**
- ✅ Complete data isolation
- ✅ UAT can have realistic prod-like data
- ✅ Demo can have sanitized/fake data
- ✅ No risk of test data polluting production

**Cost:**
- Production DB: $50-80/month (db-f1-micro, always on)
- UAT DB: $30-50/month (db-f1-micro, stopped at night)
- Demo DB: $15-25/month (db-f1-micro, mostly stopped)
- **Total DB Cost:** $95-155/month

**Option B: Shared Database with Schema Separation**

```
Single Cloud SQL instance: waooaw-db
Schemas:
  - public (production)
  - uat (UAT data)
  - demo (demo data)
```

**Pros:**
- ✅ Lower cost ($50-80/month total)
- ✅ Simpler management (1 instance)

**Cons:**
- ❌ Risk of cross-schema queries
- ❌ Difficult to restore UAT/demo independently
- ❌ Performance impact if all environments hit same instance

**RECOMMENDATION:** Option A (separate databases) for safety and independent scaling.

### 7.2 Data Management

**Production:**
- Real customer data
- Regular backups (daily, retain 30 days)
- No direct access, audit all queries

**UAT:**
- Sanitized copy of production data (refresh weekly)
- PII anonymized (emails → test@example.com)
- Can be wiped and reloaded for testing

**Demo:**
- Fake seed data (scripted)
- 5-10 sample agents, 20-30 sample customers
- Reset weekly to clean state

---

## 8. Security & Access Control

### 8.1 Authentication Differences

| Environment | Auth Method | Users |
|-------------|-------------|-------|
| **Production** | Google OAuth | Real customers |
| **UAT** | Google OAuth | Internal team + test accounts |
| **Demo** | Google OAuth | Sales team + whitelisted emails |

**OAuth Configuration:**
- Use same Google OAuth client (simpler)
- Backend determines environment from URL
- User role assignment per environment in database

### 8.2 IP Restrictions (Optional)

**Demo Environment:**
```bash
# Restrict to company IPs only
gcloud run services update waooaw-marketplace-demo \
    --ingress=internal-and-cloud-load-balancing \
    --vpc-connector=waooaw-vpc

# Configure VPC firewall rules
gcloud compute firewall-rules create allow-demo-access \
    --allow=tcp:443 \
    --source-ranges=<COMPANY_IP_RANGE>
```

**Cost Impact:** +$10-15/month for VPC connector (optional)

---

## 9. Monitoring & Observability

### 9.1 Environment-Specific Dashboards

**Create separate dashboards:**
- Production Dashboard (existing)
- UAT Dashboard (test metrics, error budgets)
- Demo Dashboard (usage tracking)

**Key Metrics for Non-Prod:**
- Deployment frequency
- Test success rate
- Average demo duration
- UAT defect detection rate

### 9.2 Alert Policies

**Production:** High priority, page on-call  
**UAT:** Medium priority, email only  
**Demo:** Low priority, daily digest

```bash
# UAT error rate alert (email only)
gcloud alpha monitoring policies create \
    --notification-channels=<EMAIL_CHANNEL> \
    --display-name="UAT Error Rate" \
    --condition-threshold-value=0.05 \
    --condition-filter='resource.labels.service_name=~".*-uat"'
```

---

## 10. Rollout Plan

### Phase 1: Infrastructure Setup (Week 1)
- [ ] Get CTO approval for budget increase ($50/month)
- [ ] Create wildcard DNS or 6 specific A records
- [ ] Create multi-domain SSL certificate (11 domains)
- [ ] Update Load Balancer host rules
- [ ] Add 6 OAuth redirect URIs

### Phase 2: Database Setup (Week 1)
- [ ] Create waooaw-uat-db (Cloud SQL)
- [ ] Create waooaw-demo-db (Cloud SQL)
- [ ] Create seed data script for demo
- [ ] Create sanitization script for UAT

### Phase 3: CI/CD Pipeline (Week 2)
- [ ] Update cloudbuild.yaml with environment detection
- [ ] Create GitHub Actions workflow (or update Cloud Build)
- [ ] Configure branch protection rules
- [ ] Test deployment to demo environment

### Phase 4: Testing & Validation (Week 2)
- [ ] Deploy to demo-* domains
- [ ] Deploy to uat-* domains
- [ ] Validate OAuth flow on all 11 domains
- [ ] Run smoke tests on each environment
- [ ] Load test UAT environment

### Phase 5: Documentation (Week 3)
- [ ] Update runbooks with environment procedures
- [ ] Document CI/CD pipeline for team
- [ ] Create demo reset procedure
- [ ] Create UAT data refresh procedure

---

## 11. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Budget overrun | High | Medium | Aggressive scale-to-zero, monitoring alerts |
| Test data leaks to prod | Critical | Low | Separate databases, code review |
| Demo breaks before important demo | High | Medium | Auto-reset daily, health checks |
| UAT environment drift | Medium | High | Weekly refresh from prod backup |
| CI/CD pipeline complexity | Medium | High | Thorough testing, rollback procedures |

---

## 12. Alternatives Considered

### Alternative 1: Staging Only (No Demo)

**Cost:** $25-35/month  
**Downside:** No sales demo environment, features shown in staging (confusing)

### Alternative 2: Single "Test" Environment

**Cost:** $15-25/month  
**Downside:** Conflicts between QA testing and sales demos

### Alternative 3: On-Demand Environments (Preview Deployments)

**Pattern:** `pr-{NUMBER}.waooaw.com` per pull request  
**Cost:** $5-10 per active PR  
**Pros:** Isolated testing, clean environments  
**Cons:** Complex setup, short-lived, not suitable for demos

---

## 13. Recommendation Summary

### ✅ APPROVED APPROACH

**Environments:** Production + UAT + Demo (3 total)

**Subdomains:** 9 domains
- Prod: www, pp, api (+ dp, yk later)
- UAT: uat-www, uat-pp, uat-api
- Demo: demo-www, demo-pp, demo-api

**Cost Impact:** +$50-78/month → **Total: $153-216/month**

**Budget Status:** Exceeds $150 policy limit → **Requires CTO approval**

**Justification for CTO Approval:**
1. Critical for QA process (prevent prod bugs)
2. Enables sales demos without prod risk
3. Standard industry practice (dev/test/prod)
4. Can optimize costs with scale-to-zero ($35-50 realistic)
5. ROI: Prevent 1 critical prod bug = save hours of downtime cost

**Infrastructure Needs:**
- Wildcard DNS or 6 A records
- 11-domain SSL certificate (free)
- 6 OAuth redirect URIs
- 2 additional Cloud SQL databases
- Load Balancer host rule updates

**CI/CD Integration:**
- GitHub Actions recommended (better than Cloud Build for multi-env)
- Branch strategy: feature → demo, release/* → UAT, main → prod
- Automated testing at each stage

---

## 14. Next Steps

**Awaiting Decision:**
1. Approve budget increase to $190/month (or optimize to $180)
2. Choose CI/CD tool (GitHub Actions vs Cloud Build)
3. Choose database strategy (separate DBs vs shared with schemas)
4. Confirm subdomain naming convention

**Ready to Implement:**
- DNS configuration
- SSL certificate creation
- Load Balancer updates
- OAuth redirect URI additions
- Database setup scripts

---

**Analysis Completed By:** GitHub Copilot  
**Date:** January 3, 2026  
**Next Action:** User approval to proceed with implementation  
**Estimated Implementation Time:** 2-3 weeks
