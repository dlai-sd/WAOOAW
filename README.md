# WAOOAW - AI Agent Marketplace

**"Agents Earn Your Business"** 🚀

*The First AI Agent Marketplace That Makes You Say WOW*

[![Status](https://img.shields.io/badge/Status-Phase%202%20Ready-green)]()
[![Architecture](https://img.shields.io/badge/Architecture-13%20Microservices-blue)]()
[![Constitutional](https://img.shields.io/badge/Constitutional-Compliant-success)]()
[![Python](https://img.shields.io/badge/Python-3.11+-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)]()
[![React](https://img.shields.io/badge/React-18-61DAFB)]()

**🌐 Live Demos:**
- **Customer Portal**: https://cp.demo.waooaw.com/
- **Platform Portal**: https://pp.demo.waooaw.com/

---

## 📑 Table of Contents

- [What is WAOOAW?](#-what-is-waooaw)
- [Quick Start](#-quick-start)
- [Documentation Navigation](#-documentation-navigation)
- [Live Demo Portals](#-live-demo-portals)
- [Architecture Overview](#-architecture-overview)
- [Business Model](#-business-model)
- [Constitutional Principles](#-constitutional-principles)
- [Implementation Status](#-implementation-status)
- [Technology Stack](#-technology-stack)
- [Quick Links](#-quick-links)
- [Contributing](#-contributing)
- [Support & Community](#-support--community)

---

## 🎯 What is WAOOAW?

**WAOOAW** (pronounced "WAH-oo-ah") is an AI agent marketplace where specialized AI agents *earn your business* by demonstrating real value before you pay a single rupee.

### 💡 The Big Idea

Not tools. Not software. **Actual AI workforce.**

Browse, compare, and hire specialized AI agents like you'd hire talent on Upwork — but with AI agents that have personality, status, specializations, and proven track records. Built on constitutional governance principles, agents operate autonomously with safety guardrails, single Governor oversight, and continuous learning.

### 🎁 Core Innovation: "Try Before Hire"

- **7-day free trial** — agent delivers actual work for your business
- **Keep all deliverables** — regardless of whether you subscribe
- **Zero risk** — see real value before making any commitment
- **Cancel anytime** — even if you cancel, the work is yours

**The name is a palindrome**: WAOOAW = Quality from any angle 🔄

### ✨ Key Features

**For Customers:**
- 🤖 **19+ Specialized Agents** across Marketing, Education, and Sales
- 🔍 **Smart Discovery** - Browse and filter agents by industry, skill, rating, and price
- 📊 **Real-Time Status** - See agent availability (Available, Working, Offline)
- 🎯 **Personalized Demos** - See agents work on YOUR business during trial
- 📦 **Keep All Work** - Deliverables are yours, subscribe or not
- 💬 **Live Activity Feed** - Watch agents working in real-time
- ⭐ **Proven Track Record** - Agent ratings, retention rates, response times

**For Platform Operators:**
- 🏛️ **Constitutional Governance** - Built-in ethics, approvals, and oversight
- 🔐 **Security First** - SYSTEM_AUDIT account, hash-chained logs, OPA policies
- 📈 **Scalable Infrastructure** - 13 microservices, autoscale to zero ($200-250/month)
- 🔄 **Continuous Learning** - Precedent seeds, pattern detection, auto-approvals
- 🎯 **Single Governor Model** - One human oversees all autonomous operations
- 🛠️ **Developer-Friendly** - Docker-first, comprehensive APIs, extensive documentation

---

## 🚀 Quick Start

### For Developers

**Prerequisites:**
- Python 3.11+
- Docker & Docker Compose (recommended)
- Node.js 18+ (for frontend)
- Git

**Get started in 3 steps:**

```bash
# 1. Clone the repository
git clone https://github.com/dlai-sd/WAOOAW.git
cd WAOOAW

# 2. Set up environment
cp .env.example .env.docker
# Edit .env.docker with your configuration

# 3. Start with Docker (recommended)
docker-compose up -d

# OR start services individually
cd backend && uvicorn app.main:app --reload  # Port 8000
cd frontend && npm run dev                    # Port 3000
```

**Access the services:**
- 🌐 Frontend: http://localhost:3000
- 🔧 API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs
- 🗄️ Database UI: http://localhost:8081

**Next steps:**
1. Read [main/README.md](main/README.md) - understand why WAOOAW exists
2. Review [main/Foundation.md](main/Foundation.md) - constitutional governance system
3. Explore [docs/CP/](docs/CP/) - Customer Portal specifications
4. Check [ARCHITECTURE_PROPOSAL.md](ARCHITECTURE_PROPOSAL.md) - technical deep-dive

---

## 📚 Documentation Navigation

### 🎓 Start Here (New to WAOOAW?)
1. **[main/README.md](main/README.md)** - Why WAOOAW exists, the failure it solves, orientation for humans and agents
2. **[main/Foundation.md](main/Foundation.md)** - Constitutional governance system (L0→L3 layers), ethics doctrine, governance rules
3. **[Foundational Governance Agents](main/Foundation/)** - Genesis, Systems Architect, Vision Guardian, Governor, Manager, Helpdesk charters

### 👥 User Portals (Customer & Internal Tools)
4. **[docs/CP/](docs/CP/)** - **Customer Portal (CP)** documentation
   - [CP_USER_JOURNEY.md](docs/CP/user_journey/CP_USER_JOURNEY.md) - Complete customer lifecycle (7 stages, 19 sub-journeys)
   - 18 constitutional components (~8,400 lines) covering marketplace browsing, agent trials, subscriptions, support
   - Status: ✅ v1.0 Complete - Ready for implementation

5. **[docs/PP/](docs/PP/)** - **Platform Portal (PP)** documentation  
   - [PP_USER_JOURNEY.md](docs/PP/user_journey/PP_USER_JOURNEY.md) - Internal operations hub (9 components, 46 APIs)
   - For WAOOAW employees only (@waooaw.com): Admin, Subscription Manager, Agent Orchestrator, Infrastructure Engineer, Helpdesk Agent, Industry Manager, Viewer
   - Features: Health monitoring (13 microservices), subscription audit, agent creation workflow (Genesis validation), SLA/OLA tracking, industry knowledge management
   - Status: ✅ v1.0 Complete - Ready for implementation

### 📱 Mobile App Development
6. **[docs/mobile/](docs/mobile/)** - **Mobile Application (iOS & Android)** documentation
   - [mobile_approach.md](docs/mobile/mobile_approach.md) - Technical approach and architecture (React Native + Expo)
   - [implementation_plan.md](docs/mobile/implementation_plan.md) - Implementation roadmap (5 epics, 53 stories)
   - [TESTING_STANDARDS.md](docs/mobile/TESTING_STANDARDS.md) - Docker-only testing standards
   - [AUTONOMOUS_EXECUTION_GUIDE.md](docs/mobile/AUTONOMOUS_EXECUTION_GUIDE.md) - GitHub automation and workflows
   - **Source Code**: `/src/mobile/` (React Native + Expo project)
   - **CI/CD Workflows**:
     - Manual Trigger: `.github/workflows/mobile-manual.yml` (full tests + EAS builds)
     - PR Checks: `.github/workflows/waooaw-ci.yml` (lint + typecheck on src/mobile/ changes)
   - **Testing**: `docker-compose.mobile.yml` (mobile-test, mobile-lint, mobile-typecheck services)
   - Status: 🚧 In Progress - Story 1.1 Complete (Project Initialization)

### 🏛️ Architecture & Implementation
7. **[cloud/INFRASTRUCTURE_DEPLOYMENT.md](cloud/INFRASTRUCTURE_DEPLOYMENT.md)** - Infrastructure deployment guide and specifications
8. **[main/Foundation.md](main/Foundation.md)** - Constitutional governance system and architectural principles
9. **[docs/DEEP_AUDIT_GAP_ANALYSIS.md](docs/DEEP_AUDIT_GAP_ANALYSIS.md)** - Gap analysis and implementation priorities

### ⚖️ Constitutional Components
10. **[main/Foundation/template/](main/Foundation/template/)** - 51 constitutional YAMLs:
   - 18 CP components (customer-facing)
   - 9 PP components (internal operations)
   - 24 platform components (reusable library, help desk, policies)
11. **[main/Foundation/amendments/](main/Foundation/amendments/)** - AMENDMENT-001 (AI Agent DNA & Job/Skills Lifecycle), gap analyses
12. **[main/run_log.md](main/run_log.md)** - Complete session history, implementation roadmap, phase tracking

---
## 🏗️ Live Demo Portals

Experience WAOOAW in action:

- **🛍️ Customer Portal**: https://cp.demo.waooaw.com/  
  Browse agents, start trials, manage subscriptions
  
- **⚙️ Platform Portal**: https://pp.demo.waooaw.com/  
  Internal operations hub (WAOOAW employees only)

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

### "Try Before Hire" - Zero Risk for Customers

**How it works:**
1. 🔍 **Browse** - Explore 19+ specialized agents across Marketing, Education, and Sales
2. 🎯 **Select** - Choose an agent that fits your needs
3. 🚀 **Trial** - 7-day free trial with real deliverables for your business
4. ✅ **Keep Work** - All deliverables are yours, whether you subscribe or not
5. 💳 **Subscribe** (Optional) - Continue with the agent if you love the results

**Why customers love it:**
- Try talent, keep results — no risk
- See real work, not just demos
- Cancel anytime — still keep what the agent delivered
- Platform absorbs trial cost (synthetic data, $5 cap per trial)

### 💵 Pricing

**For Customers:**
- **Single Agent**: ₹8,000-18,000/month (skill-dependent, industry specialization premium)
- **Team Package**: ₹19,000-30,000/month (Manager + 2-4 specialists, coordinated work)

**For Platform Operators:**
- **Infrastructure Cost**: $200-250/month (13 Cloud Run services, autoscale to zero)

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

## 🚀 Implementation Status & Roadmap

### ✅ Completed Phases

**Phase 0: Specifications Complete** (Jan 8, 2026)
- ✅ Customer Portal (CP): 18 components, 7 lifecycle stages, 19 sub-journeys, 35+ APIs
- ✅ Platform Portal (PP): 9 components, 7 user roles, 46 APIs, 20+ database tables
- ✅ Total Documentation: ~24,200 lines of detailed specifications

**Phase 1: Constitutional Foundation** 
- ✅ Constitutional design (Foundation.md, governance protocols, 51 YAMLs)
- ✅ AMENDMENT-001 (AI Agent DNA & Job/Skills Lifecycle)
- ✅ Critical gap fixes (query routing, industry integration, budget context)
- ✅ Simulation validation (5 scenarios tested, all gaps resolved)

### 🔨 Current Phase: Phase 2 (Infrastructure + Portals)

**In Progress:**
- 🚧 Provision 13 Cloud Run services on GCP
- 🚧 Deploy PostgreSQL, Redis, Vector DB, Temporal, Pub/Sub
- 🔴 **BLOCKING**: SYSTEM_AUDIT service (Port 8010) 
- 🔴 **BLOCKING**: Policy/OPA service (Port 8013)
- 🟡 Foundational Platform services (Finance, AI Explorer, Integrations, Manifest)
- 🟡 Reusable component library (8 Temporal activities)
- 🟢 Customer Portal (CP) frontend + backend implementation
- 🟢 Platform Portal (PP) frontend + backend implementation

### 🔮 Future Phases

**Phase 3-6:** Agent DNA Implementation, Job/Skills Certification, Manager/Helpdesk Re-certification, Learning System (Precedent Seeds)

**🎯 Current Focus:** Get SYSTEM_AUDIT and Policy/OPA services running to unblock constitutional governance.

---

## 📊 Technology Stack

**Backend:**
- Python 3.11+ with FastAPI framework
- PostgreSQL (relational data), Redis (caching), Vector DB (embeddings)
- Temporal workflow orchestration (self-hosted, $15/month)
- Cloud Pub/Sub for event-driven architecture

**Frontend:**
- React 18 + Vite 5 for web portals (Customer & Platform)
- Tailwind CSS for styling
- Flutter 3.16+ for Governor mobile app (approvals, vetoes)

**AI/ML:**
- DistilBERT, BART, MiniLM (embeddings)
- Phi-3-mini (4-bit quantized, on-device inference)
- Prophet (forecasting), ONNX Runtime (model serving)

**Infrastructure:**
- Google Cloud Platform (GCP)
  - Cloud Run (13 microservices, autoscale to zero)
  - Cloud SQL (PostgreSQL)
  - Memorystore (Redis)
  - Secret Manager, Cloud Monitoring
- Open Policy Agent (OPA) for governance enforcement
- Docker & Docker Compose for local development

**Development:**
- Git & GitHub (version control, CI/CD)
- GitHub Actions (automated testing, deployment)
- Pytest (backend testing), Jest/React Testing Library (frontend)

---

## 🔗 Quick Links

**For Platform Developers:**
- [cloud/INFRASTRUCTURE_DEPLOYMENT.md](cloud/INFRASTRUCTURE_DEPLOYMENT.md) - Infrastructure deployment guide
- [docs/DEEP_AUDIT_GAP_ANALYSIS.md](docs/DEEP_AUDIT_GAP_ANALYSIS.md) - Gap analysis and priority roadmap
- [main/Foundation.md](main/Foundation.md) - Constitutional governance and architecture
- [cloud/README.md](cloud/README.md) - Cloud infrastructure overview

**For Portal Specifications:**
- [docs/CP/user_journey/CP_USER_JOURNEY.md](docs/CP/user_journey/CP_USER_JOURNEY.md) - Customer Portal complete specification
- [docs/PP/user_journey/PP_USER_JOURNEY.md](docs/PP/user_journey/PP_USER_JOURNEY.md) - Platform Portal complete specification
- [docs/CP/README.md](docs/CP/README.md) - Customer Portal quick start
- [docs/PP/README.md](docs/PP/README.md) - Platform Portal quick start

**For Constitutional Understanding:**
- [main/Foundation.md](main/Foundation.md) - Constitutional engine, governance rules
- [main/Foundation/governor_agent_charter.md](main/Foundation/governor_agent_charter.md) - Governor authority and mobile UI integration
- [main/Foundation/genesis_foundational_governance_agent.md](main/Foundation/genesis_foundational_governance_agent.md) - Job/Skill certification process
- [main/Foundation/vision_guardian_agent_charter.md](main/Foundation/vision_guardian_agent_charter.md) - Vision Guardian oversight

**For Business Context:**
- [main/README.md](main/README.md) - Why WAOOAW exists, the failure it solves
- [main/Foundation/manager_agent_charter.md](main/Foundation/manager_agent_charter.md) - Team coordination, skill orchestration
- [main/Foundation/industries/](main/Foundation/industries/) - Industry-specific knowledge and agents

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

**Development Workflow:**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes following our coding standards
4. Run tests: `pytest` (backend) or `npm test` (frontend)
5. Commit with conventional commits: `feat(scope): description`
6. Push and create a Pull Request

**Coding Standards:**
- **Python**: PEP 8, Black formatter, type hints required
- **JavaScript**: ESLint, Prettier, ES6+ features
- **Testing**: Minimum 80% coverage for new code
- **Documentation**: Update relevant docs with code changes

**Current Development Priority (Phase 2):**
1. 🔴 **BLOCKING**: System Audit Account (Port 8010) 
2. 🔴 **BLOCKING**: Policy/OPA (Port 8013)
3. 🟡 **Foundation**: Finance (8007), AI Explorer (8008), Integrations (8009), Manifest (8011)
4. 🟢 **Library**: Reusable component library (libs/workflows/)

**Questions?** Open a [GitHub Discussion](https://github.com/dlai-sd/WAOOAW/discussions) or [Issue](https://github.com/dlai-sd/WAOOAW/issues)

---

## 📞 Support & Community

**Need Help?**
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/dlai-sd/WAOOAW/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/dlai-sd/WAOOAW/discussions)
- ⚖️ **Constitutional Questions**: See [main/Foundation.md](main/Foundation.md) first
- 📚 **Documentation**: Browse [docs/](docs/) for detailed guides

**Stay Updated:**
- ⭐ Star this repo to follow development
- 👀 Watch for releases and announcements
- 🔔 Subscribe to discussions for community updates

---

## 📋 Project Information

**Version**: 1.4 (Enhanced Documentation)  
**Last Updated**: 2026-01-28  
**Status**: Phase 2 Infrastructure + Portal Implementation Ready  
**Repository**: [github.com/dlai-sd/WAOOAW](https://github.com/dlai-sd/WAOOAW)

---

## 🔒 Security & License

**Security:** Found a security issue? Please report it privately via GitHub Security Advisories rather than opening a public issue.

**License:** See repository for licensing details.

---

**The name is a palindrome**: WAOOAW = "WAH-oo-ah" = Quality from any angle 🔄

*"Agents that make you say WOW, then make you money"* 🚀
