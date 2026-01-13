# Plant Phase - Backend Journey (Genesis Production Implementation)

**Status:** ✅ Specified - Ready for Implementation  
**Phase:** Plant (Production Systems Implementation)  
**User Type:** Platform Portal (API Interactions Only - No UI)  
**Updated:** 2026-01-13

---

## Document Purpose

This document describes the **backend journey for Genesis Agent production implementation** via Platform Portal API interactions. Plant is **pure infrastructure**—no screens, only backend services accessed through PP APIs.

**Read Order:** [Foundation.md](../../../main/Foundation.md) → [PP User Journey](../../PP/user_journey/PP_USER_JOURNEY.md) → [BaseEntity](../../../main/Foundation/template/base_entity.yml) → **This Document**

---

## Architecture Context

**Plant Core Services:**
- **Genesis Webhook (Port 9001)** - Production certification service
- **Constitutional Query API (Port 8004 extension)** - Vector search + precedent seeds
- **Precedent Seed Storage** - PostgreSQL + vector embeddings (MiniLM-384)
- **Audit Trail** - Append-only logs with SHA-256 hash chains
- **Health Metrics (Port 8019)** - Genesis-specific observability

**Inheritance Model:**
- All entities (Agent, Skill, JobRole, Team, Industry) inherit from **BaseEntity**
- Universal: identity, lifecycle, versioning, audit, constitutional alignment
- Genesis validates BaseEntity compliance before certification

---

[Content continues in next file creation...]
## Self-Answered Constitutional Questions

**Q1:** Can Platform Admin override Genesis certification rejection?  
**A1:** No - Genesis authority is constitutionally protected (L1 governance). Admin can escalate to Vision Guardian for ethics review, but cannot directly override.

**Q2:** How does precedent seed supersession preserve audit trail?  
**A2:** Immutable append-only logs with SHA-256 hash chains. Supersession creates new seed with superseded_by reference, marks old as "superseded", never deletes. Traceability preserved.

**Q3:** What happens if Genesis detects constitutional drift?  
**A3:** Vision Guardian daily audit calculates L0 hash. On mismatch: agents suspended (active → under_review), Governor notified for re-certification approval. Agents cannot operate with outdated constitution.

**Q4:** Can customers skip industry embeddings to save cost?  
**A4:** Yes - Governor has 3 options: (A) Approve $20 emergency budget, (B) Reject request, (C) Certify without embeddings → Week 4 productivity (₹8K pricing not ₹12K). Transparency over profit.

**Q5:** Who can terminate Genesis webhook?  
**A5:** Systems Architect: architectural issues (DLQ overflow). Vision Guardian: constitutional violations detected. Governor: permanent decommission. No single point of failure.

**Q6:** How are precedent contradictions prevented?  
**A6:** Vision Guardian audits precedent quality before activation. Vector search checks cosine similarity >0.9 for potential contradiction. Escalates to Governor for resolution.

**Q7:** What if Genesis becomes unavailable?  
**A7:** PP queues certification requests in Pub/Sub (TTL: 24 hours). Health Aggregator alerts Systems Architect. Agents continue with cached precedents. No bypass allowed.

**Q8:** Can Genesis certification be batched?  
**A8:** Yes - `/certify/batch` endpoint (max 50 requests). L0 validation per entity. Audit log records each individually. Performance cannot compromise auditability.

---

## Gap Analysis Summary

**Total Gaps:** 12 identified

**Critical (3):**
- GAP-PLANT-1: Genesis webhook authentication (service account vs OAuth)
- GAP-PLANT-4: Vector DB cold start latency (>500ms first query)
- GAP-PLANT-7: Constitutional drift detection frequency (daily vs real-time)

**High Priority (4):**
- GAP-PLANT-2: Precedent cache invalidation (TTL vs event-driven)
- GAP-PLANT-5: Genesis horizontal scaling (stateless certification)
- GAP-PLANT-8: Audit log hash chain repair procedure
- GAP-PLANT-9: DLQ retention policy

**Medium (5):**
- GAP-PLANT-3: Vector DB provider selection
- GAP-PLANT-10: Precedent seed versioning (breaking vs non-breaking)
- GAP-PLANT-11: Genesis self-test frequency
- GAP-PLANT-12: Helpdesk escalation SLA

**Resolution Strategy:**
- Critical: Resolve before Plant deployment (week 1)
- High priority: Resolve during implementation (week 2-3)
- Medium: Defer to Plant v1.1

---

## Related Documents

- [Foundation.md](../../../main/Foundation.md) - Constitutional principles (L0/L1)
- [BaseEntity](../../../main/Foundation/template/base_entity.yml) - Universal root entity
- [Base Agent Anatomy](../../../main/Foundation/template/base_agent_anatomy.yml) - Agent PCB model
- [Genesis Charter](../../../main/Foundation/genesis_foundational_governance_agent.md)
- [Systems Architect Charter](../../../main/Foundation/systems_architect_foundational_governance_agent.md)
- [Vision Guardian Charter](../../../main/Foundation/vision_guardian_foundational_governance_agent.md)
- [PP User Journey](../../PP/user_journey/PP_USER_JOURNEY.md) - Platform Portal v1.0
- [Constitutional Query API](../../../main/Foundation/template/component_constitutional_query_api.yml)

---

**Last Updated:** 2026-01-13  
**Status:** ✅ Specified - Ready for Implementation
