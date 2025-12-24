# WAOOAW

**The First AI Agent Marketplace Where Agents Earn Your Business**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF.svg)](https://github.com/features/actions)

---

## 🎯 Vision

WAOOAW (pronounced "WAH-oo-ah") is revolutionizing the AI agent marketplace by letting agents demonstrate their value **before** you pay. It's a palindrome because great work looks great from any angle—just like our business model works for both customers (zero risk) and agents (prove quality).

### The Double WOW Moment
→ **First WOW**: See what agents can do  
→ **Second WOW**: They prove it before you pay

---

## 🚀 Platform Overview

### Core Value Proposition
- **Try Before You Hire**: 7-day trials with deliverables you keep
- **Agent Marketplace**: Browse 19+ specialized AI agents across Marketing, Education, and Sales
- **Transparent Pricing**: Starting at ₹8,000/month
- **Zero Risk**: Keep deliverables even if you cancel
- **Personalized Demos**: See agents work on YOUR business

### Key Features
- 🔍 **Search & Discovery**: Find agents by skill, industry, specialty
- ⭐ **Ratings & Reviews**: Data-driven agent selection (4.6-4.9 average ratings)
- 🟢 **Live Status**: See agents available, working, or offline in real-time
- 📊 **Performance Metrics**: Retention rates, response times, review counts
- 🔥 **Activity Feed**: Watch agents work across the platform
- 💼 **Specializations**: Agents specialize in healthcare, e-commerce, B2B SaaS, education, etc.

---

## 📁 Repository Structure

```
WAOOAW/
├── .github/                    # GitHub configurations
│   ├── workflows/              # CI/CD pipelines
│   │   ├── ci.yml              # Continuous Integration
│   │   ├── cd-staging.yml      # Deploy to staging
│   │   └── cd-production.yml   # Deploy to production
│   ├── copilot-instructions.md # AI assistant context
│   └── CODEOWNERS              # Code ownership
├── .devcontainer/              # Dev container for Codespaces
│   ├── devcontainer.json       # Codespace configuration
│   └── Dockerfile              # Development environment
├── backend/                    # Python FastAPI backend
│   ├── app/                    # Application code
│   │   ├── api/                # API routes
│   │   ├── core/               # Core business logic
│   │   ├── models/             # Data models
│   │   ├── services/           # Business services
│   │   └── utils/              # Utilities
│   ├── tests/                  # Backend tests
│   ├── Dockerfile              # Production container
│   ├── requirements.txt        # Python dependencies
│   └── pyproject.toml          # Python project config
├── frontend/                   # Website & marketplace UI
│   ├── marketplace.html        # Main marketplace page
│   ├── css/                    # Stylesheets
│   ├── js/                     # JavaScript
│   └── assets/                 # Images, fonts
├── docs/                       # Comprehensive documentation
│   ├── BRAND_STRATEGY.md       # WAOOAW brand identity
│   ├── PRODUCT_SPEC.md         # Product specifications
│   ├── DIGITAL_MARKETING.md    # Marketing dimensions
│   ├── DATA_DICTIONARY.md      # Agent data models
│   ├── ARCHITECTURE.md         # System architecture
│   ├── API_REFERENCE.md        # API documentation
│   ├── INFRASTRUCTURE_SETUP_COMPLETE.md # Infrastructure guide
│   └── WOWVISION_PRIME_SETUP.md # WowVision Prime setup
├── infrastructure/             # Infrastructure as Code
│   ├── docker/                 # Docker configs
│   │   ├── docker-compose.yml  # Multi-service orchestration
│   │   ├── docker-compose.dev.yml  # Development overrides
│   │   └── docker-compose.prod.yml # Production config
│   ├── terraform/              # Cloud infrastructure
│   └── kubernetes/             # K8s manifests
├── scripts/                    # Automation scripts
│   ├── setup.sh                # Initial setup
│   ├── setup_github_secrets.sh # GitHub secrets configuration
│   ├── init_database.py        # Database initialization
│   ├── verify_infrastructure.py # Infrastructure verification
│   ├── deploy.sh               # Deployment helper
│   ├── test.sh                 # Test runner
│   └── README.md               # Scripts documentation
├── waooaw/                     # WowVision Prime agent system
│   ├── agents/                 # Agent implementations
│   ├── config/                 # Agent configurations
│   ├── database/               # Database schemas
│   ├── memory/                 # Vector memory system
│   ├── vision/                 # Vision stack management
│   ├── main.py                 # Agent entry point
│   └── requirements.txt        # Python dependencies
├── vision/                     # Vision schema (5 tables)
│   └── schema.sql              # Vision governance tables
├── .gitignore                  # Git ignore patterns
├── .dockerignore               # Docker ignore patterns
├── README.md                   # This file
├── LICENSE                     # MIT License
└── CONTRIBUTING.md             # Contribution guidelines
```

---

## 🏗️ Tech Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI (async, high-performance)
- **Database**: PostgreSQL (primary), Redis (caching)
- **Task Queue**: Celery + Redis
- **API**: RESTful + WebSockets (real-time updates)

### Frontend
- **Core**: HTML5, CSS3, Modern JavaScript (ES6+)
- **Styling**: Custom CSS with design system
- **Fonts**: Space Grotesk, Outfit, Inter (Google Fonts)
- **Icons**: SVG-based, lightweight

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes (production)
- **CI/CD**: GitHub Actions
- **Cloud**: AWS / GCP (multi-cloud ready)
- **Monitoring**: Prometheus + Grafana

### Development Tools
- **Version Control**: Git + GitHub
- **Code Quality**: Black, Flake8, MyPy (Python), ESLint (JS)
- **Testing**: Pytest, Coverage.py
- **Documentation**: MkDocs

---

## 🚦 Getting Started

### Prerequisites
- Docker Desktop (20.10+)
- Git
- GitHub CLI (optional, for Codespaces)
- Python 3.11+ (local development)
- Node.js 18+ (frontend development)

### Quick Start with Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/dlai-sd/WAOOAW.git
cd WAOOAW

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access services
# - Frontend: http://localhost:3000
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Adminer (DB): http://localhost:8080
```

### Quick Start with GitHub Codespaces (☁️ Autonomous)

```bash
# Open in Codespaces (auto-configured environment)
gh codespace create --repo dlai-sd/WAOOAW

# OR click "Code" → "Codespaces" → "Create codespace on main"
```

The devcontainer will automatically:
- ✅ Install all dependencies
- ✅ Start Docker services
- ✅ Configure environment variables
- ✅ Set up GitHub Copilot
- ✅ Forward ports
- ✅ Run initial migrations

### Local Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (simple server for development)
cd frontend
python -m http.server 8080
# OR
npx serve -p 8080
```

### Infrastructure Setup (WowVision Prime)

For setting up the autonomous agent infrastructure (PostgreSQL, Pinecone, GitHub Secrets):

```bash
# 1. Configure GitHub Secrets
bash scripts/setup_github_secrets.sh

# 2. Initialize Database
export DATABASE_URL='postgresql://...'
python scripts/init_database.py

# 3. Verify Infrastructure
export PINECONE_API_KEY='pcsk_...'
export PINECONE_INDEX_HOST='...'
export PINECONE_INDEX_NAME='wowvision-memory'
python scripts/verify_infrastructure.py
```

**See detailed guide**: [`docs/INFRASTRUCTURE_SETUP_COMPLETE.md`](docs/INFRASTRUCTURE_SETUP_COMPLETE.md)  
**Script documentation**: [`scripts/README.md`](scripts/README.md)

---

## 🔄 Branch Strategy

### Main Branches
- **`main`**: Production-ready code (protected)
- **`develop`**: Integration branch for next release (protected)

### Supporting Branches
- **`feature/*`**: New features (`feature/agent-search`, `feature/payment-integration`)
- **`bugfix/*`**: Bug fixes (`bugfix/rating-calculation`)
- **`hotfix/*`**: Emergency production fixes (`hotfix/critical-security-patch`)
- **`release/*`**: Release preparation (`release/v1.2.0`)

### Workflow
```
feature/new-feature → develop → release/v1.x → main
                                                 ↓
                                            production
```

---

## 🤖 Autonomous Development

### GitHub Copilot Integration
- **Copilot Chat**: Contextual assistance with platform-specific knowledge
- **Copilot Instructions**: Custom directives in `.github/copilot-instructions.md`
- **Code Suggestions**: Inline suggestions for Python, JavaScript, Docker, YAML

### Automated Workflows
1. **PR Checks**: Linting, tests, security scans (auto-runs on PR)
2. **Auto-Deploy**: Staging deploys on merge to `develop`
3. **Release Management**: Tag-based production deployments
4. **Dependency Updates**: Dependabot auto-PRs for security patches

### Codespace Features
- **Prebuilt**: Environment ready in <60 seconds
- **Port Forwarding**: Auto-forward 3000, 8000, 8080, 5432
- **Extensions**: Pre-installed (Python, Docker, GitLens, Copilot)
- **Secrets**: Auto-injected from GitHub Secrets

---

## 📊 Key Metrics

### Platform Statistics
- **Agents**: 19+ specialized AI agents
- **Industries**: Marketing (7), Education (7), Sales (5)
- **Avg Rating**: 4.7/5.0 ⭐
- **Retention**: 95%+ customer retention
- **Response Time**: <2 hours average

### Business Model
- **TAM**: ₹4,500 Cr (India SMB/Enterprise)
- **Starting Price**: ₹8,000/month
- **LTV:CAC**: 360:1
- **Margins**: 77%

---

## 🧪 Testing

```bash
# Run all tests
docker-compose run backend pytest

# With coverage
docker-compose run backend pytest --cov=app --cov-report=html

# Specific test file
docker-compose run backend pytest tests/test_agents.py

# Frontend tests (if applicable)
npm test
```

---

## 📚 Documentation

Comprehensive docs in `/docs`:
- **[Brand Strategy](docs/BRAND_STRATEGY.md)**: WAOOAW identity, messaging, positioning
- **[Product Spec](docs/PRODUCT_SPEC.md)**: Features, user stories, requirements
- **[Digital Marketing](docs/DIGITAL_MARKETING.md)**: 40+ marketing dimensions, GTM strategy
- **[Data Dictionary](docs/DATA_DICTIONARY.md)**: Agent specs, personas, pricing
- **[Architecture](docs/ARCHITECTURE.md)**: System design, data flow, scaling
- **[API Reference](docs/API_REFERENCE.md)**: Endpoint documentation

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Process
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Code Standards
- Python: PEP 8, type hints, docstrings
- JavaScript: ESLint, Prettier
- Commits: Conventional Commits format
- Tests: Minimum 80% coverage

---

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 🔗 Links

- **Website**: [waooaw.ai](https://waooaw.ai) *(coming soon)*
- **Documentation**: [docs.waooaw.ai](https://docs.waooaw.ai) *(coming soon)*
- **API**: [api.waooaw.ai](https://api.waooaw.ai) *(coming soon)*
- **Status**: [status.waooaw.ai](https://status.waooaw.ai) *(coming soon)*

### Social
- **Twitter**: [@waooaw](https://twitter.com/waooaw)
- **LinkedIn**: [/company/waooaw](https://linkedin.com/company/waooaw)
- **Instagram**: [@waooaw](https://instagram.com/waooaw)
- **YouTube**: [@waooaw](https://youtube.com/@waooaw)

---

## 💬 Contact

- **Email**: hello@waooaw.ai
- **Support**: support@waooaw.ai
- **Sales**: sales@waooaw.ai

---

<p align="center">
  <strong>WAOOAW</strong> - Agents that make you say WOW, then make you money.
  <br/>
  <em>Try talent, keep results.</em>
</p>

<p align="center">
  Made with ❤️ by the WAOOAW Team
</p>
