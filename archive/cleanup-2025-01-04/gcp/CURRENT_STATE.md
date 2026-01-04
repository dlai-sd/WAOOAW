# Current GCP Infrastructure State

**Discovery Date:** January 3, 2026  
**Discovery Method:** gcloud CLI commands  
**Project:** waooaw-oauth (270293855600)

---

## 1. Compute & Networking

### 1.1 Static IP Addresses

| Name | IP Address | Type | Status | Usage |
|------|-----------|------|--------|-------|
| waooaw-lb-ip | 35.190.6.91 | EXTERNAL | IN_USE | Load Balancer |

**DNS Configuration:**
- www.waooaw.com → 35.190.6.91 (configured in GoDaddy)

---

### 1.2 Load Balancer Configuration

**URL Map:** `waooaw-lb`
- **Default Service:** waooaw-frontend-service (Platform Portal)
- **Creation:** 2026-01-02

**Host Rules:**
```yaml
hosts:
  - www.waooaw.com
pathMatcher: waooaw-matcher
```

**Path Rules:**
```yaml
# Routes /api/*, /auth/login, /health to backend
paths:
  - /api/*
  - /auth/login
  - /health
service: waooaw-backend-service

# Everything else goes to frontend
defaultService: waooaw-frontend-service
```

**Issue Identified:**
- ❌ Only www.waooaw.com configured (missing pp, dp, yk, api subdomains)
- ❌ All traffic to www goes to frontend (Platform Portal), should be customer marketplace

---

### 1.3 Backend Services

| Name | Backend | Protocol | NEG Location |
|------|---------|----------|--------------|
| waooaw-backend-service | waooaw-backend-neg | HTTP | us-central1 |
| waooaw-frontend-service | waooaw-frontend-neg | HTTP | us-central1 |

---

### 1.4 HTTPS Configuration

**Target HTTPS Proxy:** `waooaw-https-proxy`
- SSL Certificate: waooaw-ssl-cert
- URL Map: waooaw-lb

**Forwarding Rules:**

| Name | IP | Protocol | Target |
|------|--------|----------|--------|
| waooaw-http-forwarding-rule | 35.190.6.91 | TCP (80) | waooaw-http-proxy |
| waooaw-https-forwarding-rule | 35.190.6.91 | TCP (443) | waooaw-https-proxy |

**Status:** ✅ HTTP → HTTPS redirect working

---

### 1.5 SSL Certificates

**Certificate:** `waooaw-ssl-cert`
- **Type:** Google-managed
- **Status:** ACTIVE
- **Domains:** www.waooaw.com (ACTIVE)
- **Expiry:** 2026-04-02
- **Auto-renewal:** Enabled

**Issue Identified:**
- ❌ Only www.waooaw.com covered
- ❌ Missing: pp.waooaw.com, dp.waooaw.com, yk.waooaw.com, api.waooaw.com

---

## 2. Cloud Run Services

### 2.1 Backend API

**Service:** `waooaw-backend-staging`
- **Region:** us-central1
- **URL:** https://waooaw-backend-staging-ryvhxvrdna-uc.a.run.app
- **Image:** us-central1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-backend:latest
- **Last Deployed:** 2026-01-02 18:34:39 UTC
- **Deployed By:** 270293855600-compute@developer.gserviceaccount.com (Cloud Build)

**Environment Variables:**
```yaml
ENV: staging
FRONTEND_URL: https://www.waooaw.com
GOOGLE_REDIRECT_URI: https://api.waooaw.com/auth/callback
GOOGLE_CLIENT_ID: (from secret)
GOOGLE_CLIENT_SECRET: (from secret)
```

**Issue Identified:**
- ✅ OAuth configured for production domains
- ❌ Service name includes "-staging" (should be production)
- ⚠️ FRONTEND_URL is www.waooaw.com (correct) but that domain currently serves Platform Portal (incorrect)

---

### 2.2 Frontend (Platform Portal)

**Service:** `waooaw-frontend-staging`
- **Region:** us-central1
- **URL:** https://waooaw-frontend-staging-ryvhxvrdna-uc.a.run.app
- **Image:** us-central1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-frontend:latest
- **Last Deployed:** 2026-01-02 18:11:29 UTC
- **Deployed By:** yogeshkhandge@gmail.com

**Issue Identified:**
- ❌ Deployed as "frontend" but is actually Platform Portal (Reflex app)
- ❌ Should be deployed at pp.waooaw.com, not www.waooaw.com
- ❌ Missing actual customer-facing frontend (React marketplace)

---

### 2.3 Missing Services

| Service | Domain | Status | Technology |
|---------|--------|--------|------------|
| Customer Marketplace | www.waooaw.com | ❌ Not deployed | React (to be built) |
| Platform Portal | pp.waooaw.com | ❌ Not mapped | Reflex (deployed as frontend-staging) |
| Development Portal | dp.waooaw.com | ❌ Not deployed | Reflex (to be cloned from pp) |
| Customer Portal (YK) | yk.waooaw.com | ❌ Not deployed | React (to be built) |

---

## 3. Artifact Registry

**Repository:** `waooaw-containers`
- **Location:** us-central1
- **Format:** Docker
- **Size:** 8,484 MB (8.4 GB)
- **Created:** 2026-01-02
- **Last Updated:** 2026-01-02 18:34:04

**Images:**
- waooaw-backend:latest (last push: 2026-01-02)
- waooaw-frontend:latest (last push: 2026-01-02)

---

## 4. Secret Manager

**Secrets:**

| Name | Created | Replication | Status |
|------|---------|-------------|--------|
| google-client-id | 2026-01-02 13:54:04 | Automatic | ✅ Active |
| google-client-secret | 2026-01-02 13:54:16 | Automatic | ✅ Active |

**Issue Identified:**
- ✅ OAuth secrets stored securely
- ⚠️ Need to verify redirect URIs in Google Cloud Console

---

## 5. OAuth Configuration

### 5.1 Backend OAuth Settings

**From waooaw-backend-staging environment:**
```
GOOGLE_REDIRECT_URI: https://api.waooaw.com/auth/callback
FRONTEND_URL: https://www.waooaw.com
```

### 5.2 Required Redirect URIs

Based on 5-domain architecture, Google Cloud Console should have:
```
https://api.waooaw.com/auth/callback         (backend OAuth handler)
https://www.waooaw.com/auth/callback         (customer marketplace)
https://pp.waooaw.com/auth/callback          (platform portal)
https://dp.waooaw.com/auth/callback          (dev portal)
https://yk.waooaw.com/auth/callback          (customer portal)
```

**Issue Identified:**
- ❓ Unknown which redirect URIs are currently registered in Google Cloud Console
- ❓ Need to verify OAuth consent screen configuration

---

## 6. Domain Mappings

**Attempt to list domain mappings:**
```
gcloud beta run domain-mappings list --region us-central1
Result: 0 items
```

**Issue Identified:**
- ❌ No Cloud Run domain mappings configured
- ❌ Services accessed via long *.run.app URLs
- ❌ Custom domains (pp, dp, yk, api) not mapped to services

---

## 7. CI/CD Configuration

**Cloud Build Trigger:** (Not queried, check manually)
- Last successful build: 2026-01-02
- Build config: /workspaces/WAOOAW/cloudbuild.yaml

**Current cloudbuild.yaml issues:**
- ✅ Builds both backend and frontend
- ❌ Deploys as "staging" services (should be production)
- ❌ Only 2 services (missing www, pp, dp, yk separation)
- ❌ Hardcoded domain mappings attempt (fails without DNS verification)

---

## 8. Cost Analysis (Current)

**Estimated Monthly Costs:**

| Resource | Usage | Estimated Cost |
|----------|-------|----------------|
| Cloud Run (backend) | Low traffic, scale-to-zero | $12-15/month |
| Cloud Run (frontend) | Low traffic, scale-to-zero | $18-22/month |
| Load Balancer | Global HTTPS LB | $15-20/month |
| Artifact Registry | 8.4 GB storage | $0.85/month |
| Secret Manager | 2 secrets | Free tier |
| Static IP | 1 address | Free (in use) |
| SSL Certificate | Google-managed | Free |
| **Total** | | **$46-58/month** |

---

## 9. Key Issues Summary

### Critical Issues (Block Production)
1. ❌ **Wrong service at www.waooaw.com** - Platform Portal serving instead of customer marketplace
2. ❌ **Missing pp.waooaw.com mapping** - Platform Portal not at correct domain
3. ❌ **OAuth broken** - Frontend has hardcoded Codespace URLs
4. ❌ **Single SSL certificate** - Only www.waooaw.com, missing 4 other domains

### High Priority Issues
5. ❌ **Missing services** - dp.waooaw.com and yk.waooaw.com not deployed
6. ❌ **No domain mappings** - All services use long *.run.app URLs
7. ❌ **Staging vs Production** - Services named "-staging" but serving production traffic
8. ⚠️ **Unknown OAuth redirect URIs** - Need to verify Google Cloud Console configuration

### Medium Priority Issues
9. ⚠️ **No monitoring** - Cost alerts, uptime checks not configured
10. ⚠️ **No runbooks** - Troubleshooting guides missing
11. ⚠️ **Build config outdated** - cloudbuild.yaml doesn't match target architecture

---

## 10. Immediate Actions Required

### Week 1: Fix Critical Issues
1. **Verify DNS** - Confirm www.waooaw.com points to 35.190.6.91
2. **Add SSL domains** - Create new cert with all 5 subdomains
3. **Fix load balancer** - Add host rules for pp, dp, yk, api
4. **Deploy correct www** - React marketplace, not Platform Portal
5. **Map pp.waooaw.com** - Point to current frontend-staging service
6. **Fix OAuth** - Update redirect URIs in Google Cloud Console

### Week 2: Add Missing Services
7. Deploy dp.waooaw.com (Development Portal)
8. Deploy yk.waooaw.com (Customer Portal)
9. Rename services (remove "-staging")
10. Test all 5 domains end-to-end

---

## 11. Discovery Commands Used

```bash
# Authentication
gcloud config list

# Networking
gcloud compute addresses list
gcloud compute url-maps list
gcloud compute url-maps describe waooaw-lb
gcloud compute backend-services list
gcloud compute forwarding-rules list
gcloud compute target-https-proxies list

# SSL
gcloud compute ssl-certificates list

# Cloud Run
gcloud run services list
gcloud run services describe waooaw-backend-staging --region us-central1
gcloud run services describe waooaw-frontend-staging --region us-central1
gcloud beta run domain-mappings list --region us-central1

# Artifact Registry
gcloud artifacts repositories list

# Secrets
gcloud secrets list
```

---

## 12. Next Steps

See [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md) for the complete 5-domain setup design.

---

*Discovery completed: January 3, 2026*  
*Discovered by: GitHub Copilot + gcloud CLI*
