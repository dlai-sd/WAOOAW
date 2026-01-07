# WAOOAW - AI Agent Marketplace with Constitutional Governance

**Ways of Working for the Autonomous World**

[![Status](https://img.shields.io/badge/Status-Phase%202%20Ready-green)]()
[![Architecture](https://img.shields.io/badge/Architecture-13%20Microservices-blue)]()
[![Constitutional](https://img.shields.io/badge/Constitutional-Compliant-success)]()

---

## 🎯 What is WAOOAW?

WAOOAW is an AI agent marketplace where specialized AI agents earn business by demonstrating value before payment. Built on constitutional governance principles, agents operate autonomously with safety guardrails, single Governor oversight, and learning feedback loops.

**Core Innovation**: "Try Before Hire" model - 7-day free trials where customers keep deliverables regardless of subscription decision.

---

## 📚 Documentation Structure

### Start Here
1. **[main/README.md](main/README.md)** - Why WAOOAW exists, the failure it solves, orientation for humans and agents
2. **[main/Foundation.md](main/Foundation.md)** - Constitutional governance system (L0→L3 layers), ethics doctrine, governance rules
3. **[Foundational Governance Agents](main/Foundation/)** - Genesis, Systems Architect, Vision Guardian, Governor, Manager, Helpdesk charters

### Architecture & Implementation
4. **[ARCHITECTURE_PROPOSAL.md](ARCHITECTURE_PROPOSAL.md)** - 13 microservices technical specification, repository structure, CI/CD, cost breakdown
5. **[ARCHITECTURE_COMPLIANCE_AUDIT.md](ARCHITECTURE_COMPLIANCE_AUDIT.md)** - Gap analysis, constitutional component mapping, implementation priority
6. **[REACT_FASTAPI_CLOUD_RUN_RESEARCH.md](REACT_FASTAPI_CLOUD_RUN_RESEARCH.md)** - React + FastAPI deployment research for Customer/Platform Portals

### Constitutional Components
7. **[main/Foundation/template/](main/Foundation/template/)** - 42 constitutional YAMLs (platform components, reusable library, help desk, policies)
8. **[main/Foundation/amendments/](main/Foundation/amendments/)** - AMENDMENT-001 (AI Agent DNA & Job/Skills Lifecycle), gap analyses
9. **[main/run_log.md](main/run_log.md)** - Complete session history, implementation roadmap, phase tracking

---

## 🏗️ Architecture Overview

### 13 Microservices (Constitutional Compliance: 100%)

**Foundational Platform (4):**
- **Finance (8007)** - Subscription tracking, MRR/ARR, cost monitoring, discount policies, budget alerts
- **AI Explorer (8008)** - Prompt templates, injection detection, token tracking, response caching
- **Integrations (8009)** - CRM/payment/communication connectors, sandbox routing, credential management
- **Audit (8010)** - CRITICAL - SYSTEM_AUDIT privileged account, hash-chained logs, breaks circular dependency

**Core Agent Services (6):**
- **Agent Creation (8001)** - 7-stage Temporal pipeline (Genesis→Architect→Ethics→Governor→Deploy)
- **Agent Execution (8002)** - Think→Act→Observe, skill orchestration, ML inference
- **Governance (8003)** - Approvals, precedent seeds, vetoes, business rules, mobile API
- **Industry Knowledge (8004)** - Vector DB queries, constitutional + industry embeddings
- **Learning (8005)** - Pattern detection, precedent seed generation
- **Admin Gateway (8006)** - Health, metrics, auth, rate limiting

**Support Services (3):**
- **Manifest (8011)** - Versioned capability registry, diff/classify API
- **Help Desk (8012)** - Intake, triage, escalation, handoff packets (HDP-1.0)
- **Policy/OPA (8013)** - CRITICAL - Trial mode enforcement, PDP/PEP, attested decisions

**Reusable Components:** 8 Temporal activities (Genesis cert, Governor approval, Architecture/Ethics reviews, Health check, Rollback, Versioning, Audit logging)

---

## 💰 Business Model

**Try Before Hire (7-Day Free Trial):**
- Customer browses marketplace → starts trial → agent delivers work → customer keeps deliverables
- Platform absorbs trial cost ($5 cap, synthetic data, sandbox routing)
- After 7 days: Subscribe (₹8K-30K/month) | Extend trial | Cancel (keep work, no payment)

**Pricing Tiers:**
- Single Agent: ₹8,000-18,000/month (skill-dependent, industry specialization premium)
- Team: ₹19,000-30,000/month (Manager + 2-4 specialists, coordinated work)

**Platform Costs:** $200-250/month (13 services on GCP Cloud Run, autoscale to zero)

---

## 🔑 Constitutional Principles

**Single Governor Invariant:**
- One Platform Governor session (you) approves external execution, emergency budgets, job pricing
- Vision Guardian has break-glass override authority (Governor ethics violations)

**Agent DNA (AMENDMENT-001):**
- **Specialization**: Agents are Jobs (specialized workforces), not generalized assistants
- **Skill Atomicity**: Skills are atomic units with Think→Act→Observe cycles
- **Memory Persistence**: Filesystem-persistent, append-only (agents/{id}/state/)
- **Constitutional Embodiment**: Vector embeddings, semantic search, RAG-driven decisions

**Ethics is Structural:**
- 4-level graduated escalation (auto-block, escalate to Vision Guardian, allow with disclaimer, log only)
- Mandatory gates (communication, execution) with trace link requirements
- Precedent seeds capture learning from Governor decisions (auto-approval with 24hr veto window)

**Circular Dependency Resolution:**
- Agent execution requires audit → Audit requires approval → Approval requires audit → **INFINITE LOOP**
- Solution: SYSTEM_AUDIT privileged account with governance exemption (Port 8010)
- Vision Guardian monitors SYSTEM_AUDIT behavior (deviation = constitutional crisis)

---

## 🚀 Implementation Status

**Phase 1: Complete ✅**
- Constitutional design (Foundation.md, governance protocols, 42 YAMLs)
- AMENDMENT-001 (AI Agent DNA & Job/Skills Lifecycle)
- Critical gap fixes (query routing, industry integration, budget context, auto-approval oversight)
- Simulation validation (5 scenarios tested, gaps resolved)

**Phase 2: Ready to Start (2026-01-11)**
- Infrastructure: Provision 13 Cloud Run services, PostgreSQL, Redis, Vector DB, Temporal, Pub/Sub
- Implement SYSTEM_AUDIT (Port 8010) and Policy/OPA (Port 8013) - **BLOCKING** for constitutional governance
- Deploy Foundational Platform services (Finance, AI Explorer, Integrations, Manifest)
- Build reusable component library (8 Temporal activities)

**Phase 3-6:** Agent DNA, Job/Skills certification, Re-certification (Manager/Helpdesk), Learning (Precedent Seeds)

---

## 📊 Technology Stack

- **Backend**: Python 3.11+, FastAPI, PostgreSQL, Redis, Temporal, Cloud Pub/Sub
- **Frontend**: React 18 + Vite 5 (Customer/Platform Portals), Tailwind CSS
- **Mobile**: Flutter 3.16+ (Governor App - approvals, vetoes, precedent seeds)
- **ML/AI**: DistilBERT, BART, MiniLM, Phi-3-mini (4-bit), Prophet, ONNX Runtime
- **Infrastructure**: GCP Cloud Run, Cloud SQL, Memorystore, Secret Manager, Cloud Monitoring
- **Policy**: Open Policy Agent (OPA) for trial mode enforcement, sandbox routing
- **Orchestration**: Temporal (self-hosted on Cloud Run, $15/month)

---

## 🔗 Quick Links

**For Platform Developers:**
- [ARCHITECTURE_PROPOSAL.md](ARCHITECTURE_PROPOSAL.md) - Full technical specification
- [ARCHITECTURE_COMPLIANCE_AUDIT.md](ARCHITECTURE_COMPLIANCE_AUDIT.md) - Gap analysis, priority roadmap
- [main/Foundation/TOOLING_SELECTION_DECISION.md](main/Foundation/TOOLING_SELECTION_DECISION.md) - Technology decisions

**For Constitutional Understanding:**
- [main/Foundation.md](main/Foundation.md) - Constitutional engine, governance rules
- [main/Foundation/governor_agent_charter.md](main/Foundation/governor_agent_charter.md) - Governor authority, mobile UI integration
- [main/Foundation/genesis_foundational_governance_agent.md](main/Foundation/genesis_foundational_governance_agent.md) - Job/Skill certification

**For Business Context:**
- [main/README.md](main/README.md) - Why WAOOAW exists, the failure it solves
- [main/Foundation/industry_component_architecture.md](main/Foundation/industry_component_architecture.md) - Day 1 domain expertise, pricing tiers
- [main/Foundation/manager_agent_charter.md](main/Foundation/manager_agent_charter.md) - Team coordination, skill orchestration

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow, coding standards, and PR guidelines.

**Critical Path (Phase 2):**
1. System Audit Account (Port 8010) - BLOCKING
2. Policy/OPA (Port 8013) - BLOCKING
3. Finance (Port 8007), AI Explorer (Port 8008), Integrations (Port 8009), Manifest (Port 8011)
4. Reusable component library (libs/workflows/)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/dlai-sd/WAOOAW/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dlai-sd/WAOOAW/discussions)
- **Constitutional Questions**: See [main/Foundation.md](main/Foundation.md) first

---

**Version**: 1.2 (Post-AMENDMENT-001)  
**Last Updated**: 2026-01-07  
**Status**: Phase 2 Infrastructure Ready  
**License**: [LICENSE](LICENSE)

**The name is a palindrome**: WAOOAW = "WAH-oo-ah" = quality from any angle 🔄
