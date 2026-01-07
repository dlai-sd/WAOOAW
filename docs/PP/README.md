# Platform Portal (PP) Documentation
**Version:** TBD  
**Last Updated:** 2026-01-07  
**Status:** Pending User Journey Definition

---

## 📖 Overview

The **Platform Portal (PP)** serves foundational governance agents and platform operators with system-wide visibility and control.

---

## 🎯 Personas

1. **Platform Governor** - Human oversight, approval authority, constitutional decisions
2. **Systems Architect** - Infrastructure design, deployment management, capacity planning
3. **Genesis** - Agent certification, Job/Skill validation, marketplace curation
4. **Vision Guardian** - Constitutional compliance, ethics oversight, incident escalation
5. **Platform Operations Team** - Monitoring, incident response, system health

---

## 🔧 Platform Portal Features (High-Level)

### **5 Core Modules** (from earlier analysis)

1. **System Operations Dashboard**
   - 13 microservices health monitoring
   - Cloud Run autoscale metrics (requests/sec, latency, error rate)
   - PostgreSQL query performance, Redis cache hit rates
   - Real-time alerts (service down, high latency, cost spike)
   - Incident timeline (active incidents, resolution status)

2. **Financial Operations Center**
   - MRR/ARR tracking (monthly recurring revenue trends)
   - Cost monitoring (GCP spend by service, budget alerts)
   - Monthly reporting pack (starting MRR, new MRR, churned MRR, variance)
   - Trial cost absorption tracking (platform subsidizes $5/agent)
   - Revenue forecasting (Prophet ML model)

3. **Agent Lifecycle Management**
   - Job/Skill catalog administration (certified jobs registry)
   - 7-stage Genesis certification pipeline (review, approval, deployment)
   - Agent versioning (v1.0 → v2.0 release management)
   - Marketplace curation (feature agents, hide deprecated)
   - Customer analytics (agent usage, satisfaction scores)

4. **Constitutional Compliance Monitor**
   - Precedent seeds dashboard (auto-approvals, veto tracking)
   - Audit verification (SYSTEM_AUDIT log integrity checks)
   - Policy metrics (trial mode violations, governance gate failures)
   - Ethics incident review (ETH-UNCLEAR escalations, resolution time)
   - Vision Guardian escalation queue

5. **Marketplace Administration**
   - Job curation (approve new Jobs for marketplace)
   - Skill registry management (add/update Skills)
   - Customer analytics (trial conversion rates, churn analysis)
   - Agent performance benchmarks (platform-wide quality scores)
   - Pricing optimization (discount analytics, proration reports)

---

## 📂 Documentation Structure

```
PP/
└── README.md (this file - placeholder)
```

**Coming soon:**
- PP_USER_JOURNEY.md
- PP_USER_JOURNEY.yaml
- Module specifications (5 modules detailed)
- Wireframes and user flows

---

## 🔌 API Dependencies

**Platform Portal will interact with:**
- All 13 microservices (system-wide visibility)
- Audit Service (8010) - audit logs, compliance reports
- Finance Service (8007) - MRR/ARR, cost tracking
- Manifest Service (8011) - Job/Skill catalog, agent versioning
- Governance Service (8003) - precedent seeds, approval metrics
- Policy Service (8013) - trial mode violations, policy enforcement stats
- Learning Service (8005) - platform-wide patterns, benchmarks

---

## 📋 Next Steps

1. ✅ High-level module structure defined (5 modules)
2. ⏳ **Create PP user journey specification** (similar to CP)
3. ⏳ Define API contracts for each module
4. ⏳ Design admin dashboard UI/UX (web-only, desktop-optimized)
5. ⏳ Map PP workflows to constitutional components

---

## 🔗 Related Documentation

**Constitutional Design:**
- [main/Foundation.md](../../main/Foundation.md) - Governance system
- [main/Foundation/genesis_foundational_governance_agent.md](../../main/Foundation/genesis_foundational_governance_agent.md) - Genesis certification
- [main/Foundation/vision_guardian_foundational_governance_agent.md](../../main/Foundation/vision_guardian_foundational_governance_agent.md) - Vision Guardian ethics
- [main/Foundation/governor_agent_charter.md](../../main/Foundation/governor_agent_charter.md) - Platform Governor authority

**Architecture:**
- [ARCHITECTURE_PROPOSAL.md](../../ARCHITECTURE_PROPOSAL.md) - 13 microservices
- [cloud/](../../cloud/) - GCP infrastructure

---

**Status:** 🟡 **Pending User Journey Definition**
