# WAOOAW Platform Portal (Reflex)

**Pure Python frontend for WAOOAW operational portal**

[![Reflex](https://img.shields.io/badge/Reflex-0.8.24-blue.svg)](https://reflex.dev)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-23%2F23-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](htmlcov/)
[![Security](https://img.shields.io/badge/security-0_issues-brightgreen.svg)](.)

---

## Overview

The WAOOAW Platform Portal is a **pure Python frontend** built with Reflex that compiles to React. This portal provides real-time monitoring and operational control for Platform CoE agents.

**Current Status:** Story 5.1.0 - Common Components (1/11 complete)

### Why Reflex?

- ✅ **Pure Python:** No HTML/CSS/JavaScript required
- ✅ **Type Safety:** Full type hints and mypy validation
- ✅ **Real-time:** Built-in WebSocket support
- ✅ **Component-Based:** Reusable UI library
- ✅ **Fast Development:** Hot reload, instant preview
- ✅ **Production Ready:** Compiles to optimized React

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
reflex run

# Run tests
pytest tests/ --cov=waooaw_portal

# Format code
black waooaw_portal/

# Security audit
bandit -r waooaw_portal/
```

---

## Project Structure

```
PlatformPortal/
├── waooaw_portal/           # Main application package
│   ├── components/          # Reusable UI components
│   │   ├── common/          # Common components (status badge, etc.)
│   │   ├── forms/           # Form components
│   │   └── layouts/         # Layout components
│   ├── pages/               # Page definitions
│   ├── state/               # Application state management
│   ├── services/            # Backend service integrations
│   ├── models/              # Data models
│   └── theme/               # Design system (colors, typography)
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

---

## Story 5.1.0: Common Components

**Goal:** Build 11 reusable components as foundation for all portal features

**Progress:** 1/11 components complete (9% done)

### Frontend Components (1/6 complete)

| Component | Status | Coverage | Tests | Security |
|-----------|--------|----------|-------|----------|
| status_badge | ✅ Complete | 100% | 23 passing | 0 issues |
| metrics_widget | 🚧 In Progress | - | - | - |
| websocket_manager | 🚧 Pending | - | - | - |
| timeline_component | 🚧 Pending | - | - | - |
| progress_tracker | 🚧 Pending | - | - | - |
| context_selector | 🚧 Pending | - | - | - |

### Backend Services (0/5 complete)

| Service | Status | Coverage | Tests | Security |
|---------|--------|----------|-------|----------|
| websocket_broadcaster | 🚧 Pending | - | - | - |
| metrics_aggregator | 🚧 Pending | - | - | - |
| health_checker | 🚧 Pending | - | - | - |
| audit_logger | 🚧 Pending | - | - | - |
| provisioning_engine | 🚧 Pending | - | - | - |

---

## Component Details

### Status Badge (`components/common/status_badge.py`)

**Purpose:** Traffic light status indicators for agents, services, workflows

**Features:**
- 15 status types (online, offline, working, error, warning, etc.)
- 3 sizes (sm, md, lg)
- Dark/light theme support
- Emoji indicators (🟢🟡🔴⚫)
- Hover effects with neon glow
- List view for multiple badges

**Usage:**
```python
from waooaw_portal.components.common import status_badge, badge_online

# Basic usage
status_badge("online", "Agent Active")

# Preset badges
badge_online("CoE Agent #7")
badge_working("Processing Request")
badge_offline("Service Unavailable")

# List view
status_badge_list([
    ("online", "API Gateway"),
    ("working", "Database"),
    ("error", "Cache Service")
])
```

**Test Coverage:** 100% (23 tests)
- Basic functionality: 10 tests
- Preset badges: 4 tests
- Edge cases: 4 tests (invalid status, empty label, long label, special chars)
- Integration scenarios: 5 tests (agent status, system health, workflows)

---

## Design System

### Theme: WAOOAW Brand

**Colors:**
- **Dark Theme (Default):** #0a0a0a (black), #18181b (cards)
- **Neon Accents:** #00f2fe (cyan), #667eea (purple), #f093fb (pink)
- **Status Colors:** #10b981 (green), #f59e0b (yellow), #ef4444 (red)

**Typography:**
- **Display:** Space Grotesk (headings, large text)
- **Headings:** Outfit (section titles)
- **Body:** Inter (paragraph text, UI)
- **Code:** JetBrains Mono (code blocks, logs)

**Spacing:** 8px base scale
- xs: 8px, sm: 16px, md: 24px, lg: 32px, xl: 48px, xxl: 64px

**Border Radius:**
- sm: 8px, md: 12px, lg: 16px, full: 9999px

**Theme Access:**
```python
from waooaw_portal.theme import (
    DARK_THEME,
    LIGHT_THEME,
    get_theme,
    get_status_color,
    get_status_emoji
)

# Get theme colors
theme = get_theme("dark")
bg_color = theme["bg_primary"]

# Get status color
status_color = get_status_color("online", "dark")  # Returns #10b981

# Get status emoji
emoji = get_status_emoji("working")  # Returns 🟡
```

---

## Development Workflow

### 1. Build Component
```bash
# Create component file
touch waooaw_portal/components/common/my_component.py

# Write component with type hints
# Follow Reflex component patterns
```

### 2. Write Tests
```bash
# Create test file
touch tests/unit/test_my_component.py

# Write comprehensive tests:
# - Basic functionality
# - Edge cases
# - Integration scenarios
# Target: >85% coverage
```

### 3. Run Quality Checks
```bash
# Run tests
pytest tests/unit/test_my_component.py --cov=waooaw_portal.components.common.my_component

# Format code
black waooaw_portal/components/common/my_component.py

# Security audit
bandit waooaw_portal/components/common/my_component.py -ll

# Type checking
mypy waooaw_portal/components/common/my_component.py
```

### 4. Code Review
- ✅ Tests passing (>85% coverage)
- ✅ Security audit clean (0 issues)
- ✅ Code formatted (black)
- ✅ Type hints present
- ✅ Follows design system
- ✅ Documentation updated

### 5. Commit & Push
```bash
git add .
git commit -m "feat(components): add my_component with tests"
git push origin main
```

---

## Testing Standards

### Unit Tests
- **Framework:** pytest 7.4.3
- **Coverage:** pytest-cov (target: >85%)
- **Async:** pytest-asyncio 0.21.1
- **Mocking:** pytest-mock 3.12.0

**Test Structure:**
```python
import pytest
from waooaw_portal.components.common.my_component import my_component

class TestMyComponent:
    """Test basic functionality"""
    
    def test_my_component_basic(self):
        result = my_component("arg1", "arg2")
        assert result is not None
        
class TestMyComponentEdgeCases:
    """Test edge cases"""
    
    def test_invalid_input(self):
        result = my_component(None, "")
        assert result is not None
        
class TestMyComponentIntegration:
    """Test integration scenarios"""
    
    def test_with_theme(self):
        result = my_component("arg", theme="dark")
        assert "dark" in str(result)
```

### Integration Tests
- Test multiple components working together
- Test with backend services
- Test WebSocket real-time updates
- Test with database

---

## Quality Gates

All components must pass these gates before merge:

| Gate | Tool | Target |
|------|------|--------|
| Tests | pytest | 100% passing |
| Coverage | pytest-cov | >85% |
| Security | bandit | 0 issues |
| Formatting | black | Pass |
| Type Checking | mypy | 0 errors |
| Linting | ruff | 0 errors |

**Run All Checks:**
```bash
# Full quality check
pytest tests/ --cov=waooaw_portal --cov-report=term-missing
black waooaw_portal/ tests/
bandit -r waooaw_portal/ -ll
mypy waooaw_portal/
ruff check waooaw_portal/
```

---

## Dependencies

**Core:**
- reflex==0.8.24.post1 - Pure Python web framework
- pydantic==2.5.3 - Data validation
- httpx==0.26.0 - Async HTTP client
- python-multipart==0.0.6 - Form data parsing

**Database:**
- sqlalchemy==2.0.25 - ORM
- asyncpg==0.29.0 - PostgreSQL async driver
- redis==5.0.1 - Redis client

**WebSocket:**
- websockets==12.0 - WebSocket support
- python-socketio==5.11.0 - Socket.IO

**Testing:**
- pytest==7.4.3 - Test framework
- pytest-asyncio==0.21.1 - Async testing
- pytest-cov==4.1.0 - Coverage
- pytest-mock==3.12.0 - Mocking

**Code Quality:**
- black==23.12.1 - Formatter
- ruff==0.1.9 - Linter
- mypy==1.8.0 - Type checker
- bandit==1.7.6 - Security linter

**Complete list:** See [requirements.txt](requirements.txt)

---

## Documentation

- **Master Plan:** [docs/platform/PLATFORM_PORTAL_MASTER_PLAN.md](../docs/platform/PLATFORM_PORTAL_MASTER_PLAN.md)
- **Version History:** [VERSION.md](../VERSION.md)
- **Status:** [STATUS.md](../STATUS.md)
- **Architecture:** [docs/platform/PLATFORM_ARCHITECTURE.md](../docs/platform/PLATFORM_ARCHITECTURE.md)

---

## Deployment

**Docker:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["reflex", "run", "--env", "prod"]
```

**Multi-Cloud:**
- **GCP:** Cloud Run, GKE
- **Azure:** Container Apps, AKS
- **CI/CD:** GitHub Actions

See [PLATFORM_PORTAL_MASTER_PLAN.md](../docs/platform/PLATFORM_PORTAL_MASTER_PLAN.md) for deployment details.

---

## Contributing

1. Create feature branch
2. Write component with tests
3. Run quality checks
4. Update documentation
5. Submit PR with code review checklist

**Quality Checklist:**
- [ ] Tests passing (>85% coverage)
- [ ] Security audit clean
- [ ] Code formatted (black)
- [ ] Type hints present
- [ ] Documentation updated
- [ ] Follows design system

---

## License

MIT License - See [LICENSE](../LICENSE) for details

---

## Support

- **Issues:** GitHub Issues
- **Docs:** [docs/platform/](../docs/platform/)
- **Status:** [STATUS.md](../STATUS.md)

---

**Built with ❤️ by the WAOOAW team**
