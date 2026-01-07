# WAOOAW Documentation Structure
**Last Updated:** 2026-01-07  
**Purpose:** Organized documentation for all portals and user journeys

---

## 📁 Directory Structure

```
docs/
├── CP/              Customer Portal (Visitor + Customer personas)
│   └── user_journey/   CP User Journey specification (v0.5)
│       ├── CP_USER_JOURNEY.md (human-readable documentation)
│       └── CP_USER_JOURNEY.yaml (machine-readable API contracts)
│
└── PP/              Platform Portal (Platform Governor, Systems Architect, Genesis)
    └── (Coming soon: Platform user journeys, governance workflows)
```

---

## 🎯 Portal Overview

### **CP (Customer Portal)**
**Personas:** Visitor (anonymous), Customer (authenticated)  
**Primary Functions:**
- Marketplace discovery (browse agents/teams)
- Trial registration (7-day free, no credit card)
- Agent setup wizard (goals, access, criteria)
- Operations monitoring (approvals, performance)
- Subscription management (upgrades, version upgrades)

**Status:** ✅ User Journey v0.5 (draft, pending approval)  
**Location:** [docs/CP/user_journey/](CP/user_journey/)

---

### **PP (Platform Portal)**
**Personas:** Platform Governor, Systems Architect, Genesis, Vision Guardian  
**Primary Functions:**
- Constitutional compliance monitoring
- Agent lifecycle management (certification, deployment)
- Financial operations (MRR/ARR, cost tracking)
- Marketplace administration (job catalog, skill registry)
- System operations dashboard (13 microservices health)

**Status:** 🟡 Pending user journey definition  
**Location:** [docs/PP/](PP/)

---

## 📋 Document Conventions

### **User Journey Documents**
Each portal should have:
1. **{PORTAL}_USER_JOURNEY.md** - Human-readable documentation
   - Personas, lifecycle stages, UI/UX details
   - Wireframe descriptions, user actions
   - Gap analysis with solutions
   
2. **{PORTAL}_USER_JOURNEY.yaml** - Machine-readable specification
   - API contracts (endpoints, services, auth)
   - Data schemas, validation rules
   - Constitutional alignment references

3. **Version Synchronization:** MD and YAML files must share same version number and be updated together

---

## 🔗 Cross-References

**Project Root:**
- [README.md](../README.md) - Project overview
- [ARCHITECTURE_PROPOSAL.md](../ARCHITECTURE_PROPOSAL.md) - 13 microservices technical specification
- [ARCHITECTURE_COMPLIANCE_AUDIT.md](../ARCHITECTURE_COMPLIANCE_AUDIT.md) - Gap analysis

**Constitutional Design:**
- [main/Foundation.md](../main/Foundation.md) - Constitutional governance system
- [main/Foundation/template/](../main/Foundation/template/) - 42 constitutional component YAMLs

**Infrastructure:**
- [cloud/](../cloud/) - GCP deployment (Terraform, Cloud Run)
- [infrastructure/](../infrastructure/) - Docker, monitoring, backup

---

## 📝 Change Log

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-01-07 | Initial docs/ structure created (CP/AP/PP folders) |
| 0.1 | 2026-01-07 | CP User Journey v0.5 moved to docs/CP/user_journey/ |

---

**Next Steps:**
1. Define AP (Admin Portal) user journeys
2. Define PP (Platform Portal) user journeys
3. Create constitutional component YAMLs for 9 identified gaps (GAP-UJ-1 through GAP-UJ-9)
