# Plant Backend

FastAPI backend for WAOOAW Plant Phase - Agent manufacturing pipeline with constitutional alignment.

## Architecture

**7-Section BaseEntity Pattern:**
- All entities (Skill, JobRole, Team, Agent, Industry) inherit from BaseEntity
- BaseEntity enforces L0/L1 constitutional principles from first moment
- Cryptographic signatures (RSA-4096) for non-repudiation
- Hash chain (SHA-256) for audit trail integrity

**Tech Stack:**
- **Backend:** Python 3.11 + FastAPI
- **Database:** PostgreSQL Cloud SQL + pgvector (semantic search)
- **ORM:** SQLAlchemy 2.0 + Alembic migrations
- **Cache:** Redis (embedding cache)
- **Cryptography:** RSA-4096 + SHA-256 hash chains
- **Testing:** pytest + testcontainers (90%+ coverage)

## Directory Structure

```
BackEnd/
├── core/              # Configuration, database, exceptions
├── models/            # BaseEntity + entity models + Pydantic schemas
├── validators/        # L0/L1 constitutional checks
├── security/          # Cryptography + hash chains
├── database/          # Migrations + RLS policies
├── api/               # FastAPI routes
├── services/          # Business logic
├── tests/             # Unit/integration/performance/security tests
└── scripts/           # Utility scripts
```

See `/docs/plant/PLANT_BLUEPRINT.yaml` Section 13 for detailed structure.

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb plant_db

# Run migrations (future - using Alembic)
# alembic upgrade head
```

### 4. Run Development Server

```bash
# Run with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or use main.py directly
python main.py
```

### 5. Access API Docs

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## API Endpoints

### Genesis Certification
- `POST /api/v1/genesis/jobs` - Create job role
- `POST /api/v1/genesis/jobs/{id}/certify` - Certify job role
- `POST /api/v1/genesis/skills` - Create skill
- `POST /api/v1/genesis/skills/{id}/certify` - Certify skill

### Agent Management
- `POST /api/v1/agents` - Create agent specification
- `GET /api/v1/agents/{id}` - Get agent details
- `PUT /api/v1/agents/{id}` - Update agent

### Constitutional Audit
- `POST /api/v1/audit/run` - Run constitutional compliance audit
- `GET /api/v1/audit/{id}` - Get audit results

## Testing

```bash
# Run all tests with coverage
pytest

# Run specific test categories
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests
pytest -m performance    # Performance SLA validation
pytest -m security       # Security tests

# Generate coverage report
pytest --cov-report=html
open htmlcov/index.html
```

**Coverage Target:** ≥90% (CI/CD gate)

## Development Guidelines

### BaseEntity Usage

```python
from models import Skill

# Create skill
skill = Skill(
    name="Python 3.11",
    description="Backend Python development",
    category="technical",
    governance_agent_id="genesis"
)

# Validate constitutional alignment
result = skill.validate_self()
if not result["compliant"]:
    raise ConstitutionalAlignmentError(result["violations"])

# Evolve entity
skill.evolve({"description": "Updated description"})

# Sign amendment
skill.sign_amendment(private_key_pem)

# Verify signature
is_valid = skill.verify_amendment(public_key_pem)
```

### Adding New Entity

1. Create model in `models/` (inherit from BaseEntity)
2. Add L1 validation rules in `validators/constitutional_validator.py`
3. Create Pydantic schemas in `models/schemas.py`
4. Add database migration in `database/migrations/versions/`
5. Implement service in `services/`
6. Add API routes in `api/v1/`
7. Write tests in `tests/`

### Code Quality Standards

- **Type hints:** 100% (enforced by mypy --strict)
- **Test coverage:** ≥90% (enforced by pytest-cov)
- **Code format:** Black formatter (auto-fix)
- **Linting:** Flake8 (E, W, F errors)
- **Security:** Bandit (no HIGH issues)

## Configuration

Edit `.env` file for local development:

```bash
# Database
DATABASE_URL="postgresql://user:password@localhost:5432/plant_db"

# Redis
REDIS_URL="redis://localhost:6379/0"

# ML Service
ML_SERVICE_URL="http://localhost:8005"

# Security
SECRET_KEY="your-secret-key-change-in-production"
RSA_KEY_SIZE=4096
```

## Performance SLAs

| Operation | SLA | Enforcement |
|-----------|-----|-------------|
| `validate_self()` | <10ms | Benchmark test |
| `evolve()` | <5ms | Benchmark test |
| `verify_amendment()` | <20ms | Benchmark test |
| pgvector search | <500ms | Integration test |
| Schema migration latency | <10% increase | Workflow gate |

## Constitutional Principles

### L0 Principles (Foundation)
- **L0-01:** Governance agent ID tracked for all entities
- **L0-02:** Amendment history complete (append-only)
- **L0-03:** No manual updates to past amendments
- **L0-04:** Supersession chain preserved
- **L0-05:** Compliance gate exportable

### L1 Principles (Entity-Specific)
- Skill: Name unique, category valid
- JobRole: Required skills non-empty
- Team: At least one agent, job role set
- Agent: Skill + JobRole + Industry set
- Industry: Name unique

## Troubleshooting

### Database connection fails
```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql postgresql://user:password@localhost:5432/plant_db
```

### Import errors
```bash
# Install all dependencies
pip install -r requirements.txt

# Verify installations
pip list | grep fastapi
pip list | grep sqlalchemy
```

### Tests failing
```bash
# Run with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_base_entity.py -v

# Check coverage
pytest --cov=models --cov-report=term-missing
```

## Reference Documents

- **Blueprint:** `/docs/plant/PLANT_BLUEPRINT.yaml` (Sections 1-13)
- **User Stories:** `/docs/plant/PLANT_USER_STORIES.yaml`
- **Phase 0 Review:** `/docs/plant/PLANT_PHASE0_REVIEW.md`
- **Foundation:** `/main/Foundation/` (ADR-007, architecture_manifest.yml)

## Next Steps

- [ ] Implement database migrations (Alembic)
- [ ] Add Genesis certification endpoints (api/v1/genesis/)
- [ ] Implement ML integration (ml/inference_client.py)
- [ ] Add Temporal workflows (workflows/)
- [ ] Create comprehensive test suite (tests/)
- [ ] Deploy to GCP Cloud Run

---

**Status:** Phase 0 core implementation complete (BaseEntity, validators, security layer)
**Last Updated:** 2026-01-14
**Blueprint Version:** 1.2

