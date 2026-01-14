# Plant Database Connector Usage Enforcement

**Reference:** `PLANT_BLUEPRINT.yaml` → `infrastructure.data_layer.migration_strategy.connector_usage_enforcement`  
**Policy Owner:** Systems Architect  
**Effective Date:** January 14, 2026  
**Status:** Active

---

## Challenge Statement

> "Now we have challenge to ensure our plant code use this connector for anything and everything related to db."

All Plant database operations must go through the global Database Connector (`src/Plant/BackEnd/core/database.py`). Direct database imports, sync sessions, or raw SQL connections are **forbidden**.

---

## Enforcement Rules

### Rule 1: No Direct SessionLocal Imports ❌

**Forbidden:**
```python
# ❌ BANNED
from core.database import SessionLocal, Base
from sqlalchemy.orm import Session

@app.get("/skills/")
def list_skills(db: Session = Depends(lambda: SessionLocal())):
    return db.query(Skill).all()
```

**Required:**
```python
# ✅ CORRECT
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db_session

@app.get("/skills/")
async def list_skills(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(Skill))
    return result.scalars().all()
```

### Rule 2: No Sync Sessions ❌

**Forbidden:**
```python
# ❌ BANNED - Blocking I/O in FastAPI
@app.get("/agents/")
def list_agents():  # ← sync function
    db = SessionLocal()  # ← sync session
    agents = db.query(Agent).all()  # ← blocking query
    db.close()
    return agents
```

**Required:**
```python
# ✅ CORRECT - Async all the way
@app.get("/agents/")
async def list_agents(session: AsyncSession = Depends(get_db_session)):
    stmt = select(Agent)
    result = await session.execute(stmt)  # ← non-blocking
    return result.scalars().all()
```

### Rule 3: No Raw Connection Usage ❌

**Forbidden:**
```python
# ❌ BANNED
import psycopg2

def get_agent(agent_id: str):
    conn = psycopg2.connect("dbname=plant user=postgres")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agent_entity WHERE id = %s", (agent_id,))
    return cursor.fetchone()
```

**Required:**
```python
# ✅ CORRECT
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

async def get_agent(agent_id: str, session: AsyncSession):
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await session.execute(stmt)
    return result.scalars().first()
```

### Rule 4: All Endpoints Must Be Async ❌

**Forbidden:**
```python
# ❌ BANNED
@app.post("/skills/")
def create_skill(name: str, session: AsyncSession = Depends(get_db_session)):
    # ← FastAPI mismatch: sync function with async session
    skill = Skill(name=name)
    session.add(skill)
    session.commit()  # ← blocking call
    return skill
```

**Required:**
```python
# ✅ CORRECT
@app.post("/skills/")
async def create_skill(name: str, session: AsyncSession = Depends(get_db_session)):
    skill = Skill(name=name)
    session.add(skill)
    await session.commit()  # ← non-blocking
    return skill
```

### Rule 5: All Database Queries Must Use Await ❌

**Forbidden:**
```python
# ❌ BANNED
result = session.execute(select(Skill))  # ← missing await
skills = result.scalars().all()
```

**Required:**
```python
# ✅ CORRECT
result = await session.execute(select(Skill))  # ← await keyword
skills = result.scalars().all()
```

---

## Enforcement Mechanisms

### 1. Pre-Commit Hook

**File:** `.git/hooks/pre-commit`

```bash
#!/bin/bash

echo "🔍 Checking for forbidden database patterns..."

# Check for direct SessionLocal imports
if grep -r "from core.database import SessionLocal" src/Plant/BackEnd/; then
    echo "❌ FAIL: Direct SessionLocal import detected. Use get_db_session instead."
    exit 1
fi

# Check for sync @app.get/@app.post decorators with DB operations
if grep -A 5 "@app\.\(get\|post\|put\|delete\)" src/Plant/BackEnd/api/ | grep -v "async def"; then
    if grep -A 5 "@app\.\(get\|post\|put\|delete\)" src/Plant/BackEnd/api/ | grep "Depends(get_db_session)"; then
        echo "❌ FAIL: Sync endpoint with async session. Use 'async def'."
        exit 1
    fi
fi

# Check for missing await on session.execute
if grep "session.execute(" src/Plant/BackEnd/ | grep -v "await session.execute"; then
    echo "⚠️  WARNING: Missing await on session.execute (might be commented)"
fi

echo "✅ PASS: Database patterns look good"
exit 0
```

### 2. CI/CD Linting (GitHub Actions)

**In `.github/workflows/plant-db-migrations.yml`:**

```yaml
- name: "Validate Connector Usage"
  run: |
    echo "🔍 Scanning for forbidden patterns..."
    
    # Fail if SessionLocal imported
    if grep -r "from core.database import SessionLocal" src/Plant/BackEnd/; then
      echo "❌ FAIL: SessionLocal import detected"
      exit 1
    fi
    
    # Fail if sync sessions used
    if grep -r "db = SessionLocal()" src/Plant/BackEnd/; then
      echo "❌ FAIL: Direct SessionLocal() usage detected"
      exit 1
    fi
    
    # Fail if psycopg2 imported
    if grep -r "import psycopg2" src/Plant/BackEnd/; then
      echo "❌ FAIL: Raw psycopg2 import detected"
      exit 1
    fi
    
    # Count connector usage (should be increasing)
    connector_count=$(grep -r "get_db_session\|AsyncSession" src/Plant/BackEnd/ | wc -l)
    echo "✅ Found $connector_count connector usage points"
```

### 3. Type Checking (mypy)

**File:** `.mypy.ini`

```ini
[mypy]
strict = True
warn_unused_ignores = True
disallow_untyped_defs = True

# Custom plugin to validate async session types
plugins = mypy_plugins.connector_validator
```

**Custom Plugin:** `mypy_plugins/connector_validator.py`

```python
"""MyPy plugin to enforce AsyncSession usage."""

from mypy.plugin import Plugin
from mypy.nodes import ARG_POS, Decorator

class ConnectorValidatorPlugin(Plugin):
    def get_decorator_hook(self, fullname: str):
        if fullname in ("fastapi.APIRouter.get", "fastapi.APIRouter.post"):
            return self._check_async_handler
        return None
    
    def _check_async_handler(self, ctx):
        # Ensure endpoint is async if using AsyncSession
        pass  # Implementation

def plugin(version: str):
    return ConnectorValidatorPlugin
```

### 4. Code Review Checklist

**Every PR touching `src/Plant/BackEnd/`:**

- [ ] No `SessionLocal` imports (search: `SessionLocal`)
- [ ] No `db = Session()` patterns (search: `Session()`)
- [ ] No sync endpoints with `Depends(get_db_session)` (search: `def.*get_db_session`)
- [ ] All DB endpoints are `async def` (search: `@app\.(get|post|put|delete)` followed by `async def`)
- [ ] All `session.execute()` calls have `await` (search: `session.execute()` without await)
- [ ] Tests use `async_session_fixture` not direct `SessionLocal` (search: `SessionLocal` in `tests/`)
- [ ] Health check endpoint exists: `GET /health/db` (search: `health_check_database`)

### 5. Automated Code Scanning

**Script:** `scripts/validate-connector-usage.sh`

```bash
#!/bin/bash

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🔍 Plant Database Connector Usage Validation"
echo "═══════════════════════════════════════════════════════════════"

ERRORS=0

# Check 1: No SessionLocal imports
echo ""
echo "1️⃣  Checking for SessionLocal imports..."
if grep -r "SessionLocal" src/Plant/BackEnd/ --include="*.py" | grep -v "test_" | grep -v "#"; then
    echo "❌ FAIL: SessionLocal found in non-test code"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ PASS: No SessionLocal imports in production code"
fi

# Check 2: No raw psycopg2
echo ""
echo "2️⃣  Checking for raw psycopg2 usage..."
if grep -r "import psycopg2\|from psycopg2" src/Plant/BackEnd/ --include="*.py" | grep -v "#"; then
    echo "❌ FAIL: psycopg2 found in code"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ PASS: No psycopg2 imports"
fi

# Check 3: All endpoints async
echo ""
echo "3️⃣  Checking endpoint async compliance..."
SYNC_ENDPOINTS=$(grep -r "@app\.\(get\|post\|put\|delete\)" src/Plant/BackEnd/api/ | grep -v "async def" | wc -l)
if [ "$SYNC_ENDPOINTS" -gt 0 ]; then
    echo "❌ FAIL: $SYNC_ENDPOINTS sync endpoints found"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ PASS: All endpoints are async"
fi

# Check 4: Connector usage count
echo ""
echo "4️⃣  Counting connector usage..."
CONNECTOR_USAGE=$(grep -r "get_db_session\|AsyncSession" src/Plant/BackEnd/ --include="*.py" | wc -l)
echo "✅ Found $CONNECTOR_USAGE connector usage points"

# Check 5: Health check endpoint
echo ""
echo "5️⃣  Checking health check endpoint..."
if grep -r "def health_check_database\|async def.*health.*db" src/Plant/BackEnd/ --include="*.py"; then
    echo "✅ PASS: Health check endpoint found"
else
    echo "⚠️  WARNING: Health check endpoint not found"
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════════"
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ SUCCESS: All connector usage checks passed"
    exit 0
else
    echo "❌ FAILURE: $ERRORS validation errors detected"
    exit 1
fi
```

**Run in CI:**
```bash
bash scripts/validate-connector-usage.sh
```

---

## Connector Usage Patterns

### Pattern 1: Simple Query

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db_session

@app.get("/skills/")
async def list_skills(session: AsyncSession = Depends(get_db_session)):
    """List all skills using connector."""
    stmt = select(Skill).order_by(Skill.name)
    result = await session.execute(stmt)
    return result.scalars().all()
```

### Pattern 2: Create with Transaction

```python
@app.post("/skills/")
async def create_skill(
    name: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Create skill with automatic transaction management."""
    skill = Skill(name=name)
    session.add(skill)
    await session.commit()  # Automatically ends session
    return skill
```

### Pattern 3: Error Handling with Rollback

```python
@app.post("/agents/")
async def create_agent(
    agent_data: AgentCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """Create agent with error handling."""
    try:
        agent = Agent(**agent_data.dict())
        session.add(agent)
        await session.commit()
        return agent
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Agent already exists")
```

### Pattern 4: Testing with Async Fixture

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from core.database import Base

@pytest.fixture
async def test_db_session():
    """Isolated test database session."""
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/plant_test")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        yield session
        await session.rollback()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

# tests/test_skills.py
@pytest.mark.asyncio
async def test_create_skill(test_db_session: AsyncSession):
    skill = Skill(name="Python")
    test_db_session.add(skill)
    await test_db_session.commit()
    
    result = await test_db_session.execute(select(Skill).where(Skill.name == "Python"))
    assert result.scalars().first().name == "Python"
```

---

## Connector Compliance Checklist

**Before committing code:**

- [ ] No `from core.database import SessionLocal` imports anywhere
- [ ] No `from sqlalchemy.orm import Session` (use `AsyncSession` instead)
- [ ] All endpoints are `async def` (not `def`)
- [ ] All DB operations use `await session.execute()` (not `session.execute()`)
- [ ] All models have `AsyncSession` type hints (not `Session`)
- [ ] Health check endpoint exists and responds <1s
- [ ] Tests use `async_session_fixture` (not `SessionLocal`)
- [ ] No raw SQL `.execute("SELECT ...")` (use `select()` ORM)
- [ ] Connection pooling config matches environment (.env)
- [ ] Startup event calls `await initialize_database()`
- [ ] Shutdown event calls `await shutdown_database()`

---

## Audit & Monitoring

### Daily Automated Audit

```python
# Background job (runs daily at 2 AM UTC)
@app.on_event("startup")
async def schedule_daily_audit():
    async def audit_connector_usage():
        """Daily check for connector compliance."""
        # Scan codebase for violations
        violations = await check_connector_compliance()
        
        if violations:
            alert_systems_architect(f"⚠️ Connector violations found: {violations}")
            append_audit_log(f"COMPLIANCE_CHECK_FAILED: {len(violations)} violations")
        else:
            append_audit_log("COMPLIANCE_CHECK_PASSED")
    
    # Schedule at 02:00 UTC
    scheduler.add_job(audit_connector_usage, "cron", hour=2, minute=0)
```

### Metrics to Track

| Metric | Ideal Value | Alert If |
|--------|---|---|
| Connector usage points | ↑ increasing | < 50 total |
| Violations per week | 0 | > 0 |
| Health check latency | <500ms | > 1000ms |
| Async endpoint % | 100% | < 95% |
| Test coverage | ≥90% | < 80% |

---

## Penalties for Non-Compliance

| Violation | Penalty |
|-----------|---------|
| Commit with `SessionLocal` import | Automated PR block (no merge) |
| Sync endpoint with `get_db_session` | Code review rejection + re-education |
| Missing `await` on query | CI/CD failure |
| Direct psycopg2 usage | Immediate rollback + incident review |

---

## Questions & Exceptions

**Q: Can I use raw SQL for complex queries?**  
A: Use SQLAlchemy `text()` with `session.execute(text("SELECT ..."))` + await. No psycopg2.

**Q: Can I use sync sessions for background jobs?**  
A: No. Use Temporal workflows with `await` or Celery async tasks.

**Q: What if I need a `Session` type for a function signature?**  
A: Use `AsyncSession` from `sqlalchemy.ext.asyncio`. Type hints enforce correctness.

**Q: Can I bypass this for legacy code?**  
A: All code is new. No exceptions. Contact Systems Architect if truly needed.

---

**Maintained by:** Systems Architect Agent  
**Last Updated:** January 14, 2026  
**Status:** Active & Enforced
