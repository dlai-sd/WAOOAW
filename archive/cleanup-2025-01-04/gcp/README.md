# WAOOAW GCP Infrastructure

Complete documentation and configuration for WAOOAW platform on Google Cloud Platform.

## Quick Facts

| Property | Value |
|----------|-------|
| **GCP Project** | waooaw-oauth (270293855600) |
| **Primary Region** | asia-south1 (Mumbai) |
| **DNS Domain** | waooaw.com |
| **Active Environments** | demo (3 services deployed) |
| **Target Environments** | demo, uat, production |

## Current Infrastructure Status (v2 Architecture)

✅ **Demo Environment Deployed:**
- Backend API (`waooaw-api-demo`) - FastAPI with mock data
- Customer Portal (`waooaw-portal-demo`) - React marketplace
- Platform Portal (`waooaw-platform-portal-demo`) - Reflex admin portal
- OAuth Secrets in Secret Manager (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, JWT_SECRET)
- GitHub Actions CI/CD pipeline with smoke tests
- Cost: ~$35-40/month (scale-to-zero enabled)

🚧 **Pending:**
- Custom domain mapping (demo-*.waooaw.com)
- DNS CNAME records configuration
- OAuth Console custom domain setup
- UAT environment deployment
- Production environment deployment

## Directory Structure

```
/cloud/gcp/
├── README.md                    (this file)
├── CURRENT_STATE.md            (v2 infrastructure inventory)
├── TARGET_ARCHITECTURE.md      (3-environment setup design)
│
├── deployment/                 (deployment scripts and configs)
│   ├── deploy-phase1.sh       (legacy production deployment)
│   └── cloud-run-config.yaml  (Cloud Run service manifests)
│
├── oauth/                     (OAuth configuration)
│   └── google-oauth-config.md
│
├── monitoring/                (monitoring and cost tracking)
│   └── cost-tracking.md
│
└── runbooks/                  (operational procedures)
    ├── oauth-issues.md
    └── scaling-guide.md
```

## Quick Links

### Deployment
- [Custom Domain Setup](../../infrastructure/gcp/deploy.sh) - Automated domain mapping script
- [Domain Configuration Docs](../../docs/infrastructure/custom-domains.md)
- [GitHub Actions Workflows](../../.github/workflows/)

### Infrastructure Management
```bash
# Setup custom domains for demo
cd /workspaces/WAOOAW/infrastructure/gcp
./deploy.sh demo

# Check domain mappings
gcloud run domain-mappings list --region=asia-south1

# View service URLs
gcloud run services list --region=asia-south1
```
│   └── ssl-certificates.yaml
│
├── cloud-run/                 (service definitions)
│   ├── www-waooaw/
│   ├── pp-waooaw/
│   ├── dp-waooaw/
│   ├── yk-waooaw/
│   └── api-waooaw/
│
├── networking/                (DNS, SSL, domains)
│   ├── domain-setup.md
│   ├── ssl-certificate-config.md
│   └── firewall-rules.md
│
├── oauth/                     (authentication setup)
│   ├── google-oauth-config.md
│   ├── redirect-uris.md
│   └── secrets-management.md
│
├── deployment/                (CI/CD and scripts)
│   ├── deploy-all.sh
│   ├── deploy-single-service.sh
│   ├── rollback.sh
│   └── cloudbuild-multi-service.yaml
│
├── monitoring/                (observability)
│   ├── cost-tracking.md
│   ├── alerts-setup.md
│   └── dashboard-config.yaml
│
└── runbooks/                  (operations guides)
    ├── troubleshooting.md
    ├── oauth-issues.md
    ├── ssl-renewal.md
    └── scaling-guide.md
```

## Quick Links

### Current Infrastructure
- [Current State Inventory](CURRENT_STATE.md) - What's deployed now
- [Infrastructure Discovery Commands](runbooks/discovery-commands.md)

### Target Architecture
- [Target Architecture Overview](TARGET_ARCHITECTURE.md) - 5-domain setup
- [Load Balancer Design](architecture/load-balancer-design.md)
- [Multi-Domain Routing](architecture/multi-domain-routing.md)

### Implementation Guides
- [Step-by-Step Deployment](deployment/DEPLOYMENT_GUIDE.md)
- [OAuth Configuration](oauth/google-oauth-config.md)
- [SSL Certificate Setup](networking/ssl-certificate-config.md)

### Operations
- [Troubleshooting OAuth](runbooks/oauth-issues.md)
- [Cost Monitoring](monitoring/cost-tracking.md)
- [Scaling Services](runbooks/scaling-guide.md)

## Implementation Priority

Based on business requirements:

### Phase 1: Fix Current Issues (Week 1)
1. ✅ Document current state
2. 🔧 Fix OAuth redirect URIs
3. 🔧 Update load balancer for pp.waooaw.com
4. 🔧 Test www.waooaw.com → api.waooaw.com routing

### Phase 2: Add Internal Portals (Week 2)
1. 📋 Deploy dp.waooaw.com (Development Portal)
2. 📋 Configure SSL for all 5 domains
3. 📋 Update load balancer host rules
4. 📋 Test multi-domain routing

### Phase 3: Customer Portals (Week 3)
1. 📋 Deploy yk.waooaw.com (customer portal template)
2. 📋 Configure customer-specific routing
3. 📋 Test end-to-end OAuth flow
4. 📋 Performance optimization

### Phase 4: Monitoring & Optimization (Week 4)
1. 📋 Set up cost alerts
2. 📋 Configure uptime monitoring
3. 📋 Performance tuning
4. 📋 Documentation finalization

## Cost Tracking

**Current Monthly Cost:** ~$45-60/month
- Backend API: $12-15
- Frontend (Platform Portal): $18-22
- Load Balancer: $15-20
- Artifact Registry: Free tier
- Secret Manager: Free tier

**Target Monthly Cost (5 services):** $85-130/month (within $150 policy limit)

See [Cost Monitoring Guide](monitoring/cost-tracking.md) for details.

## Support

**Infrastructure Owner:** Platform Architecture Team  
**GCP Admin:** yogeshkhandge@gmail.com  
**Policy Reference:** [Tech Stack Selection Policy](/policy/TECH_STACK_SELECTION_POLICY.md)

---

*Last updated: January 3, 2026*
