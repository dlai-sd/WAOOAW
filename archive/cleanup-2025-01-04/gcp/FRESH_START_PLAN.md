# Fresh Start: Demo → UAT → Production (Sequential Build)

**Strategy:** Build new, discard old  
**Approach:** Clean-slate implementation starting with demo  
**Timeline:** 6 weeks  
**Status:** Ready to begin

---

## Context: Why Start Fresh?

**Current State (Production):**
- ❌ OAuth broken (hardcoded Codespace URLs)
- ❌ Wrong UI (old Platform Portal design)
- ❌ Services at wrong domains
- ❌ Not worth fixing - being replaced

**Decision:** Don't fix broken production. Build new, deploy when ready.

**Advantage:** 
- ✅ No technical debt carried forward
- ✅ Modern OAuth implementation from day 1
- ✅ New Platform Portal UI designed properly
- ✅ Clean architecture, proper domain routing
- ✅ Learn in demo, perfect in UAT, deploy to prod when ready

---

## Phase 1: Demo Environment (Week 1-2)

### Week 1: Fresh OAuth & Infrastructure

#### Day 1: OAuth Design (From Scratch)

**New OAuth Architecture:**
```python
# backend/app/auth/oauth_v2.py (NEW FILE)
"""
OAuth 2.0 Implementation - Version 2.0
Multi-domain support with automatic frontend detection
"""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
import os

router = APIRouter(prefix="/auth", tags=["authentication"])

# Multi-domain configuration
DOMAIN_CONFIG = {
    "demo": {
        "www": "https://demo-www.waooaw.com",
        "pp": "https://demo-pp.waooaw.com",
        "api": "https://demo-api.waooaw.com"
    },
    "uat": {
        "www": "https://uat-www.waooaw.com",
        "pp": "https://uat-pp.waooaw.com",
        "api": "https://uat-api.waooaw.com"
    },
    "production": {
        "www": "https://www.waooaw.com",
        "pp": "https://pp.waooaw.com",
        "api": "https://api.waooaw.com"
    }
}

def detect_environment(request: Request) -> str:
    """Detect environment from request host"""
    host = request.headers.get("host", "")
    if "demo-" in host:
        return "demo"
    elif "uat-" in host:
        return "uat"
    else:
        return "production"

def get_frontend_from_referer(request: Request, env: str) -> str:
    """Detect which frontend initiated OAuth from Referer header"""
    referer = request.headers.get("referer", "")
    config = DOMAIN_CONFIG[env]
    
    # Check which domain the user came from
    if config["www"] in referer:
        return config["www"]
    elif config["pp"] in referer:
        return config["pp"]
    else:
        # Default to www (marketplace)
        return config["www"]

@router.get("/login")
async def oauth_login(request: Request):
    """Initiate OAuth - detects environment and frontend automatically"""
    env = detect_environment(request)
    redirect_uri = f"{DOMAIN_CONFIG[env]['api']}/auth/callback"
    
    # Store origin frontend in state parameter
    frontend_url = get_frontend_from_referer(request, env)
    state = encode_state({"frontend": frontend_url})
    
    # Build OAuth URL with state
    auth_url = f"{GOOGLE_AUTH_URL}?client_id={CLIENT_ID}&redirect_uri={redirect_uri}&state={state}&..."
    
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def oauth_callback(code: str, state: str, request: Request):
    """Handle OAuth callback - redirect to correct frontend"""
    env = detect_environment(request)
    
    # Exchange code for token (standard OAuth flow)
    # ... token exchange logic ...
    
    # Decode state to get original frontend
    state_data = decode_state(state)
    frontend_url = state_data.get("frontend", DOMAIN_CONFIG[env]["www"])
    
    # Create JWT and redirect to originating frontend
    jwt_token = create_access_token(user_info)
    redirect_url = f"{frontend_url}/auth/callback?token={jwt_token}&..."
    
    return RedirectResponse(url=redirect_url)
```

**Key Improvements:**
- ✅ Automatic environment detection
- ✅ Multi-domain support built-in
- ✅ Uses OAuth state parameter to track origin
- ✅ No hardcoded URLs
- ✅ Scales to any number of domains

#### Day 2-3: Demo Infrastructure

```bash
# DNS Configuration
# Add to GoDaddy:
demo-www.waooaw.com   A  35.190.6.91  600
demo-pp.waooaw.com    A  35.190.6.91  600
demo-api.waooaw.com   A  35.190.6.91  600

# SSL Certificate (demo domains only for now)
gcloud compute ssl-certificates create waooaw-demo-cert \
    --domains=demo-www.waooaw.com,demo-pp.waooaw.com,demo-api.waooaw.com \
    --global

# Database Schema
psql waooaw-db << EOF
CREATE SCHEMA IF NOT EXISTS demo;

-- Users table
CREATE TABLE demo.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    picture TEXT,
    role VARCHAR(50) DEFAULT 'viewer',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Agents table (seed data)
CREATE TABLE demo.agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    specialty VARCHAR(255),
    status VARCHAR(50) DEFAULT 'available',
    rating DECIMAL(3,2) DEFAULT 0.0,
    price_monthly INTEGER,
    industry VARCHAR(100)
);

-- Seed demo data
INSERT INTO demo.agents (name, specialty, status, rating, price_monthly, industry) VALUES
('Marketing Pro Agent', 'Content Marketing', 'available', 4.8, 12000, 'marketing'),
('Sales Assistant Agent', 'Lead Generation', 'working', 4.9, 15000, 'sales'),
('Math Tutor Agent', 'JEE/NEET Prep', 'available', 4.7, 10000, 'education'),
('SEO Specialist Agent', 'E-commerce SEO', 'available', 4.9, 18000, 'marketing'),
('Science Tutor Agent', 'CBSE Boards', 'available', 4.6, 9000, 'education');
EOF

# OAuth Configuration
# Add to Google Cloud Console → OAuth Credentials:
# Authorized Redirect URIs:
#   https://demo-api.waooaw.com/auth/callback
#   https://demo-www.waooaw.com/auth/callback
#   https://demo-pp.waooaw.com/auth/callback
```

#### Day 4-5: Load Balancer Configuration

```bash
# Create backend services for demo
gcloud compute backend-services create demo-api-backend \
    --protocol=HTTP \
    --global

gcloud compute backend-services create demo-www-backend \
    --protocol=HTTP \
    --global

gcloud compute backend-services create demo-pp-backend \
    --protocol=HTTP \
    --global

# Add serverless NEGs (will connect to Cloud Run services)
gcloud compute network-endpoint-groups create demo-api-neg \
    --region=asia-south1 \
    --network-endpoint-type=serverless \
    --cloud-run-service=waooaw-api-demo

# Add to backend services
gcloud compute backend-services add-backend demo-api-backend \
    --global \
    --network-endpoint-group=demo-api-neg \
    --network-endpoint-group-region=asia-south1

# Update URL map (add demo host rules)
gcloud compute url-maps add-path-matcher waooaw-lb \
    --path-matcher-name=demo-api \
    --default-service=demo-api-backend \
    --new-hosts=demo-api.waooaw.com

gcloud compute url-maps add-path-matcher waooaw-lb \
    --path-matcher-name=demo-www \
    --default-service=demo-www-backend \
    --new-hosts=demo-www.waooaw.com

gcloud compute url-maps add-path-matcher waooaw-lb \
    --path-matcher-name=demo-pp \
    --default-service=demo-pp-backend \
    --new-hosts=demo-pp.waooaw.com
```

---

### Week 2: New Platform Portal UI & Deployment

#### Day 1-2: New Platform Portal Design

**Create Fresh Platform Portal:**

```bash
# New directory structure
mkdir -p PlatformPortal-v2/
cd PlatformPortal-v2/

# Initialize Reflex project
reflex init
```

**New UI Design Principles:**
- Dark theme (#0a0a0a background)
- Neon accents (cyan #00f2fe, purple #667eea)
- Modern dashboard layout
- Real-time metrics
- Responsive design

**Key Pages:**
```
/login          → OAuth login (NEW design)
/dashboard      → Metrics overview
/agents         → Agent management
/alerts         → System alerts
/metrics        → Performance metrics
/logs           → Log viewer
```

**Sample New Login Page:**
```python
# PlatformPortal-v2/pages/login.py
import reflex as rx

def login_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("WAOOAW", size="9", color="#00f2fe"),
            rx.text("Platform Portal", size="5", color="gray"),
            rx.spacer(height="2em"),
            rx.link(
                rx.button(
                    rx.hstack(
                        rx.icon("google", size=24),
                        rx.text("Login with Google"),
                    ),
                    size="4",
                    variant="solid",
                    color_scheme="blue",
                ),
                href="/auth/login",  # Goes to API OAuth endpoint
            ),
            spacing="4",
            align="center",
            padding="4em",
            background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            border_radius="24px",
            box_shadow="0 20px 60px rgba(0, 0, 0, 0.3)",
        ),
        height="100vh",
        background="#0a0a0a",
    )
```

#### Day 3: Build & Deploy Demo Services

```bash
# Build backend (new OAuth v2)
cd /workspaces/WAOOAW/backend
docker build -t asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-backend:demo .

# Build new Platform Portal (internal operations)
cd /workspaces/WAOOAW/PlatformPortal-v2
docker build -t asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-platform-portal:demo .

# Build WaooawPortal (customer-facing)
cd /workspaces/WAOOAW/WaooawPortal-v2
docker build -t asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-portal:demo .

# Push images
docker push asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-backend:demo
docker push asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-platform-portal:demo
docker push asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-portal:demo

# Deploy to Cloud Run
gcloud run deploy waooaw-api-demo \
    --image=asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-backend:demo \
    --region=asia-south1 \
    --platform=managed \
    --allow-unauthenticated \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=5 \
    --port=8000 \
    --set-env-vars="ENV=demo,DB_SCHEMA=demo" \
    --set-secrets="GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest"

gcloud run deploy waooaw-platform-portal-demo \
    --image=asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-platform-portal:demo \
    --region=asia-south1 \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=0 \
    --max-instances=3 \
    --port=3000 \
    --set-env-vars="ENV=demo,BACKEND_URL=https://demo-api.waooaw.com"

gcloud run deploy waooaw-portal-demo \
    --image=asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-portal:demo \
    --region=asia-south1 \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=10 \
    --port=8080 \
    --set-env-vars="ENV=demo,API_URL=https://demo-api.waooaw.com"
```

#### Day 4: GitHub Actions CI/CD

```yaml
# .github/workflows/deploy-demo.yml
name: Deploy to Demo

on:
  push:
    branches:
      - 'feature/**'
      - 'dev/**'
  pull_request:
    branches: [main]

env:
  PROJECT_ID: waooaw-oauth
  REGION: asia-south1
  REGISTRY: asia-south1-docker.pkg.dev
  ENVIRONMENT: demo

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
      
      - name: Configure Docker
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev
      
      - name: Build Backend
        run: |
          cd backend
          docker build -t ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/waooaw-containers/waooaw-backend:demo .
          docker push ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/waooaw-containers/waooaw-backend:demo
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy waooaw-api-demo \
            --image=${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/waooaw-containers/waooaw-backend:demo \
            --region=${{ env.REGION }} \
            --platform=managed \
            --allow-unauthenticated
      
      - name: Run Smoke Tests
        run: |
          API_URL=$(gcloud run services describe waooaw-api-demo --region=${{ env.REGION }} --format='value(status.url)')
          curl -f ${API_URL}/health || exit 1

  deploy-frontend:
    runs-on: ubuntu-latest
    needs: deploy-backend
    strategy:
      matrix:
        service: [marketplace, platform-portal]
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and Deploy ${{ matrix.service }}
        run: |
          # Similar steps for frontend services
          echo "Deploying ${{ matrix.service }} to demo"

  notify:
    runs-on: ubuntu-latest
    needs: [deploy-backend, deploy-frontend]
    if: success()
    steps:
      - name: Notify Success
        run: |
          echo "✅ Demo deployment successful!"
          echo "🔗 Marketplace: https://demo-www.waooaw.com"
          echo "🔗 Platform Portal: https://demo-pp.waooaw.com"
          echo "🔗 API: https://demo-api.waooaw.com"
```

#### Day 5: Testing & Validation

**Test Checklist:**
```bash
# 1. DNS Resolution
dig demo-www.waooaw.com
dig demo-pp.waooaw.com
dig demo-api.waooaw.com

# 2. SSL Certificates
curl -I https://demo-www.waooaw.com
curl -I https://demo-pp.waooaw.com
curl -I https://demo-api.waooaw.com

# 3. OAuth Flow
# Manual: Go to demo-pp.waooaw.com/login
# Click "Login with Google"
# Should redirect to Google
# After approval, should return to demo-pp with token

# 4. API Health
curl https://demo-api.waooaw.com/health

# 5. Database Connectivity
curl https://demo-api.waooaw.com/agents
# Should return list of 5 demo agents

# 6. End-to-End Test
# Login to demo-pp → View agents → Check logs → Logout
```

**Week 2 Deliverable:** ✅ Fully functional demo environment with new OAuth and new UI

---

## Phase 2: UAT Environment (Week 3-4)

### Week 3: Clone Demo to UAT

#### Day 1-2: UAT Infrastructure (Mirror Demo Setup)

```bash
# DNS
uat-www.waooaw.com   A  35.190.6.91  600
uat-pp.waooaw.com    A  35.190.6.91  600
uat-api.waooaw.com   A  35.190.6.91  600

# SSL Certificate (add UAT domains)
gcloud compute ssl-certificates create waooaw-demo-uat-cert \
    --domains=demo-www.waooaw.com,demo-pp.waooaw.com,demo-api.waooaw.com,\
uat-www.waooaw.com,uat-pp.waooaw.com,uat-api.waooaw.com \
    --global

# Database Schema (UAT)
psql waooaw-db << EOF
CREATE SCHEMA IF NOT EXISTS uat;

-- Copy structure from demo schema
CREATE TABLE uat.users (LIKE demo.users INCLUDING ALL);
CREATE TABLE uat.agents (LIKE demo.agents INCLUDING ALL);

-- Copy production data (sanitized)
-- Script to anonymize production data and copy to UAT
EOF

# OAuth Redirect URIs (add to Google Console)
# https://uat-api.waooaw.com/auth/callback
# https://uat-www.waooaw.com/auth/callback
# https://uat-pp.waooaw.com/auth/callback

# Load Balancer (add UAT host rules)
# Mirror demo setup for uat-* domains
```

#### Day 3-4: UAT Deployment

```bash
# Build with uat tag
docker build -t .../waooaw-backend:uat backend/
docker build -t .../waooaw-platform-portal:uat PlatformPortal-v2/
docker build -t .../waooaw-portal:uat WaooawPortal-v2/

# Deploy UAT services
gcloud run deploy waooaw-api-uat --image=.../waooaw-backend:uat ...
gcloud run deploy waooaw-platform-portal-uat --image=.../waooaw-platform-portal:uat ...
gcloud run deploy waooaw-portal-uat --image=.../waooaw-portal:uat ...
```

#### Day 5: GitHub Actions for UAT

```yaml
# .github/workflows/deploy-uat.yml
name: Deploy to UAT

on:
  push:
    branches:
      - 'release/**'

env:
  ENVIRONMENT: uat

# Similar to demo workflow but deploys to uat-* services
```

### Week 4: QA Testing

**QA Test Suite:**

1. **Functional Testing**
   - OAuth login/logout on all frontends
   - Agent CRUD operations
   - User role-based access
   - Metrics dashboard functionality

2. **Integration Testing**
   - Frontend ↔ API communication
   - Database queries performance
   - Real-time updates (WebSocket)

3. **Security Testing**
   - OAuth token validation
   - CORS configuration
   - Input sanitization
   - SQL injection attempts

4. **Performance Testing**
   ```bash
   # Load test with k6
   k6 run load-test.js --vus 100 --duration 5m
   
   # Monitor Cloud Run metrics
   gcloud monitoring dashboards list
   ```

5. **User Acceptance Testing**
   - Sales team demos features
   - Product team validates workflows
   - Stakeholders sign-off

**Week 4 Deliverable:** ✅ UAT environment validated and approved for production

---

## Phase 3: Production Deployment (Week 5-6)

### Week 5: Production Migration

#### Day 1: Production Infrastructure

```bash
# Update existing production domains to point to new services
# Current: www.waooaw.com points to old waooaw-frontend-staging
# New: Will point to new waooaw-marketplace-prod

# SSL Certificate (add production to existing cert)
gcloud compute ssl-certificates create waooaw-multi-env-cert \
    --domains=www.waooaw.com,pp.waooaw.com,api.waooaw.com,\
demo-www.waooaw.com,demo-pp.waooaw.com,demo-api.waooaw.com,\
uat-www.waooaw.com,uat-pp.waooaw.com,uat-api.waooaw.com \
    --global

# Database: Production uses 'public' schema
# No changes needed - already exists

# OAuth: Update redirect URIs
# https://api.waooaw.com/auth/callback
# https://www.waooaw.com/auth/callback
# https://pp.waooaw.com/auth/callback
```

#### Day 2-3: Production Deployment

```bash
# Build production images
docker build -t .../waooaw-backend:prod backend/
docker build -t .../waooaw-platform-portal:prod PlatformPortal-v2/
docker build -t .../waooaw-portal:prod WaooawPortal-v2/

# Deploy new services (rename old ones first)
gcloud run services update waooaw-frontend-staging \
    --tag=old-frontend

gcloud run deploy waooaw-api \
    --image=.../waooaw-backend:prod \
    --region=asia-south1 \
    --set-env-vars="ENV=production,DB_SCHEMA=public" \
    --min-instances=0

gcloud run deploy waooaw-platform-portal \
    --image=.../waooaw-platform-portal:prod \
    --region=asia-south1 \
    --set-env-vars="ENV=production,BACKEND_URL=https://api.waooaw.com"

gcloud run deploy waooaw-portal \
    --image=.../waooaw-portal:prod \
    --region=asia-south1 \
    --set-env-vars="ENV=production,API_URL=https://api.waooaw.com"

# Update load balancer to point to new services
gcloud compute url-maps import waooaw-lb \
    --source=updated-url-map.yaml

# Test production
curl https://www.waooaw.com
curl https://pp.waooaw.com
curl https://api.waooaw.com/health
```

#### Day 4: Smoke Testing & Monitoring

```bash
# Smoke tests on production
curl -f https://www.waooaw.com || echo "FAIL"
curl -f https://pp.waooaw.com || echo "FAIL"
curl -f https://api.waooaw.com/health || echo "FAIL"

# OAuth test (manual)
# Go to pp.waooaw.com/login
# Login with Google
# Verify redirect works

# Set up monitoring alerts
gcloud alpha monitoring policies create \
    --notification-channels=<EMAIL> \
    --display-name="Production Error Rate" \
    --condition-threshold-value=0.01
```

#### Day 5: Rollback Plan & Cleanup

```bash
# If issues found, rollback:
# 1. Update load balancer to point back to old services
# 2. Rollback Cloud Run revisions

# If successful, cleanup old services:
gcloud run services delete waooaw-frontend-staging
gcloud run services delete waooaw-backend-staging

# Document new architecture
```

### Week 6: CI/CD, Documentation & Optimization

#### Day 1-2: Production CI/CD

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches:
      - main
  
env:
  ENVIRONMENT: production

jobs:
  approve:
    runs-on: ubuntu-latest
    steps:
      - name: Require Manual Approval
        uses: trstringer/manual-approval@v1
        with:
          secret: ${{ github.TOKEN }}
          approvers: yogeshkhandge
          minimum-approvals: 1
  
  deploy:
    needs: approve
    runs-on: ubuntu-latest
    # Deploy to production services
```

#### Day 3-4: Documentation

**Create Runbooks:**
- Demo environment reset procedure
- UAT data refresh from production
- Production deployment checklist
- Rollback procedures
- OAuth troubleshooting guide

#### Day 5: Cost Optimization & Review

```bash
# Review actual costs for all 3 environments
gcloud billing budgets list

# Optimize scale-to-zero
gcloud run services update waooaw-portal-demo \
    --min-instances=0 \
    --timeout=300s

# Set up cost alerts
# Document actual vs estimated costs
```

**Week 6 Deliverable:** ✅ Production running on new architecture, all environments operational

---

## Success Criteria

### Demo Environment
- ✅ New OAuth working on all 3 domains
- ✅ New Platform Portal UI functional
- ✅ Sales team can demo features
- ✅ Cost: <$15/month

### UAT Environment  
- ✅ QA test suite passing 100%
- ✅ Performance benchmarks met
- ✅ Security audit passed
- ✅ Cost: <$35/month

### Production
- ✅ Zero downtime migration
- ✅ OAuth working for all users
- ✅ New Platform Portal deployed
- ✅ Old services decommissioned
- ✅ Cost: <$150/month
- ✅ **Total: <$200/month**

---

## Timeline Summary

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | Demo Infrastructure + Fresh OAuth | DNS, SSL, DB, New OAuth v2 |
| 2 | New Platform Portal UI + CI/CD | Demo fully functional |
| 3 | UAT Infrastructure | UAT environment ready |
| 4 | QA Testing | UAT validated and approved |
| 5 | Production Deployment | New services live |
| 6 | CI/CD + Documentation | All environments production-ready |

**Total Duration:** 6 weeks  
**Start Date:** Week of January 6, 2026  
**Target Completion:** Week of February 17, 2026

---

## Key Decisions Made

1. ✅ **Scrap old OAuth** - Build clean OAuth v2 with multi-domain support
2. ✅ **Redesign Platform Portal** - New UI in PlatformPortal-v2/
3. ✅ **Sequential build** - Demo → UAT → Production
4. ✅ **Shared database** - Schemas (demo, uat, public) with migration path to separate DBs
5. ✅ **GitHub Actions** - CI/CD tool
6. ✅ **Don't fix production** - Will be replaced completely

---

## Next Actions

**Week 1 Starts Monday:**
1. Create PlatformPortal-v2/ directory structure
2. Design new OAuth v2 implementation (oauth_v2.py)
3. Set up demo DNS records in GoDaddy
4. Create demo SSL certificate
5. Add demo database schema

**Ready to begin?** Let me know and I'll start with:
1. Creating new OAuth v2 implementation
2. Setting up new Platform Portal directory structure
3. Preparing GitHub Actions workflows

---

**Status:** 🟢 Ready to execute  
**Approach:** Clean slate, sequential build  
**Timeline:** 6 weeks to production  
**Budget:** $190/month (requires CTO approval)
