# Customer Portal (CP) Documentation
**Version:** 0.5 (Draft)  
**Last Updated:** 2026-01-07  
**Status:** Pending Approval

---

## 📖 Overview

The **Customer Portal (CP)** serves two distinct user personas across the complete customer lifecycle:

1. **Visitor** (Pre-registration) - Anonymous marketplace browsing, agent evaluation, trial start
2. **Customer** (Post-registration) - Active agent management, performance monitoring, subscription control

---

## 📂 Documentation Structure

```
CP/
├── README.md (this file)
└── user_journey/
    ├── CP_USER_JOURNEY.md (human-readable)
    └── CP_USER_JOURNEY.yaml (machine-readable)
```

---

## 🎯 CP Features

### **7 Lifecycle Stages**
1. **Discovery & Evaluation** (Visitor) - Browse marketplace, view agent details
2. **Hire Decision & Registration** (Visitor→Customer) - Start trial, onboarding
3. **Goal Configuration** (Customer) - Define goals, configure settings
4. **Agent/Team Setup Wizard** (Customer) - Business context, access, criteria, conformity
5. **Go-Live Declaration** (Customer) - Activate production (real data, real integrations)
6. **Operations & Monitoring** (Customer) - Approve actions, monitor performance, reconfigure
7. **Subscription Management** (Customer) - Trial conversion, plan upgrades, version upgrades

### **19 Sub-Journeys**
- S1.1: Browse Marketplace
- S1.2: Evaluate Agent Details
- S2.1: Start Trial
- S2.2: Onboarding Flow
- S3.1: Define Goals
- S3.2: Configure Settings
- S4.1: Complete Setup Wizard
- S4.2: Setup Adjustments
- S5.1: Go-Live Activation
- S6.1: Monitor Actions & Performance
- S6.2: Approve/Deny Agent Actions
- S6.3: Reconfigure Settings
- S6.4: Interrupt Agent
- S6.5: View Usage & Billing
- S6.6: Review Past Performance (Gamification)
- S7.1: Trial-to-Paid Conversion
- S7.2: Subscription Upgrades/Downgrades
- S7.3: Agent Version Upgrades

---

## 🔌 API Contracts

**35+ Endpoints Across 8 Microservices:**

- **Manifest Service (8011):** Marketplace discovery, agent catalog, version tracking
- **Finance Service (8007):** Trial subscriptions, billing, usage tracking, plan limits
- **Agent Creation Service (8001):** Agent provisioning, setup wizard, version upgrades
- **Agent Execution Service (8002):** Activity monitoring, sample generation, interrupt/resume
- **Governance Service (8003):** Approval decisions, settings management
- **Policy Service (8013):** Trial mode enforcement, go-live activation
- **Audit Service (8010):** Setup approvals, go-live attestation, event logging
- **Learning Service (8005):** Gamification badges, milestones, analytics

**Full API specification:** See [user_journey/CP_USER_JOURNEY.yaml](user_journey/CP_USER_JOURNEY.yaml)

---

## 🚨 Identified Gaps → ✅ RESOLVED

**All 9 Critical Gaps RESOLVED** with constitutional component YAMLs created:

| Gap ID | Component | Status | Solution File |
|--------|-----------|--------|---------------|
| GAP-UJ-1 | Marketplace Discovery | ✅ **RESOLVED** | [component_marketplace_discovery.yml](../../main/Foundation/template/component_marketplace_discovery.yml) |
| GAP-UJ-2 | Customer Authentication | ✅ **RESOLVED** | [component_customer_authentication.yml](../../main/Foundation/template/component_customer_authentication.yml) |
| GAP-UJ-3 | Agent Setup Wizard | ✅ **RESOLVED** | [component_agent_setup_wizard.yml](../../main/Foundation/template/component_agent_setup_wizard.yml) |
| GAP-UJ-4 | Go-Live Approval Gate | ✅ **RESOLVED** | Extended [governance_protocols.yaml](../../main/Foundation/template/governance_protocols.yaml) |
| GAP-UJ-5 | Customer Interrupt Protocol | ✅ **RESOLVED** | [component_customer_interrupt_protocol.yml](../../main/Foundation/template/component_customer_interrupt_protocol.yml) |
| GAP-UJ-6 | Subscription Plan Limits | ✅ **RESOLVED** | Extended [financials.yml](../../main/Foundation/template/financials.yml) |
| GAP-UJ-7 | Agent Version Upgrades | ✅ **RESOLVED** | [component_agent_version_upgrade_workflow.yml](../../main/Foundation/template/component_agent_version_upgrade_workflow.yml) |
| GAP-UJ-8 | Gamification Engine | ✅ **RESOLVED** | [component_gamification_engine.yml](../../main/Foundation/template/component_gamification_engine.yml) |
| GAP-UJ-9 | Trial Conversion Workflow | ✅ **RESOLVED** | Extended [financials.yml](../../main/Foundation/template/financials.yml) |

**Implementation Status:**
- 🎯 **6 New Components Created** (Marketplace Discovery, Customer Auth, Setup Wizard, Interrupt Protocol, Version Upgrades, Gamification)
- 🎯 **2 Existing Components Extended** (governance_protocols.yaml with go-live gate, financials.yml with plan limits + trial conversion)
- 🎯 **All Gaps Have Solutions** ready for implementation phase

---

## ✅ Success Metrics

- **Visitor→Trial Conversion:** >40% (4 in 10 start trial)
- **Onboarding Completion:** >80% (8 in 10 complete wizard)
- **Setup Wizard Pass:** >70% (7 in 10 pass first time)
- **Approval Latency:** <5 minutes median
- **Trial→Paid Conversion:** >50% (5 in 10 subscribe)

---

## 📋 Document Versioning

| Document | Version | Status | Last Updated |
|----------|---------|--------|--------------|
| CP_USER_JOURNEY.md | 0.5 | Draft | 2026-01-07 |
| CP_USER_JOURNEY.yaml | 0.5 | Draft | 2026-01-07 |

**Version synchronization:** Both MD and YAML files must be updated together.

---

## 🔗 Related Documentation

**Constitutional Design:**
- [main/Foundation.md](../../main/Foundation.md) - Governance system
- [main/Foundation/template/](../../main/Foundation/template/) - 42 component YAMLs
- [main/Foundation/governor_agent_charter.md](../../main/Foundation/governor_agent_charter.md) - Approval authority
- [main/Foundation/policies/mobile_ux_requirements.yml](../../main/Foundation/policies/mobile_ux_requirements.yml) - Mobile app MVP

**Architecture:**
- [ARCHITECTURE_PROPOSAL.md](../../ARCHITECTURE_PROPOSAL.md) - 13 microservices
- [ARCHITECTURE_COMPLIANCE_AUDIT.md](../../ARCHITECTURE_COMPLIANCE_AUDIT.md) - Gap analysis

---

**Status:** 🟡 **Draft - Pending User Approval**
