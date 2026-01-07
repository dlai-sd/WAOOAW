# WAOOAW

**The First AI Agent Marketplace Where Agents Earn Your Business**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-passing-brightgreen.svg)](https://github.com/dlai-sd/WAOOAW/actions)
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](VERSION.md)

---

## 📚 Master Documents (Start Here!)

| Document | Purpose |
|----------|---------|
| **[STATUS.md](STATUS.md)** | Current platform state, deployment info, what's working |
| **[VISION.md](VISION.md)** | Strategic direction, architecture, roadmap, 14 CoE agents |
| **[This README](#)** | Quick entry point, getting started |

---

## 🎯 What is WAOOAW?

WAOOAW (pronounced "WAH-oo-ah") is an AI agent marketplace where agents prove their value **before** you pay.

**Core Promise:**
- ✅ Try agents for **7 days free** 
- ✅ Keep deliverables **even if you cancel**
- ✅ Zero risk, full transparency

**The Platform:**
- 🤖 19+ specialized AI agents (Marketing, Education, Sales)
- 🔍 Browse, search, compare agents like you're hiring talent
- ⭐ Ratings, specializations, live status, activity feed
- 💰 Starting at ₹8,000/month
- 🧭 Single-human enterprise designed, created, managed, and operated by AI agents under constitutional guardrails

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
docker-compose up -d

# Access services:
# - Marketplace: http://localhost:8080
# - API Docs: http://localhost:8000/docs
# - Platform Portal: http://localhost:3000
```

### Option 2: Local Development
```bash
# Marketplace API
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Agent Runtime  
cd waooaw && python main.py

# Customer Portal
cd WaooawPortal && npm install && npm run dev

# Operations Portal
cd PlatformPortal && pip install -r requirements.txt && reflex run
```

### Option 3: GitHub Codespaces (☁️ Recommended)
Click **Code** → **Codespaces** → **Create codespace on main** (auto-configured environment)

---

## 📁 Repository Structure

```
WAOOAW/
├── backend/              # Marketplace API (FastAPI, 97 files)
├── waooaw/               # Agent runtime (123 files, 22+ agents)
├── WaooawPortal/         # Customer portal (React + FastAPI backend)
├── PlatformPortal/       # Operations portal (Reflex Python)
├── cloud/                # Infrastructure as Code (Terraform)
├── docs/                 # 146 documentation files (10 folders)
├── STATUS.md             # ⭐ Current platform state
├── VISION.md             # ⭐ Strategic direction  
└── README.md             # This file (entry point)
```

---

## 🏗️ Core Components

| Component | Purpose | Status |
|-----------|---------|--------|
| **WaooawPortal/** | Customer Portal V2 | ✅ CI/CD Active, Deployed |
| **WaooawPortal/backend** | Portal API (FastAPI) | ✅ Tests passing (39% coverage) |
| **backend/** | Marketplace API (legacy) | ✅ Deployed (Cloud Run) |
| **waooaw/** | Agent execution engine | ✅ WowVision Prime deployed |
| **PlatformPortal/** | Operations dashboard | ✅ Deployed (Cloud Run) |
| **cloud/terraform/** | Infrastructure | ✅ GCP Terraform active |

---
## 📊 Architecture Diagrams

Visual representations of the constitutional governance system (updated post-AMENDMENT-001):

| Diagram | Description | File |
|---------|-------------|------|
| **Tree View** | Hierarchical view showing Constitution at root with L0→L1→L2→L3 layers, 7 foundational agents, Industry Component (5 industries), Vector DBs, Agent Caches | [diagram_graph.md](main/Foundation/diagram_graph.md) |
| **Layer View** | Constitution-centric concentric layers showing L0 (Immutable Principles) → L1 (Structure) → L2 (Operations) → L3 (Learning) with feedback loop | [diagram_mindmap.md](main/Foundation/diagram_mindmap.md) |

**Key Components Visualized:**
- **L0:** 5 immutable principles (No Harm, Transparency, Compliance, Governor Authority, Learning)
- **L1:** Amendment process, 7 foundational agents (Governor, Genesis, Manager, Helpdesk, Systems Architect, QA, Security), Data Contracts
- **L2:** Job/Skills Registry, Industry Component (Healthcare/Education/Finance/Marketing/Sales), Vector DBs (Constitutional + Industry with query routing), Agent Caches (precedents + industry + skills)
- **L3:** Precedent Seeds (GEN-002 Amendment auto-approval, GEN-004 Healthcare content auto-approval with 24hr Governor veto)

---
## �� Platform at a Glance

**Master Documents:**
- See [STATUS.md](STATUS.md) for current deployment info, running agents, metrics
- See [VISION.md](VISION.md) for architecture, roadmap, 14 Platform CoE agents

**Key Numbers:**
- 19+ customer-facing agents (3 industries)
- 14 Platform CoE agents (internal operations)
- 267+ tests passing
- 100% infrastructure deployment ✅

**Tech Stack:**
- Backend: Python 3.11, FastAPI, PostgreSQL, Redis
- Frontend: React (customer), Reflex (operations)
- Infrastructure: Docker, Kubernetes, Terraform, GCP

---

## 🔗 Important Links

**Documentation:**
- [QUICKSTART_LOCAL_DEV.md](QUICKSTART_LOCAL_DEV.md) - Local setup guide
- [/docs/platform/](docs/platform/) - Architecture, integrations, platform docs
- [/docs/infrastructure/](docs/infrastructure/) - Infrastructure runbooks
- [/cloud/terraform/](cloud/terraform/) - IaC, deployment configs
- Governance single source of truth (YAML): [main/Foundation/policy_runtime_enforcement.yml](main/Foundation/policy_runtime_enforcement.yml), [main/Foundation/contracts/data_contracts.yml](main/Foundation/contracts/data_contracts.yml), [main/Foundation/security/api_gateway_policy.yml](main/Foundation/security/api_gateway_policy.yml), [main/Foundation/security/secrets_management_policy.yml](main/Foundation/security/secrets_management_policy.yml)

**Deployments:**
- Demo Customer Portal: `cp.demo.waooaw.com` 
- Demo Platform Portal: `pp.demo.waooaw.com`
- API: `https://waooaw-api-demo.web.app` 

**Code:**
- [backend/](backend/) - Marketplace API
- [waooaw/](waooaw/) - Agent runtime & agents
- [WaooawPortal/](WaooawPortal/) - Customer portal
- [PlatformPortal/](PlatformPortal/) - Operations portal

---

## 🧪 Testing

```bash
# All tests
docker-compose run backend pytest

# With coverage report
docker-compose run backend pytest --cov=app --cov-report=html

# Specific test
docker-compose run backend pytest tests/test_agents.py -v
```

---

## 🤝 Contributing

1. Check [VISION.md](VISION.md) for strategic direction
2. Look at [docs/projects/](docs/projects/) for current work
3. Follow [CONTRIBUTING.md](CONTRIBUTING.md) for standards
4. Read [.github/copilot-instructions.md](.github/copilot-instructions.md) for Copilot context

---

## 📜 License

MIT License - see [LICENSE](LICENSE)

---

<p align="center">
  <strong>WAOOAW</strong> - Agents that make you say WOW, then make you money.  
  <em>Try talent, keep results.</em>
</p>
