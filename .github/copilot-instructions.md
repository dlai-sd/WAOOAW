# GitHub Copilot Instructions for WAOOAW

## Project Context

WAOOAW is an AI agent marketplace platform where specialized AI agents earn business by demonstrating value before payment. The name is a palindrome ("WAH-oo-ah") representing quality from any angle.

### Core Philosophy
- **Try Before Hire**: 7-day trials, keep deliverables
- **Marketplace DNA**: Browse, compare, discover agents like hiring talent
- **Agentic Vibe**: Agents have personality, status, specializations
- **Zero Risk**: Customers keep work even if they cancel

---

## Development Guidelines

### 🚨 CRITICAL RULES

**1. Document Creation Policy**
- ❌ **DO NOT** create documents unless explicitly asked
- ❌ **DO NOT** create documents without permission
- ✅ **ALWAYS** ask before creating new documentation files
- ✅ Only create docs when user says "create document" or grants explicit permission

**2. Browser Serving Standards**
- ✅ **ALWAYS** serve web pages on Codespace browser after implementation
- ✅ **CHECK** CORS settings, localhost configuration, port forwarding
- ✅ **VERIFY** ports are publicly accessible before sharing URLs
- ✅ **TEST** the URL works before telling user it's ready
- ✅ Use format: `https://${CODESPACE_NAME}-{PORT}.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/`

**3. Port Configuration**
- Frontend: 3000, 8080
- Backend API: 8000
- PostgreSQL: 5432
- Redis: 6379
- Adminer: 8081

---

## Brand Identity (MUST REMEMBER)

### Name & Tagline
- **Name**: WAOOAW (all caps, palindrome)
- **Pronunciation**: "WAH-oo-ah"
- **Tagline**: "Agents Earn Your Business"
- **Positioning**: "The First AI Agent Marketplace That Makes You Say WOW"

### Design System
- **Colors**: 
  * Dark theme: #0a0a0a (black), #18181b (gray-900)
  * Neon accents: #00f2fe (cyan), #667eea (purple), #f093fb (pink)
  * Status: #10b981 (green/online), #f59e0b (yellow/working), #ef4444 (red/offline)
- **Fonts**: Space Grotesk (display), Outfit (headings), Inter (body)
- **Vibe**: Dark, tech-forward, marketplace-focused (Upwork meets cutting-edge AI)

### Key Messaging
- "Agents that make you say WOW, then make you money"
- "Try talent, keep results"
- "Not tools. Not software. Actual AI workforce."

---

## Technical Architecture

### Stack
- **Backend**: Python 3.11+, FastAPI, PostgreSQL, Redis, Celery
- **Frontend**: HTML5, CSS3, Modern JavaScript
- **Infrastructure**: Docker, Docker Compose, Kubernetes
- **CI/CD**: GitHub Actions
- **Development**: Docker-first, Codespaces-optimized

### Project Structure
```
WAOOAW/
├── backend/       # FastAPI application
├── frontend/      # Marketplace UI
├── docs/          # Documentation (Brand, Product, Marketing, Data)
├── infrastructure/# Docker, Terraform, K8s
├── .github/       # Workflows, Copilot instructions
└── scripts/       # Automation
```

---

## Coding Standards

### Python (Backend)
- **Style**: PEP 8, Black formatter
- **Types**: Type hints mandatory (`from typing import ...`)
- **Docstrings**: Google style
- **Async**: Use `async def` for I/O operations
- **Imports**: Absolute imports, grouped (stdlib, third-party, local)
- **Testing**: Pytest, minimum 80% coverage

```python
# Example
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from app.models.agent import Agent
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("/", response_model=List[Agent])
async def list_agents(
    industry: Optional[str] = None,
    min_rating: float = 0.0
) -> List[Agent]:
    """
    List all available agents with optional filters.
    
    Args:
        industry: Filter by industry (marketing, education, sales)
        min_rating: Minimum rating (0.0 to 5.0)
        
    Returns:
        List of agent objects matching filters
    """
    service = AgentService()
    return await service.get_agents(industry=industry, min_rating=min_rating)
```

### JavaScript (Frontend)
- **Style**: ESLint, Prettier
- **Modern**: ES6+ features (arrow functions, destructuring, async/await)
- **Naming**: camelCase for variables/functions, PascalCase for classes
- **Comments**: JSDoc for functions

```javascript
/**
 * Fetch agents from API with filters
 * @param {Object} filters - Filter parameters
 * @param {string} filters.industry - Industry filter
 * @param {number} filters.minRating - Minimum rating
 * @returns {Promise<Array>} Array of agent objects
 */
async function fetchAgents({ industry, minRating } = {}) {
  const params = new URLSearchParams();
  if (industry) params.append('industry', industry);
  if (minRating) params.append('min_rating', minRating);
  
  const response = await fetch(`/api/agents?${params}`);
  if (!response.ok) throw new Error('Failed to fetch agents');
  return response.json();
}
```

### CSS
- **System**: CSS Variables for design tokens
- **Naming**: BEM methodology or semantic class names
- **Responsive**: Mobile-first approach
- **Dark Theme**: Default (#0a0a0a background)

```css
:root {
  --color-primary: #667eea;
  --color-neon-cyan: #00f2fe;
  --bg-black: #0a0a0a;
  --font-display: 'Space Grotesk', sans-serif;
}

.agent-card {
  background: var(--bg-card);
  border: 1px solid var(--border-dark);
  border-radius: 1.5rem;
  transition: all 0.3s ease;
}

.agent-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 0 30px rgba(0, 242, 254, 0.3);
}
```

---

## Domain Knowledge

### Platform Features
1. **Agent Marketplace**: Browse 19+ agents across 3 industries
2. **Search & Filters**: By skill, industry, specialty, rating, price
3. **Agent Cards**: Avatar, status (🟢 Available, 🟡 Working), rating, specialty, activity
4. **Live Activity Feed**: Real-time updates ("Agent X completed Y for Company Z")
5. **Personalized Demos**: See agents work on YOUR business
6. **7-Day Trials**: Keep deliverables regardless of decision

### Industries & Agents
**Marketing (7 agents)**
- Content Marketing (Healthcare specialist)
- Social Media (B2B specialist)
- SEO (E-commerce specialist)
- Email Marketing
- PPC Advertising
- Brand Strategy
- Influencer Marketing

**Education (7 agents)**
- Math Tutor (JEE/NEET specialist)
- Science Tutor (CBSE specialist)
- English Language
- Test Prep
- Career Counseling
- Study Planning
- Homework Help

**Sales (5 agents)**
- SDR Agent (B2B SaaS specialist)
- Account Executive
- Sales Enablement
- CRM Management
- Lead Generation

### Pricing
- Starting: ₹8,000/month
- Average: ₹12,000-15,000/month
- Premium: ₹18,000+/month
- Trial: Free 7 days, keep deliverables

---

## Critical Documents (Reference)

When working on features, reference these docs in `/docs`:
- **BRAND_STRATEGY.md**: Name, tagline, messaging, logo concepts
- **PRODUCT_SPEC.md**: Features, user stories, acceptance criteria
- **DIGITAL_MARKETING.md**: 40+ marketing dimensions, GTM strategy
- **DATA_DICTIONARY.md**: Agent schemas, personas, specializations

---

## Docker Best Practices

- **Multi-stage builds**: Separate build and runtime stages
- **Layer caching**: Order commands from least to most frequently changing
- **Security**: Run as non-root user, scan images
- **Size**: Use alpine base images where possible
- **Compose**: Use profiles for different environments (dev, test, prod)

```dockerfile
# Example multi-stage Python Dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Git Commit Standards

Use Conventional Commits format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: feat, fix, docs, style, refactor, test, chore
**Scope**: agent, marketplace, api, frontend, docker, ci

Examples:
```
feat(marketplace): add agent search with filters

Implemented search functionality with filters for:
- Industry (marketing, education, sales)
- Rating (1-5 stars)
- Price range
- Specialty tags

Closes #42
```

```
fix(api): correct agent status calculation

Status was showing 'offline' for agents with recent activity.
Fixed by updating last_active_at timestamp logic.

Fixes #87
```

---

## Testing Standards

### Backend Tests
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_agents():
    response = client.get("/api/agents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.parametrize("industry,expected_count", [
    ("marketing", 7),
    ("education", 7),
    ("sales", 5),
])
def test_filter_agents_by_industry(industry, expected_count):
    response = client.get(f"/api/agents?industry={industry}")
    assert response.status_code == 200
    assert len(response.json()) == expected_count
```

### Coverage
- Minimum: 80% overall
- Critical paths: 90%+
- Run: `pytest --cov=app --cov-report=html`

---

## Workflow Automation

### When to Trigger CI/CD
- **Pull Request**: Lint, test, build (auto)
- **Merge to develop**: Deploy to staging (auto)
- **Tag v*.*.* **: Deploy to production (manual approval)
- **Daily**: Security scans, dependency updates

### Branch Protection
- **main**: Requires PR review, status checks, up-to-date branch
- **develop**: Requires status checks, allows direct push for maintainers

---

## Special Notes

### Marketplace DNA
The design MUST feel like browsing talent (Upwork/Fiverr), NOT like buying software (SaaS landing page):
- ✅ Agent cards with avatars and personalities
- ✅ Search bar prominently displayed
- ✅ Filters for discovery (industry, rating, price)
- ✅ Live activity feed showing agents working
- ✅ Status indicators (available, working, offline)
- ❌ Generic feature lists or marketing copy-heavy sections

### Agentic Vibe
Agents must feel ALIVE:
- Show real-time status
- Display recent activity ("Posted 23 times today")
- Include specializations (not just generic titles)
- Use metrics (98% retention, 2hr response time)
- Feature avatars with personality (gradient backgrounds, initials)

---

## Common Tasks

### Starting Development
```bash
# With Docker (recommended)
docker-compose up -d

# Without Docker
cd backend && uvicorn app.main:app --reload
cd frontend && python -m http.server 8080
```

### Running Tests
```bash
docker-compose run backend pytest
docker-compose run backend pytest --cov=app
```

### Accessing Services
- Frontend: http://localhost:3000 or :8080
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database UI: http://localhost:8081

---

## Helpful Context

When user mentions:
- "**marketplace**" → Think Upwork/Fiverr browsing experience
- "**agents**" → Specialized AI workers with personality, status, ratings
- "**try before hire**" → 7-day trial, keep deliverables
- "**dark theme**" → #0a0a0a background with neon cyan/purple accents
- "**serve it**" → Deploy to Codespace browser with proper URL
- "**document**" → ASK FIRST, don't auto-create

---

## Error Prevention

Common mistakes to avoid:
1. ❌ Creating docs without asking
2. ❌ Saying "localhost" without Codespace URL
3. ❌ Designing like SaaS landing page (should be marketplace)
4. ❌ Using light theme (should be dark)
5. ❌ Generic agent cards (need avatars, status, personality)
6. ❌ Forgetting to check port forwarding

---

## Summary

You are building WAOOAW, an AI agent marketplace with:
- **Vibe**: Dark, tech-forward, talent marketplace (not SaaS)
- **Stack**: Python/FastAPI, Docker-first, GitHub Actions
- **Rules**: Ask before docs, always serve on Codespace browser
- **Brand**: Palindrome name, "Agents Earn Your Business", try-before-hire

When in doubt:
1. Check `/docs` for context
2. Reference this file
3. Ask user for clarification
4. Default to marketplace DNA over generic design

---

**Remember**: WAOOAW makes users say "WOW!" - bring that energy to every feature! 🚀
