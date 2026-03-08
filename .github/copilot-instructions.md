# GitHub Copilot Instructions for WAOOAW

## Response Format Requirements (ALWAYS FOLLOW)

- Summaries must be exactly 5 bullets, each bullet 1-2 sentences.
- Do not add decorative badges, long text, or large code samples.
- Wherever possible, present comparisons/analysis in tables with: Root cause | Impact | Best possible solution/fix.

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
- **Backend**: Python 3.11+, FastAPI, PostgreSQL 15, Redis 7, SQLAlchemy (async), Alembic
- **Frontend**: React 18, TypeScript, Vite (CP & PP portals); React Native / Expo (mobile)
- **Infrastructure**: Docker, Docker Compose, GCP Cloud Run, Terraform
- **CI/CD**: GitHub Actions
- **Development**: Docker-first, Codespaces-optimized

### Project Structure
```
WAOOAW/
├── src/
│   ├── CP/
│   │   ├── BackEnd/    # Customer Portal — FastAPI thin proxy
│   │   └── FrontEnd/   # Customer Portal — React 18 / TypeScript / Vite
│   ├── Plant/
│   │   ├── BackEnd/    # Plant (agent-side) — FastAPI core business logic
│   │   └── Gateway/    # Plant API gateway — auth, RBAC, OPA policy, budget
│   ├── PP/
│   │   ├── BackEnd/    # Partner Portal — FastAPI thin proxy
│   │   └── FrontEnd/   # Partner Portal — React 18 / TypeScript / Vite
│   └── mobile/         # React Native / Expo / TypeScript — mobile app
├── docs/               # All platform docs (start with CONTEXT_AND_INDEX.md)
├── infrastructure/     # Docker, Terraform, GCP Cloud Run
├── .github/            # Workflows, Copilot instructions, agent personas
└── scripts/            # Automation
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
# Example — always use waooaw_router(), never bare APIRouter
from typing import List, Optional
from fastapi import Depends
from core.routing import waooaw_router
from models.agent import Agent
from services.agent_service import AgentService
from core.database import get_read_db_session

router = waooaw_router(prefix="/agents", tags=["agents"])

@router.get("/", response_model=List[Agent])
async def list_agents(
    industry: Optional[str] = None,
    min_rating: float = 0.0,
    db=Depends(get_read_db_session),
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
- **`docs/CONTEXT_AND_INDEX.md`**: Master platform reference — architecture, file index, test commands, gotchas (read §1, §3, §5, §11, §17 first)
- **`docs/CP/iterations/NFRReusable.md`**: Mandatory NFR patterns every route must follow (§3 interface definitions, §5 preventive gate stories)
- **`docs/CP/README.md`**: Customer Portal feature overview and iteration history
- **`docs/plant/README.md`**: Plant (agent-side) backend overview

---

## Docker Best Practices

- **Multi-stage builds**: Separate build and runtime stages
- **Layer caching**: Order commands from least to most frequently changing
- **Security**: Run as non-root user, scan images
- **Size**: Use alpine base images where possible
- **Compose**: Use profiles for different environments (dev, test, prod)

```dockerfile
# Example multi-stage Python Dockerfile (no virtualenv — Docker is the isolation layer)
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target /install

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local/lib/python3.11/site-packages
COPY . .
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
**Scope**: cp, plant, gateway, pp, mobile, infra, ci

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
from main import app

client = TestClient(app)

def test_list_agents():
    response = client.get("/v1/agents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### Coverage
- Minimum: 80% overall
- Critical paths: 90%+
- Run: `pytest --cov=app --cov-report=xml --cov-fail-under=80`

---

## Workflow Automation

### When to Trigger CI/CD
- **Pull Request**: Lint, test, build (auto)
- **Merge to main**: Deploy to demo/staging (auto)
- **Tag v*.*.* **: Deploy to production (manual approval)
- **Daily**: Security scans, dependency updates

### Branch Protection
- **main**: Requires PR review, status checks, up-to-date branch
- Branch naming: `feat/<scope>-<desc>` | `fix/<scope>-<desc>` | `docs/<topic>`

---

## GCP Access — Cloud Run Logs & Debugging

This Codespace is authenticated as `waooaw-codespace-reader@waooaw-oauth.iam.gserviceaccount.com`
against project `waooaw-oauth`. You **can and should** pull live Cloud Run logs directly — never
guess from a generic CI timeout message.

```bash
# Get logs for a specific revision
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.revision_name="<REVISION>"' \
  --project=waooaw-oauth --limit=50 --freshness=5d 2>&1 | grep textPayload

# Get recent error logs for a service
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="<SERVICE>" AND severity>=ERROR' \
  --project=waooaw-oauth --limit=30 --freshness=2d 2>&1

# List revisions for a service
gcloud run revisions list --service=<SERVICE> --region=asia-south1 --project=waooaw-oauth
```

> When Terraform apply fails with *"container failed to start and listen on PORT"*, always fetch
> the Cloud Run stderr logs for that revision first — they contain the exact Python traceback
> (e.g. `ModuleNotFoundError`) rather than the generic Cloud Run timeout message.

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
docker-compose -f docker-compose.local.yml up -d
```

### Running Tests
```bash
# Python backend — minimum 80% coverage required
docker-compose -f docker-compose.test.yml run cp-test pytest --cov=app --cov-report=xml --cov-fail-under=80
docker-compose -f docker-compose.test.yml run plant-test pytest --cov=app --cov-report=xml --cov-fail-under=80

# Mobile
cd src/mobile && node_modules/.bin/jest --forceExit
```

### Accessing Services
- CP Frontend: http://localhost:3002
- PP Frontend: http://localhost:3001
- Plant Gateway: http://localhost:8000
- Plant Backend: http://localhost:8001
- CP Backend: http://localhost:8020
- PP Backend: http://localhost:8015
- API Docs (Plant Gateway): http://localhost:8000/docs
- Database UI (Adminer): http://localhost:8081

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
- **Stack**: Python/FastAPI + React/TypeScript, Docker-first, GitHub Actions
- **Rules**: Ask before docs, always serve on Codespace browser
- **Brand**: Palindrome name, "Agents Earn Your Business", try-before-hire

When in doubt:
1. Check `/docs` for context
2. Reference this file
3. Ask user for clarification
4. Default to marketplace DNA over generic design

---

## PM Planning Workflow (activated by "create iteration plan" or "plan this")

When the user asks for an iteration plan, switch into Program Manager mode:

### Step 1 — Vision intake
Answer these 5 questions (from context or by asking the user):
1. What service/area? (CP FrontEnd, CP BackEnd, mobile, Plant, PP, infra)
2. What user outcome? (one sentence — what can the user DO after this is done?)
3. What is OUT of scope? (prevents agents from gold-plating)
4. Lane A (wire existing APIs) or Lane B (new backend required)?
5. Timeline constraint?

State your answers as bullets. Let the user correct before proceeding.

### Step 2 — Read context
- `docs/CONTEXT_AND_INDEX.md` §1, §3, §5, §13 — architecture + exact file paths
- `docs/CP/iterations/NFRReusable.md` §3, §6 — NFR patterns + image promotion rules
- Any UX analysis or design doc the user references

### Step 3 — Produce the plan (with incremental commit checkpoints)

> **Why checkpoints matter**: Plan documents are large (500–1000+ lines). A context-limit hit,
> disconnection, or token exhaustion part-way through loses all unwritten content. The rules
> below ensure every completed section is saved to git before the next one is written.

#### 3a — Branch first (do this before writing a single line of plan content)
```bash
git checkout main && git pull origin main
git checkout -b docs/[plan-id]-[short-name]
```

#### 3b — Commit the skeleton immediately
Write and commit the plan skeleton (metadata table, vision intake, iteration summary table,
agent execution rules — NO story cards yet):
```bash
git add docs/[service]/iterations/[plan-id]-[name].md
git commit -m "docs([plan-id]): skeleton — metadata, vision intake, iteration summary"
git push -u origin docs/[plan-id]-[short-name]
```

#### 3c — Write and commit one iteration at a time
For each iteration (1, 2, 3 …):
1. Write all story cards for that iteration into the plan file.
2. Immediately commit + push:
```bash
git add docs/[service]/iterations/[plan-id]-[name].md
git commit -m "docs([plan-id]): iteration N story cards — [scope summary]"
git push
```
3. Only then start writing the next iteration's story cards.

> If the session is interrupted after any commit, the next session can pick up exactly
> where it left off by reading the last committed state of the file.

#### 3d — Open the PR after all iterations are written
```bash
gh pr create --base main \
  --title "docs([plan-id]): [plan name]" \
  --body "[summary of all iterations]"
```

#### 3e — Plan content rules
- Copy `docs/templates/iteration-plan-template.md`
- Save to `docs/[service]/iterations/[plan-id]-[name].md`
- Fill every `[PLACEHOLDER]` — zero placeholders in the published file
- Tick every item in the PM Review Checklist inside the template
- **Story card rule**: every story must be self-contained (exact file paths, 2-3 sentence context, no "see above")
- **Inline code rule**: every story card embeds the relevant NFR snippet in "Code patterns to copy exactly" — do NOT write "see NFRReusable.md §3". Pull the 10-20 line snippet and embed it verbatim. Zero-cost models (Gemini Flash, GPT-4o-mini) have 8K-32K context windows — they cannot afford an external reference file read mid-story.
- **Story size**: 30 min (small FE) / 45 min (single endpoint) / 90 min (full-stack). Split anything larger.
- **Max 6 stories per iteration**

### Step 4 — Report to user (exactly this, nothing more)

```
Plan ready: [PLAN-ID]
File: docs/[path]
PR: [github PR URL]

| Iteration | Scope | ⏱ Est | Come back |
|---|---|---|---|
| 1 | ... | Xh | DATE HH:MM TZ |
...

To launch Iteration 1 — GitHub Copilot Agent interface:
1. Open VS Code → Copilot Chat (Ctrl+Alt+I / Cmd+Alt+I)
2. Click model dropdown → Agent mode
3. Click + → type @ → select platform-engineer
4. Paste task:
[iteration 1 agent task from plan's "How to Launch" section]
5. Come back: DATE HH:MM TZ

To launch Iteration 2 (after Iteration 1 PR merged):
[same steps with iteration 2 task]
```

> ⚠️ **Before launching ANY iteration**: verify the plan file AND that iteration section are on `main`:
> ```bash
> git fetch origin
> git show origin/main:docs/[path/to/plan.md] | grep "## Iteration N"
> # Zero results → DO NOT launch. Merge the plan PR to main first.
> ```
> If the file is missing or the iteration section is absent, the agent will invent its own scope. Merge the plan PR first, then launch.

### Step 5 — Execution agent checkpoint rule (embed in every plan's Agent Execution Rules)

Every plan's "Agent Execution Rules" section MUST include this rule verbatim:

> **CHECKPOINT RULE**: After completing each epic (all tests passing), run:
> ```bash
> git add -A && git commit -m "feat([plan-id]): [epic-id] — [epic title]" && git push
> ```
> Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

### PM hard rules
- Never write "find the file that handles X" — you find it and name it
- Never write "similar to how Y works" — self-contained story cards only
- Never write "refactor while you're there" — in-scope only
- Lane A always precedes Lane B in iteration ordering
- Backend story (S1) always precedes its frontend counterpart (S2); mark S2 as `BLOCKED UNTIL: S1 merged`
- Zero-cost model constraint: max 3-4 files to read per story — pre-identified by PM in the card
- Embed NFR snippets inline — never reference NFRReusable.md in a story card
- **Always branch + commit skeleton before writing story cards** — no exceptions
- **CP BackEnd is a thin proxy, not a business logic layer.** Every story involving CP must state which pattern applies: (a) existing `/cp/*` route in `api/cp_*.py` → call via `gatewayRequestJson`; (b) missing `/cp/*` route → new `api/cp_<resource>.py` file with `waooaw_router` + `PlantGatewayClient` (Lane B, 45 min); (c) existing `/v1/*` pass-through → call via `gatewayRequestJson`, no new BE file. Never place business logic or data storage in CP BackEnd.

---

**Remember**: WAOOAW makes users say "WOW!" - bring that energy to every feature! 🚀
