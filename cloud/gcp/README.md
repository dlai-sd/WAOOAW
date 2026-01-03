# WAOOAW GCP Infrastructure

Complete documentation and configuration for WAOOAW platform on Google Cloud Platform.

## Quick Facts

| Property | Value |
|----------|-------|
| **GCP Project** | waooaw-oauth (270293855600) |
| **Primary Region** | us-central1 |
| **Load Balancer IP** | 35.190.6.91 |
| **DNS Domain** | waooaw.com |
| **Active Services** | 2 (backend-staging, frontend-staging) |
| **Target Services** | 5 (www, pp, dp, yk, api) |

## Current Infrastructure Status

✅ **Deployed:**
- Load Balancer (`waooaw-lb`) - routing www.waooaw.com
- Backend API (`waooaw-backend-staging`) - staging environment
- Frontend (`waooaw-frontend-staging`) - Reflex Platform Portal
- SSL Certificate (`waooaw-ssl-cert`) - www.waooaw.com (ACTIVE)
- Static IP (`waooaw-lb-ip`) - 35.190.6.91
- Artifact Registry (`waooaw-containers`) - 8.4 GB
- OAuth Secrets (google-client-id, google-client-secret)

🚧 **Pending:**
- pp.waooaw.com domain mapping
- dp.waooaw.com domain mapping and service
- yk.waooaw.com domain mapping and service
- Multi-domain SSL certificate
- OAuth redirect URI updates
- Load balancer host rules for 5 domains

## Directory Structure

```
/cloud/gcp/
├── README.md                    (this file)
├── CURRENT_STATE.md            (infrastructure inventory)
├── TARGET_ARCHITECTURE.md      (5-domain setup design)
│
├── architecture/               (diagrams and design docs)
│   ├── load-balancer-design.md
│   ├── multi-domain-routing.md
│   └── network-flow.md
│
├── load-balancer/             (LB configuration)
│   ├── url-map-config.yaml
│   ├── backend-services.yaml
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
