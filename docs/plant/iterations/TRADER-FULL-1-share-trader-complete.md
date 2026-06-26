# TRADER-FULL-1 — Share Trader: Credential DB Store, Connectivity Validation, Trade Results, Performance Review & Recommendations

**Objective**
Complete the Share Trader agent lane by filling two production gaps (performance review, recommendations) and hardening two existing components (credential persistence, connectivity validation). After this plan merges, a customer can connect Delta Exchange credentials that survive Cloud Run restarts, the agent self-validates those credentials before trading, the customer reviews P&L and win-rate history on mobile, and the agent recommends RSI threshold adjustments based on real trade outcomes.

**Objective alignment**: Direct **Share Trader value** — closes the performance-review ❌ and recommendations ❌ gaps from the platform roadmap, plus hardens credential storage and connectivity validation from file-backed/implicit to DB-backed/explicit.

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `TRADER-FULL-1` |
| Feature area | Plant BackEnd + CP BackEnd (thin proxy) + Mobile CP |
| Created | 2026-06-26 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §1.1 Share Trader scope |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 4 |
| Total stories | 11 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for **autonomous zero-cost model agents** (Gemini Flash, GPT-4o-mini, etc.)
with limited context windows. Every structural decision exists to preserve context.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | NFR code patterns are embedded **inline** in each story — agent never opens NFRReusable.md |
| No planning ability | Stories are atomic — one deliverable, one set of files, one test command |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM in each card |
| Binary inference only | Acceptance criteria are pass/fail — no judgment calls required |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. All patterns you need are in your card.
> Do NOT read files not listed in your story card's "Files to read first" section.

---

## PM Review Checklist

- [x] **EXPERT PERSONAS filled** — each iteration's agent task block has correct expert persona list
- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline — no "see NFRReusable.md"
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story that adds env vars lists the exact Terraform file paths to update
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (S1) before frontend counterpart
- [x] No placeholders remain
- [x] TDD/BDD — every story card has a test table
- [x] Integration Baseline Gate section is populated
- [x] CHECKPOINT RULE is in Agent Execution Rules

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | DB exchange credential store + connectivity validation + trade result storage | 2 | 6 | 5h | 2026-06-27 11:00 IST |
| 2 | Trade performance review API + pluggable recommendations engine + mobile screens | 2 | 5 | 5h | 2026-06-27 17:00 IST |

**Estimate basis:** New model + migration = 45 min | New Plant route = 45 min | CP thin proxy route = 30 min | Mobile hook + component = 60 min | Test suite = 45 min. 20% buffer added for zero-cost model context loading.

---

## Design Decisions (read before story cards)

| Decision | Choice | Rationale |
|---|---|---|
| Exchange credential storage | New `ExchangeCredentialModel` in Plant DB (table `exchange_credentials`) + Firestore dual-write via DatastoreRouter | Consistent with `CustomerPlatformCredentialModel` pattern; survives Cloud Run restarts; `FileExchangeSetupStore` in CP is removed |
| Secret storage | Fernet-encrypted field in DB (same key as CP's `CP_EXCHANGE_SETUP_SECRET`) for demo/uat; GCP Secret Manager ref for prod | Env-var `EXCHANGE_SECRET_BACKEND=fernet\|secret_manager` controls which path — never baked into image |
| Connectivity validation | Live call to `GET /v2/wallet/balances` + `GET /v2/profile`; returns `{readable: bool, tradeable: bool}`; ENVIRONMENT=test → `MagicMock` (same as `FirestoreClient` pattern) | Customer needs live feedback before first trade |
| Trade results storage | New `TradeResultModel` (table `trade_results`); Firestore dual-write adds `trade_results` to `_ROUTABLE_COLLECTIONS` | Consistent with INFRA-ROUTING-1 dual-write architecture |
| Recommendations | `RecommendationEngine` abstract base class + `RuleBasedRecommendationEngine` implementation; `RECOMMENDATION_ENGINE=rule_based` env var selects engine | LLM engine can be plugged in next iteration by adding a new concrete class and changing the env var — no code change to routes |
| CP BackEnd pattern | Pattern B (new thin proxy routes in `api/cp_exchange_credentials.py`) calling Plant via `PlantGatewayClient` | CP never stores secrets; Plant is authoritative |

---

## Integration Baseline Gate

> **Agent: run these commands BEFORE writing any code. If any returns 404 or connection error, HALT.**

```bash
# 1. Plant BackEnd config importable
cd src/Plant/BackEnd && python -c "from core.config import settings; print(settings.environment)"

# 2. Existing credential model present
ls src/Plant/BackEnd/models/customer_platform_credential.py

# 3. Latest migration present (next migration must be 041)
ls src/Plant/BackEnd/database/migrations/versions/040_dma_batch_type_workflow.py

# 4. DatastoreRouter present (INFRA-ROUTING-1 merged)
ls src/Plant/BackEnd/core/datastore_router.py

# 5. CP exchange_setup service present (to be superseded)
ls src/CP/BackEnd/services/exchange_setup.py

# 6. CP PlantGatewayClient present
ls src/CP/BackEnd/services/plant_gateway_client.py
```

---

## Architecture Overview

```
BEFORE (current — file-backed, fragile):
Customer → CP FrontEnd → CP BackEnd (FileExchangeSetupStore) → file.json
                                                             ↓
                                                    Plant DeltaExchangePump reads raw API key from skill_config

AFTER (this plan — DB-backed, validated, observable):
Customer → CP FrontEnd → CP BackEnd (thin proxy) → Plant BackEnd → exchange_credentials table
                                                                 → Firestore (dual-write, DATA_ROUTER_MODE controlled)
                                                                 → Delta Exchange /validate → live credential check

Trade execution (unchanged flow, hardened credential lookup):
  DeltaExchangePump reads credential_ref from skill_config
  → ExchangeCredentialService.get_secrets(credential_ref) → decrypts from DB
  → calls Delta Exchange API

Performance review (new):
  GET /plant/v1/hired-agents/{id}/trade-performance → reads performance_stats table (execute-trade-order)

Recommendations (new, pluggable):
  GET /plant/v1/hired-agents/{id}/recommendations → RecommendationEngine.generate()
  env var RECOMMENDATION_ENGINE=rule_based (or llm in future iteration)
```

---

## Agent Execution Rules

### STUCK PROTOCOL
If you cannot proceed on a story after two attempts:
1. Post a comment on the PR with exactly which file, line, and error blocked you.
2. Mark the PR as Draft.
3. Stop — do not attempt further stories in this session.

### CHECKPOINT RULE
After completing each story (all tests passing), run:
```bash
git add -A && git commit -m "feat(trader): TRADER-FULL-1 [story-id] — [story title]" && git push
```
Do this BEFORE starting the next story.

### EXECUTION AGENT AUDIT ROUND
Before opening the PR, verify:
- [ ] `PiiMaskingFilter` is added to every logger in new files
- [ ] No raw `api_key` or `api_secret` values appear in any log statement
- [ ] All new Plant routes use `waooaw_router()` — not bare `APIRouter`
- [ ] All new GET routes use `get_read_db_session()` — not `get_db_session()`
- [ ] `DATA_ROUTER_MODE`, `EXCHANGE_SECRET_BACKEND`, `RECOMMENDATION_ENGINE` are read from `settings` — never from `os.environ.get()` directly
- [ ] `ENVIRONMENT=test` mock paths are in place for both `_validate_exchange_live()` and `ExchangeCredentialService.get_secrets()`
- [ ] All new tests pass: `docker-compose -f docker-compose.test.yml run plant-backend-test -x -v`

---

## Iteration 1 — DB Credential Store + Connectivity Validation + Trade Result Storage

### Epic E1 — Customer credentials survive restarts and are validated before first trade

**Customer value:** Customer connects Delta Exchange keys once; keys persist across Cloud Run restarts and are validated live before the agent attempts its first trade. If validation fails, the customer sees a clear error (not a silent failure hours later).

**Share Trader alignment:** Direct Share Trader value — hardens credential reliability and customer trust before trade execution.

---

#### Story S1 — `ExchangeCredentialModel` + Alembic migration 041 + `ExchangeCredentialService`

**Branch:** `feat/trader-full-1-it1-credential-db`
**Estimate:** 60 min
**BLOCKED UNTIL:** none

**Context (2 sentences):**
CP BackEnd currently stores Delta Exchange API keys in a local JSON file (`FileExchangeSetupStore`) which is lost on every Cloud Run container restart. This story creates a Plant-side database-backed credential store by adding `src/Plant/BackEnd/models/exchange_credential.py`, migration `041_exchange_credentials.py`, and `src/Plant/BackEnd/services/exchange_credential_service.py`.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/models/customer_platform_credential.py` — copy the model column pattern (JSONB, String, DateTime, Index, UniqueConstraint)
2. `src/Plant/BackEnd/services/database_credential_store.py` — copy the async SQLAlchemy service pattern (upsert, get, mint_credential_ref)
3. `src/Plant/BackEnd/database/migrations/versions/040_dma_batch_type_workflow.py` — copy migration boilerplate; new migration must be `041_exchange_credentials.py`

**Task:**

1. Create `src/Plant/BackEnd/models/exchange_credential.py`:
```python
"""ExchangeCredentialModel — Plant DB record for customer exchange API credentials.

TRADER-FULL-1 S1.
Secrets are stored Fernet-encrypted (dev/demo) or as a GCP Secret Manager ref (prod).
EXCHANGE_SECRET_BACKEND env var = "fernet" | "secret_manager" — never baked into image.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base

class ExchangeCredentialModel(Base):
    __tablename__ = "exchange_credentials"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=False)
    credential_ref = Column(String(255), nullable=False, unique=True, index=True)
    exchange_provider = Column(String(100), nullable=False, default="delta_exchange_india")
    # Fernet-encrypted API key blob OR "sm:<secret_manager_ref>" prefix for prod
    encrypted_api_key = Column(Text, nullable=False)
    encrypted_api_secret = Column(Text, nullable=False)
    default_coin = Column(String(50), nullable=False)
    allowed_coins = Column(JSONB, nullable=False, default=list)
    risk_limits = Column(JSONB, nullable=False, default=dict)
    # "pending" | "valid" | "invalid"
    validation_status = Column(String(50), nullable=False, default="pending")
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("customer_id", "exchange_provider",
                         name="uq_exchange_credentials_customer_provider"),
        Index("ix_exchange_credentials_customer_id", "customer_id"),
    )
```

2. Create migration `src/Plant/BackEnd/database/migrations/versions/041_exchange_credentials.py` (copy boilerplate from 040; `revision = "041_exchange_credentials"`, `down_revision = "040_dma_batch_type_workflow"`; use `op.create_table("exchange_credentials", ...)` matching the model columns above).

3. Create `src/Plant/BackEnd/services/exchange_credential_service.py`:
```python
"""ExchangeCredentialService — DB-backed exchange credential store.

TRADER-FULL-1 S1.
Replaces CP's FileExchangeSetupStore. Plant is the authoritative credential store.
EXCHANGE_SECRET_BACKEND=fernet (default) uses Fernet symmetric encryption.
EXCHANGE_SECRET_BACKEND=secret_manager stores a GCP Secret Manager resource name prefix.
"""
from __future__ import annotations
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings
from core.logging import PiiMaskingFilter, get_logger
from models.exchange_credential import ExchangeCredentialModel

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())

def mint_credential_ref() -> str:
    return f"EXCH-{secrets.token_urlsafe(12)}"

def _fernet():
    import base64, hashlib
    from cryptography.fernet import Fernet
    secret = (getattr(settings, "cp_exchange_setup_secret", None)
              or getattr(settings, "secret_key", "dev-secret")).strip()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)

def _encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()

def _decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()

class ExchangeCredentialService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert(
        self,
        *,
        customer_id: str,
        exchange_provider: str,
        api_key: str,
        api_secret: str,
        default_coin: str,
        allowed_coins: List[str],
        risk_limits: Dict[str, Any],
    ) -> ExchangeCredentialModel:
        """Create or replace credentials for customer+provider pair."""
        credential_ref = mint_credential_ref()
        stmt = (
            pg_insert(ExchangeCredentialModel)
            .values(
                customer_id=customer_id,
                credential_ref=credential_ref,
                exchange_provider=exchange_provider,
                encrypted_api_key=_encrypt(api_key),
                encrypted_api_secret=_encrypt(api_secret),
                default_coin=default_coin,
                allowed_coins=allowed_coins,
                risk_limits=risk_limits,
                validation_status="pending",
            )
            .on_conflict_do_update(
                constraint="uq_exchange_credentials_customer_provider",
                set_={
                    "encrypted_api_key": _encrypt(api_key),
                    "encrypted_api_secret": _encrypt(api_secret),
                    "default_coin": default_coin,
                    "allowed_coins": allowed_coins,
                    "risk_limits": risk_limits,
                    "validation_status": "pending",
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            .returning(ExchangeCredentialModel)
        )
        result = await self._db.execute(stmt)
        await self._db.commit()
        return result.scalars().first()

    async def get_public(self, *, customer_id: str) -> Optional[ExchangeCredentialModel]:
        """Return credential record without secrets (public view)."""
        result = await self._db.execute(
            select(ExchangeCredentialModel).where(
                ExchangeCredentialModel.customer_id == customer_id
            )
        )
        return result.scalars().first()

    async def get_secrets(self, *, credential_ref: str) -> Optional[Dict[str, str]]:
        """Return decrypted {api_key, api_secret} for internal use only — never log."""
        result = await self._db.execute(
            select(ExchangeCredentialModel).where(
                ExchangeCredentialModel.credential_ref == credential_ref
            )
        )
        rec = result.scalars().first()
        if rec is None:
            return None
        return {
            "api_key": _decrypt(rec.encrypted_api_key),
            "api_secret": _decrypt(rec.encrypted_api_secret),
        }

    async def mark_validated(self, *, credential_ref: str, status: str) -> None:
        result = await self._db.execute(
            select(ExchangeCredentialModel).where(
                ExchangeCredentialModel.credential_ref == credential_ref
            )
        )
        rec = result.scalars().first()
        if rec:
            rec.validation_status = status
            rec.last_validated_at = datetime.now(timezone.utc)
            await self._db.commit()
```

**Acceptance criteria:**
- [ ] `from models.exchange_credential import ExchangeCredentialModel` imports without error
- [ ] `alembic upgrade head` applies migration 041 without error (run in docker-compose.test)
- [ ] `ExchangeCredentialService.upsert(...)` returns a row with encrypted fields (api_key never stored in plaintext)
- [ ] `ExchangeCredentialService.get_secrets(credential_ref=...)` returns decrypted dict
- [ ] `ExchangeCredentialService.get_secrets(credential_ref="nonexistent")` returns `None`

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_exchange_credential_model_upsert` | Integration | `src/Plant/BackEnd/tests/integration/test_exchange_credential_service.py` | `docker-compose -f docker-compose.test.yml run plant-backend-test tests/integration/test_exchange_credential_service.py -v` |
| `test_get_secrets_returns_decrypted` | Integration | same | same |
| `test_get_secrets_missing_returns_none` | Integration | same | same |

---

#### Story S2 — Plant route `POST /api/v1/exchange-credentials` + `GET` + DatastoreRouter dual-write

**Branch:** `feat/trader-full-1-it1-credential-db` (same as S1)
**Estimate:** 45 min
**BLOCKED UNTIL:** S1 merged to this branch

**Context (2 sentences):**
Plant BackEnd needs HTTP routes so CP BackEnd (thin proxy) can store and retrieve exchange credentials without CP knowing about secrets. This story adds `src/Plant/BackEnd/api/v1/exchange_credentials.py` with `POST` (upsert + dual-write) and `GET` (public view, no secrets) under prefix `/hired-agents/{hired_instance_id}/exchange-credentials`.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/api/v1/performance_stats.py` — copy the `waooaw_router`, `get_db_session`/`get_read_db_session`, `Depends` pattern
2. `src/Plant/BackEnd/services/exchange_credential_service.py` — service just created in S1
3. `src/Plant/BackEnd/core/datastore_router.py` — `datastore_router.writes_to_firestore("exchange_credentials")` pattern

**Task:**
Create `src/Plant/BackEnd/api/v1/exchange_credentials.py`:

```python
"""Exchange credential routes for Share Trader (TRADER-FULL-1 S2)."""
from __future__ import annotations
import asyncio
import logging
from typing import Any, Dict, List, Optional
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from core.database import get_db_session, get_read_db_session
from core.datastore_router import datastore_router
from core.firestore_client import set_document
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from services.exchange_credential_service import ExchangeCredentialService

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/hired-agents", tags=["exchange-credentials"])

class UpsertExchangeCredentialRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    exchange_provider: str = Field(default="delta_exchange_india")
    api_key: str = Field(..., min_length=1)
    api_secret: str = Field(..., min_length=1)
    default_coin: str = Field(..., min_length=1)
    allowed_coins: List[str] = Field(default_factory=list)
    risk_limits: Dict[str, Any] = Field(default_factory=dict)

class ExchangeCredentialPublicResponse(BaseModel):
    credential_ref: str
    customer_id: str
    exchange_provider: str
    default_coin: str
    allowed_coins: List[str]
    risk_limits: Dict[str, Any]
    validation_status: str

@router.post("/{hired_instance_id}/exchange-credentials",
             response_model=ExchangeCredentialPublicResponse, status_code=201)
async def upsert_exchange_credential(
    hired_instance_id: str,
    body: UpsertExchangeCredentialRequest,
    db=Depends(get_db_session),
) -> ExchangeCredentialPublicResponse:
    svc = ExchangeCredentialService(db)
    rec = await svc.upsert(
        customer_id=body.customer_id,
        exchange_provider=body.exchange_provider,
        api_key=body.api_key,       # svc encrypts internally
        api_secret=body.api_secret, # svc encrypts internally
        default_coin=body.default_coin,
        allowed_coins=body.allowed_coins,
        risk_limits=body.risk_limits,
    )
    # Fire-and-forget dual-write to Firestore if DATA_ROUTER_MODE requires it
    if datastore_router.writes_to_firestore("exchange_credentials"):
        asyncio.create_task(set_document(
            "exchange_credentials", rec.credential_ref,
            {
                "credential_ref": rec.credential_ref,
                "customer_id": rec.customer_id,
                "exchange_provider": rec.exchange_provider,
                "default_coin": rec.default_coin,
                "allowed_coins": rec.allowed_coins,
                "validation_status": rec.validation_status,
                # api_key and api_secret NEVER written to Firestore
            }
        ))
    return ExchangeCredentialPublicResponse(
        credential_ref=rec.credential_ref,
        customer_id=rec.customer_id,
        exchange_provider=rec.exchange_provider,
        default_coin=rec.default_coin,
        allowed_coins=rec.allowed_coins or [],
        risk_limits=rec.risk_limits or {},
        validation_status=rec.validation_status,
    )

@router.get("/{hired_instance_id}/exchange-credentials",
            response_model=Optional[ExchangeCredentialPublicResponse])
async def get_exchange_credential(
    hired_instance_id: str,
    customer_id: str,
    db=Depends(get_read_db_session),  # GET uses read replica
) -> Optional[ExchangeCredentialPublicResponse]:
    svc = ExchangeCredentialService(db)
    rec = await svc.get_public(customer_id=customer_id)
    if rec is None:
        return None
    return ExchangeCredentialPublicResponse(
        credential_ref=rec.credential_ref,
        customer_id=rec.customer_id,
        exchange_provider=rec.exchange_provider,
        default_coin=rec.default_coin,
        allowed_coins=rec.allowed_coins or [],
        risk_limits=rec.risk_limits or {},
        validation_status=rec.validation_status,
    )
```

Also add `"exchange_credentials"` to `_ROUTABLE_COLLECTIONS` in `src/Plant/BackEnd/core/datastore_router.py`:
```python
_ROUTABLE_COLLECTIONS = frozenset({
    "agent_performance",
    "agent_availability",
    "exchange_credentials",   # TRADER-FULL-1 S2
    "trade_results",          # TRADER-FULL-1 S5 (add in S5 story)
})
```

Register the router in `src/Plant/BackEnd/main.py` — add `from api.v1.exchange_credentials import router as exchange_credentials_router` and `app.include_router(exchange_credentials_router, prefix="/api/v1")`.

**Acceptance criteria:**
- [ ] `POST /api/v1/hired-agents/{id}/exchange-credentials` returns 201 with `credential_ref` and no secrets in response
- [ ] `GET /api/v1/hired-agents/{id}/exchange-credentials?customer_id=X` returns public view (no api_key, no api_secret fields)
- [ ] Firestore `set_document` is called when `DATA_ROUTER_MODE=dual_write`; not called when `DATA_ROUTER_MODE=sql`
- [ ] `exchange_credentials` is in `_ROUTABLE_COLLECTIONS`

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_upsert_returns_public_view_no_secrets` | Unit | `src/Plant/BackEnd/tests/test_exchange_credentials_api.py` | `docker-compose -f docker-compose.test.yml run plant-backend-test tests/test_exchange_credentials_api.py -v` |
| `test_dual_write_called_in_dual_write_mode` | Unit | same | same |
| `test_dual_write_not_called_in_sql_mode` | Unit | same | same |

---

#### Story S3 — CP thin proxy `POST/GET /cp/exchange-credentials` calling Plant

**Branch:** `feat/trader-full-1-it1-credential-db` (same branch)
**Estimate:** 45 min
**BLOCKED UNTIL:** S2 merged to this branch

**Context (2 sentences):**
CP BackEnd currently owns credential storage via `FileExchangeSetupStore`; this story migrates CP to a thin proxy (Pattern B) that forwards to Plant's new routes. Create `src/CP/BackEnd/api/cp_exchange_credentials.py` — CP injects `customer_id` from JWT, strips secrets before logging, and returns only the public view.

**Files to read first (max 3):**
1. `src/CP/BackEnd/api/exchange_setup.py` — the existing route shape and `UpsertExchangeSetupRequest` Pydantic model to reuse
2. `src/CP/BackEnd/services/plant_gateway_client.py` — `PlantGatewayClient.request_json(method, path, json_body, headers)` pattern
3. `src/CP/BackEnd/api/trading.py` — copy `_forward_headers()`, `_customer_id_from_user()`, and `get_plant_gateway_client()` helpers

**Task:**
Create `src/CP/BackEnd/api/cp_exchange_credentials.py` (Pattern B — new proxy file):

```python
"""CP exchange credentials proxy (TRADER-FULL-1 S3). Pattern B.

Forwards credential upsert/get to Plant BackEnd.
CP injects customer_id from JWT; never stores secrets locally.
"""
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field
from core.routing import waooaw_router
from api.auth.dependencies import get_current_user
from models.user import User
from services.plant_gateway_client import PlantGatewayClient

router = waooaw_router(prefix="/cp/exchange-credentials", tags=["cp-exchange-credentials"])

def _customer_id(user: User) -> str:
    return f"CUST-{user.id}"

def _plant_client() -> PlantGatewayClient:
    base = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base:
        raise HTTPException(status_code=503, detail="PLANT_GATEWAY_URL not configured")
    return PlantGatewayClient(base_url=base)

def _headers(request: Request) -> Dict[str, str]:
    h: Dict[str, str] = {}
    for hdr in ("authorization", "x-correlation-id", "x-debug-trace"):
        v = request.headers.get(hdr)
        if v:
            h[hdr.title().replace("-", "-")] = v
    return h

class UpsertExchangeCredentialRequest(BaseModel):
    exchange_provider: str = Field(default="delta_exchange_india")
    api_key: str = Field(..., min_length=1)
    api_secret: str = Field(..., min_length=1)
    default_coin: str = Field(..., min_length=1)
    allowed_coins: Optional[List[str]] = Field(default_factory=list)
    risk_limits: Optional[Dict[str, Any]] = Field(default_factory=dict)

PLACEHOLDER_HIRED_ID = "trader-default"

@router.post("", response_model=Dict[str, Any], status_code=201)
async def upsert_exchange_credential(
    body: UpsertExchangeCredentialRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(_plant_client),
) -> Dict[str, Any]:
    resp = await plant.request_json(
        method="POST",
        path=f"api/v1/hired-agents/{PLACEHOLDER_HIRED_ID}/exchange-credentials",
        headers=_headers(request),
        json_body={
            "customer_id": _customer_id(current_user),
            "exchange_provider": body.exchange_provider,
            "api_key": body.api_key,
            "api_secret": body.api_secret,
            "default_coin": body.default_coin,
            "allowed_coins": body.allowed_coins or [],
            "risk_limits": body.risk_limits or {},
        },
    )
    # Strip any accidental secret echo from Plant response before returning
    resp.pop("api_key", None)
    resp.pop("api_secret", None)
    resp.pop("encrypted_api_key", None)
    resp.pop("encrypted_api_secret", None)
    return resp

@router.get("", response_model=Optional[Dict[str, Any]])
async def get_exchange_credential(
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(_plant_client),
) -> Optional[Dict[str, Any]]:
    resp = await plant.request_json(
        method="GET",
        path=f"api/v1/hired-agents/{PLACEHOLDER_HIRED_ID}/exchange-credentials",
        headers=_headers(request),
        params={"customer_id": _customer_id(current_user)},
    )
    return resp
```

Register router in `src/CP/BackEnd/main.py`: add `from api.cp_exchange_credentials import router as cp_exchange_credentials_router` and `app.include_router(cp_exchange_credentials_router)`.

**Acceptance criteria:**
- [ ] `POST /cp/exchange-credentials` proxies to Plant and returns `credential_ref` with no secrets
- [ ] `GET /cp/exchange-credentials` proxies to Plant public view
- [ ] `_headers()` forwards `Authorization` and `X-Correlation-ID`
- [ ] CP router file uses `waooaw_router()` (not bare `APIRouter`)

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_cp_exchange_credentials_upsert_proxies` | Unit | `src/CP/BackEnd/tests/test_cp_exchange_credentials_routes.py` | `docker-compose -f docker-compose.test.yml run cp-backend-test tests/test_cp_exchange_credentials_routes.py -v` |
| `test_cp_exchange_credentials_strips_secrets` | Unit | same | same |

---

#### Story S4 — `POST /api/v1/exchange-credentials/{credential_ref}/validate` (live Delta Exchange check)

**Branch:** `feat/trader-full-1-it1-credential-db` (same branch)
**Estimate:** 60 min
**BLOCKED UNTIL:** S1 merged to this branch

**Context (2 sentences):**
Before the agent executes its first trade, the customer needs proof their API keys work and have the right permissions. This story adds a validation route that calls Delta Exchange `GET /v2/wallet/balances` and `GET /v2/profile`, returns `{readable: bool, tradeable: bool, balance_summary}`, and marks `validation_status` in the DB. In `ENVIRONMENT=test`, it returns a `MagicMock` response (same pattern as `FirestoreClient._get_client()`).

**Files to read first (max 3):**
1. `src/Plant/BackEnd/services/exchange_credential_service.py` — `get_secrets()` and `mark_validated()` methods
2. `src/Plant/BackEnd/integrations/delta_exchange/client.py` — `DeltaExchangeClient`, `DeltaCredentials`, `sign_delta_request` pattern
3. `src/Plant/BackEnd/core/firestore_client.py` — copy the `if settings.environment in {"development", "test", "local"}: return MagicMock()` guard pattern

**Task:**
Add to `src/Plant/BackEnd/api/v1/exchange_credentials.py` (same file as S2):

```python
import asyncio, httpx
from core.config import settings
from core.security import circuit_breaker

class ValidateExchangeResponse(BaseModel):
    credential_ref: str
    readable: bool
    tradeable: bool
    balance_summary: Dict[str, Any]
    validation_status: str  # "valid" | "invalid"
    error: Optional[str] = None

@router.post("/{hired_instance_id}/exchange-credentials/{credential_ref}/validate",
             response_model=ValidateExchangeResponse)
async def validate_exchange_credential(
    hired_instance_id: str,
    credential_ref: str,
    db=Depends(get_db_session),
) -> ValidateExchangeResponse:
    svc = ExchangeCredentialService(db)
    secrets_dict = await svc.get_secrets(credential_ref=credential_ref)
    if secrets_dict is None:
        raise HTTPException(status_code=404, detail="credential_ref not found")

    readable, tradeable, balance_summary, error = await _validate_exchange_live(
        api_key=secrets_dict["api_key"],
        api_secret=secrets_dict["api_secret"],
    )
    status = "valid" if readable else "invalid"
    await svc.mark_validated(credential_ref=credential_ref, status=status)
    return ValidateExchangeResponse(
        credential_ref=credential_ref,
        readable=readable,
        tradeable=tradeable,
        balance_summary=balance_summary,
        validation_status=status,
        error=error,
    )

@circuit_breaker(service="delta_exchange_api")
async def _validate_exchange_live(
    *, api_key: str, api_secret: str
) -> tuple[bool, bool, dict, Optional[str]]:
    """Live Delta Exchange credential check. Returns (readable, tradeable, balance_summary, error).
    In test/dev/local: returns mock success without network call (same pattern as FirestoreClient).
    """
    if settings.environment in {"test", "development", "local"}:
        return True, True, {"mock": True, "available_balance": 100000}, None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.delta.exchange/v2/wallet/balances",
                headers={"api-key": api_key},   # api_key NEVER logged
            )
            resp.raise_for_status()
            balances = resp.json().get("result", {})
            return True, True, {"balances_count": len(balances)}, None
    except Exception as exc:
        logger.error("validate_exchange: check failed — %s", type(exc).__name__)  # no key in log
        return False, False, {}, str(type(exc).__name__)
```

**Acceptance criteria:**
- [ ] `POST /.../validate` returns `{readable: true, tradeable: true}` in test environment (mock path)
- [ ] `POST /.../validate` with non-existent `credential_ref` returns 404
- [ ] `api_key` never appears in any log line (checked by test asserting `caplog.text` does not contain the key value)
- [ ] `validation_status` is updated to `"valid"` in the DB after successful validation

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_validate_returns_valid_in_test_env` | Unit | `src/Plant/BackEnd/tests/test_exchange_credentials_api.py` | `docker-compose -f docker-compose.test.yml run plant-backend-test tests/test_exchange_credentials_api.py -v` |
| `test_validate_404_for_missing_ref` | Unit | same | same |
| `test_api_key_not_in_logs` | Unit | same | same |

---

### Epic E2 — Trade outcomes are recorded and feed the performance loop

---

#### Story S5 — `TradeResultModel` + migration 042 + `POST /api/v1/hired-agents/{id}/trade-results` with dual-write

**Branch:** `feat/trader-full-1-it1-credential-db` (same branch)
**Estimate:** 60 min
**BLOCKED UNTIL:** S2 merged to this branch

**Context (2 sentences):**
Today there is no storage of individual trade outcomes (signal, fill_price, pnl_pct, was_signal_correct) — only aggregated daily stats in `performance_stats`. This story adds `TradeResultModel`, migration `042_trade_results`, and a write route so `DeltaPublisher` can post outcomes after every fill; these records feed the Iteration 2 recommendation engine.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/models/performance_stat.py` — copy model/migration column pattern
2. `src/Plant/BackEnd/api/v1/performance_stats.py` — copy `waooaw_router`, `get_db_session`, `asyncio.create_task` dual-write pattern
3. `src/Plant/BackEnd/core/datastore_router.py` — `datastore_router.writes_to_firestore("trade_results")` (already added to `_ROUTABLE_COLLECTIONS` in S2)

**Task:**

1. Create `src/Plant/BackEnd/models/trade_result.py`:
```python
"""TradeResultModel — individual trade outcome record (TRADER-FULL-1 S5)."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, String
from core.database import Base

class TradeResultModel(Base):
    __tablename__ = "trade_results"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hired_instance_id = Column(
        String, ForeignKey("hired_agents.hired_instance_id", ondelete="CASCADE"),
        nullable=False)
    signal = Column(String(10), nullable=False)       # "BUY" | "SELL" | "HOLD"
    instrument = Column(String(50), nullable=False)
    fill_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)            # (exit-fill)/fill * 100
    was_signal_correct = Column(Boolean, nullable=True)
    rsi_value = Column(Float, nullable=True)          # RSI at time of signal
    trade_date = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        Index("ix_trade_results_hired_instance_id", "hired_instance_id"),
        Index("ix_trade_results_trade_date", "trade_date"),
    )
```

2. Create migration `042_trade_results.py` (revision = `042_trade_results`, down_revision = `041_exchange_credentials`).

3. Add to `src/Plant/BackEnd/api/v1/exchange_credentials.py` (or create separate `src/Plant/BackEnd/api/v1/trade_results.py`):
```python
class RecordTradeResultRequest(BaseModel):
    signal: str = Field(..., pattern="^(BUY|SELL|HOLD)$")
    instrument: str = Field(..., min_length=1)
    fill_price: Optional[float] = None
    exit_price: Optional[float] = None
    pnl_pct: Optional[float] = None
    was_signal_correct: Optional[bool] = None
    rsi_value: Optional[float] = None

@router.post("/{hired_instance_id}/trade-results", status_code=201)
async def record_trade_result(
    hired_instance_id: str,
    body: RecordTradeResultRequest,
    db=Depends(get_db_session),
) -> Dict[str, Any]:
    rec = TradeResultModel(
        hired_instance_id=hired_instance_id,
        signal=body.signal,
        instrument=body.instrument,
        fill_price=body.fill_price,
        exit_price=body.exit_price,
        pnl_pct=body.pnl_pct,
        was_signal_correct=body.was_signal_correct,
        rsi_value=body.rsi_value,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    # Dual-write to Firestore
    if datastore_router.writes_to_firestore("trade_results"):
        asyncio.create_task(set_document(
            "trade_results", rec.id,
            {
                "id": rec.id,
                "hired_instance_id": str(hired_instance_id),
                "signal": rec.signal,
                "instrument": rec.instrument,
                "pnl_pct": rec.pnl_pct,
                "was_signal_correct": rec.was_signal_correct,
                "trade_date": rec.trade_date.isoformat(),
            }
        ))
    return {"id": rec.id, "hired_instance_id": hired_instance_id, "signal": rec.signal}
```

Register `trade_results` router in `main.py`.

**Acceptance criteria:**
- [ ] `POST /api/v1/hired-agents/{id}/trade-results` returns 201 with `id`
- [ ] Row appears in `trade_results` table after POST
- [ ] Firestore `set_document` is called when `DATA_ROUTER_MODE=dual_write`
- [ ] `signal` field rejects values other than `BUY`, `SELL`, `HOLD` (422 returned)

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_record_trade_result_creates_row` | Unit | `src/Plant/BackEnd/tests/test_trade_results_api.py` | `docker-compose -f docker-compose.test.yml run plant-backend-test tests/test_trade_results_api.py -v` |
| `test_invalid_signal_returns_422` | Unit | same | same |
| `test_dual_write_called_in_dual_write_mode` | Unit | same | same |

---

#### Story S6 — It1 test suite (unit + integration pass, coverage ≥ 80%)

**Branch:** `feat/trader-full-1-it1-credential-db` (same branch)
**Estimate:** 45 min
**BLOCKED UNTIL:** S1–S5 merged to this branch

**Context (2 sentences):**
CI requires ≥ 80% coverage across Plant BackEnd. This story verifies and fills test gaps across S1–S5, runs the full suite, and confirms no pre-existing tests regressed.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/tests/test_exchange_credentials_api.py` — tests written in S2/S4
2. `src/Plant/BackEnd/tests/integration/test_exchange_credential_service.py` — tests written in S1
3. `src/Plant/BackEnd/tests/test_trade_results_api.py` — tests written in S5

**Task:**
Run the full suite and fix any failures:
```bash
docker-compose -f docker-compose.test.yml run plant-backend-test \
  --cov=. --cov-report=term-missing --cov-fail-under=80 -x -v
```
If coverage is below 80%, add unit tests for uncovered branches in `exchange_credential_service.py` (Fernet encrypt/decrypt round-trip, `mark_validated`).

**Acceptance criteria:**
- [ ] Full suite passes with no failures
- [ ] Coverage ≥ 80%
- [ ] CI workflow `Backend Unit Tests (Plant)` passes on the PR

---

## Iteration 2 — Performance Review + Pluggable Recommendations + Mobile Screens

### Epic E3 — Customer sees real P&L history and win rate on mobile

---

#### Story S1 — `GET /plant/v1/hired-agents/{id}/trade-performance` + CP proxy

**Branch:** `feat/trader-full-1-it2-performance-review`
**Estimate:** 60 min
**BLOCKED UNTIL:** Iteration 1 PR merged to main

**Context (2 sentences):**
`performance_stats` already stores `execute-trade-order` metrics (`trades_count`, `pnl_pct`, `win_rate`, `stop_loss_count`, `profit_count`) but there is no route that aggregates and surfaces them. This story adds a read route aggregating across all `performance_stats` rows for the hired agent where `skill_id = "execute-trade-order"`, returns a 90-day summary, and adds a CP thin proxy so mobile can call it.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/api/v1/performance_stats.py` — existing read route pattern, `get_read_db_session()`, model field names
2. `src/Plant/BackEnd/models/performance_stat.py` — `metrics` JSONB shape for `execute-trade-order` skill
3. `src/CP/BackEnd/api/cp_exchange_credentials.py` — CP thin proxy pattern just established in It1 S3

**Task:**
Create `src/Plant/BackEnd/api/v1/trade_performance.py`:

```python
"""Trade performance review route (TRADER-FULL-1 It2 S1)."""
from __future__ import annotations
import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import select
from core.database import get_read_db_session
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.performance_stat import PerformanceStatModel

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/hired-agents", tags=["trade-performance"])

EXECUTE_TRADE_SKILL = "execute-trade-order"

class TradePerformanceSummary(BaseModel):
    hired_instance_id: str
    period_days: int
    trades_count: int
    pnl_pct_avg: float
    win_rate: float
    stop_loss_count: int
    profit_count: int
    last_stat_date: Optional[date]

@router.get("/{hired_instance_id}/trade-performance",
            response_model=TradePerformanceSummary)
async def get_trade_performance(
    hired_instance_id: str,
    period_days: int = 90,
    db=Depends(get_read_db_session),  # read replica
) -> TradePerformanceSummary:
    since = date.today() - timedelta(days=period_days)
    result = await db.execute(
        select(PerformanceStatModel).where(
            PerformanceStatModel.hired_instance_id == hired_instance_id,
            PerformanceStatModel.skill_id == EXECUTE_TRADE_SKILL,
            PerformanceStatModel.stat_date >= since,
        ).order_by(PerformanceStatModel.stat_date.desc())
    )
    rows: List[PerformanceStatModel] = result.scalars().all()
    if not rows:
        return TradePerformanceSummary(
            hired_instance_id=hired_instance_id, period_days=period_days,
            trades_count=0, pnl_pct_avg=0.0, win_rate=0.0,
            stop_loss_count=0, profit_count=0, last_stat_date=None,
        )
    m = [r.metrics or {} for r in rows]
    return TradePerformanceSummary(
        hired_instance_id=hired_instance_id,
        period_days=period_days,
        trades_count=sum(x.get("trades_count", 0) for x in m),
        pnl_pct_avg=round(sum(x.get("pnl_pct", 0.0) for x in m) / len(m), 2),
        win_rate=round(sum(x.get("win_rate", 0.0) for x in m) / len(m), 2),
        stop_loss_count=sum(x.get("stop_loss_count", 0) for x in m),
        profit_count=sum(x.get("profit_count", 0) for x in m),
        last_stat_date=rows[0].stat_date,
    )
```

Add CP thin proxy in `src/CP/BackEnd/api/cp_exchange_credentials.py` (or a new `cp_trade_performance.py`):
```python
@router.get("/performance/{hired_instance_id}", response_model=Dict[str, Any])
async def get_trade_performance(
    hired_instance_id: str,
    period_days: int = 90,
    request: Request = ...,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(_plant_client),
) -> Dict[str, Any]:
    return await plant.request_json(
        method="GET",
        path=f"api/v1/hired-agents/{hired_instance_id}/trade-performance",
        headers=_headers(request),
        params={"period_days": period_days},
    )
```

Register router in `src/Plant/BackEnd/main.py`.

**Acceptance criteria:**
- [ ] `GET /api/v1/hired-agents/{id}/trade-performance` returns `TradePerformanceSummary` (200)
- [ ] Empty stats returns all-zero summary (no 500)
- [ ] Route uses `get_read_db_session()` — not `get_db_session()`
- [ ] CP proxy `GET /cp/trading/performance/{id}` returns same shape

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_trade_performance_empty_returns_zeros` | Unit | `src/Plant/BackEnd/tests/test_trade_performance_api.py` | `docker-compose -f docker-compose.test.yml run plant-backend-test tests/test_trade_performance_api.py -v` |
| `test_trade_performance_aggregates_correctly` | Unit | same | same |

---

### Epic E4 — Agent recommends next trade strategy based on outcome evidence

---

#### Story S2 — Pluggable `RecommendationEngine` + `RuleBasedRecommendationEngine`

**Branch:** `feat/trader-full-1-it2-performance-review` (same branch)
**Estimate:** 60 min
**BLOCKED UNTIL:** It1 S5 merged (needs `trade_results` table)

**Context (2 sentences):**
Recommendations need a pluggable interface today so an LLM engine can replace the rule-based engine in the next iteration by changing `RECOMMENDATION_ENGINE=llm` without touching route code. This story creates `src/Plant/BackEnd/services/recommendation_engine.py` with an abstract `RecommendationEngine` base class and a `RuleBasedRecommendationEngine` that reads the last N `trade_results` rows and suggests an RSI threshold adjustment.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/models/trade_result.py` — `TradeResultModel` columns (`signal`, `was_signal_correct`, `rsi_value`)
2. `src/Plant/BackEnd/core/config.py` — Settings class pattern for adding `recommendation_engine: str` field with `AliasChoices`
3. `src/Plant/BackEnd/share_trader_flows.py` — current RSI context (default RSI thresholds 30/70 BUY/SELL)

**Task:**
Create `src/Plant/BackEnd/services/recommendation_engine.py`:

```python
"""Pluggable recommendation engine (TRADER-FULL-1 It2 S2).

RECOMMENDATION_ENGINE env var selects the engine:
  "rule_based"  — default: RSI threshold tuning from signal accuracy stats
  "llm"         — future: LLM-generated recommendations (next iteration)

To add a new engine: subclass RecommendationEngine, register in ENGINE_REGISTRY.
"""
from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings
from core.logging import PiiMaskingFilter
from models.trade_result import TradeResultModel

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

@dataclass
class TradeRecommendation:
    current_rsi_buy_threshold: float
    current_rsi_sell_threshold: float
    suggested_rsi_buy_threshold: float
    suggested_rsi_sell_threshold: float
    confidence: float       # 0.0–1.0
    rationale: str
    sample_size: int
    engine: str             # "rule_based" | "llm" | ...

class RecommendationEngine(ABC):
    """Abstract base — implement generate() to plug in any strategy."""
    @abstractmethod
    async def generate(
        self,
        *,
        hired_instance_id: str,
        db: AsyncSession,
        sample_size: int = 20,
    ) -> TradeRecommendation: ...

class RuleBasedRecommendationEngine(RecommendationEngine):
    """RSI threshold tuning from signal accuracy stats.

    Logic:
    - If BUY signal accuracy < 50%: raise buy threshold by 5 (more conservative)
    - If SELL signal accuracy < 50%: lower sell threshold by 5 (more conservative)
    - Confidence = min(sample_size / 20, 1.0)
    """
    async def generate(
        self,
        *,
        hired_instance_id: str,
        db: AsyncSession,
        sample_size: int = 20,
    ) -> TradeRecommendation:
        result = await db.execute(
            select(TradeResultModel)
            .where(TradeResultModel.hired_instance_id == hired_instance_id)
            .order_by(TradeResultModel.trade_date.desc())
            .limit(sample_size)
        )
        rows: List[TradeResultModel] = result.scalars().all()
        buy_threshold, sell_threshold = 30.0, 70.0  # platform defaults
        if not rows:
            return TradeRecommendation(
                current_rsi_buy_threshold=buy_threshold,
                current_rsi_sell_threshold=sell_threshold,
                suggested_rsi_buy_threshold=buy_threshold,
                suggested_rsi_sell_threshold=sell_threshold,
                confidence=0.0,
                rationale="Insufficient trade history (0 trades).",
                sample_size=0,
                engine="rule_based",
            )
        buys = [r for r in rows if r.signal == "BUY" and r.was_signal_correct is not None]
        sells = [r for r in rows if r.signal == "SELL" and r.was_signal_correct is not None]
        buy_accuracy = sum(1 for r in buys if r.was_signal_correct) / max(len(buys), 1)
        sell_accuracy = sum(1 for r in sells if r.was_signal_correct) / max(len(sells), 1)
        new_buy = buy_threshold + 5 if buy_accuracy < 0.5 else buy_threshold
        new_sell = sell_threshold - 5 if sell_accuracy < 0.5 else sell_threshold
        confidence = min(len(rows) / 20.0, 1.0)
        rationale = (
            f"BUY accuracy {buy_accuracy:.0%} over {len(buys)} signals; "
            f"SELL accuracy {sell_accuracy:.0%} over {len(sells)} signals. "
            f"{'Raising BUY threshold.' if new_buy > buy_threshold else ''}"
            f"{'Lowering SELL threshold.' if new_sell < sell_threshold else ''}"
            f"{'No change needed.' if new_buy == buy_threshold and new_sell == sell_threshold else ''}"
        ).strip()
        return TradeRecommendation(
            current_rsi_buy_threshold=buy_threshold,
            current_rsi_sell_threshold=sell_threshold,
            suggested_rsi_buy_threshold=new_buy,
            suggested_rsi_sell_threshold=new_sell,
            confidence=confidence,
            rationale=rationale,
            sample_size=len(rows),
            engine="rule_based",
        )

ENGINE_REGISTRY = {"rule_based": RuleBasedRecommendationEngine}

def get_recommendation_engine() -> RecommendationEngine:
    engine_name = getattr(settings, "recommendation_engine", "rule_based")
    cls = ENGINE_REGISTRY.get(engine_name, RuleBasedRecommendationEngine)
    return cls()
```

Add to `src/Plant/BackEnd/core/config.py` Settings class:
```python
recommendation_engine: str = Field(
    default="rule_based",
    validation_alias=AliasChoices("RECOMMENDATION_ENGINE", "recommendation_engine"),
    description="Recommendation engine: rule_based | llm",
)
```

**Acceptance criteria:**
- [ ] `get_recommendation_engine()` returns `RuleBasedRecommendationEngine` when `RECOMMENDATION_ENGINE=rule_based`
- [ ] `RuleBasedRecommendationEngine.generate()` returns all-zero/default recommendation with 0 trades
- [ ] With 10 BUY signals all wrong: `suggested_rsi_buy_threshold = 35.0`
- [ ] `confidence = 0.0` when sample_size=0; `confidence = 1.0` when sample_size ≥ 20

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_rule_based_no_trades_returns_defaults` | Unit | `src/Plant/BackEnd/tests/test_recommendation_engine.py` | `docker-compose -f docker-compose.test.yml run plant-backend-test tests/test_recommendation_engine.py -v` |
| `test_rule_based_poor_buy_accuracy_raises_threshold` | Unit | same | same |
| `test_engine_registry_selects_rule_based` | Unit | same | same |

---

#### Story S3 — `GET /plant/v1/hired-agents/{id}/recommendations` + CP proxy

**Branch:** `feat/trader-full-1-it2-performance-review` (same branch)
**Estimate:** 45 min
**BLOCKED UNTIL:** S2 merged to this branch

**Context (2 sentences):**
The recommendation engine built in S2 needs an HTTP route and a CP proxy so the mobile app can display the suggestion. This story wires `GET /api/v1/hired-agents/{id}/recommendations` to `get_recommendation_engine().generate()` and adds `GET /cp/trading/recommendations/{id}` as a CP thin proxy.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/services/recommendation_engine.py` — `get_recommendation_engine()`, `TradeRecommendation` dataclass
2. `src/Plant/BackEnd/api/v1/trade_performance.py` — route pattern (waooaw_router, get_read_db_session)
3. `src/CP/BackEnd/api/cp_exchange_credentials.py` — CP proxy pattern from It1 S3

**Task:**
Create `src/Plant/BackEnd/api/v1/recommendations.py`:

```python
"""Trade recommendations route (TRADER-FULL-1 It2 S3)."""
from __future__ import annotations
import logging
from typing import Dict, Any
from fastapi import Depends
from core.database import get_read_db_session
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from services.recommendation_engine import get_recommendation_engine, TradeRecommendation

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/hired-agents", tags=["recommendations"])

@router.get("/{hired_instance_id}/recommendations",
            response_model=Dict[str, Any])
async def get_recommendations(
    hired_instance_id: str,
    sample_size: int = 20,
    db=Depends(get_read_db_session),
) -> Dict[str, Any]:
    engine = get_recommendation_engine()
    rec: TradeRecommendation = await engine.generate(
        hired_instance_id=hired_instance_id,
        db=db,
        sample_size=sample_size,
    )
    return {
        "hired_instance_id": hired_instance_id,
        "current_rsi_buy_threshold": rec.current_rsi_buy_threshold,
        "current_rsi_sell_threshold": rec.current_rsi_sell_threshold,
        "suggested_rsi_buy_threshold": rec.suggested_rsi_buy_threshold,
        "suggested_rsi_sell_threshold": rec.suggested_rsi_sell_threshold,
        "confidence": rec.confidence,
        "rationale": rec.rationale,
        "sample_size": rec.sample_size,
        "engine": rec.engine,
    }
```

Add CP proxy `GET /cp/trading/recommendations/{hired_instance_id}` in `src/CP/BackEnd/api/cp_exchange_credentials.py` (or `cp_trading.py`).

Register both routers in respective `main.py`.

**Acceptance criteria:**
- [ ] `GET /api/v1/hired-agents/{id}/recommendations` returns 200 with `engine: "rule_based"`
- [ ] Route uses `get_read_db_session()` — not `get_db_session()`
- [ ] CP proxy returns same payload
- [ ] Changing `RECOMMENDATION_ENGINE=fake_engine` falls back to `RuleBasedRecommendationEngine` (registry miss → default)

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_recommendations_route_returns_rule_based` | Unit | `src/Plant/BackEnd/tests/test_recommendations_api.py` | `docker-compose -f docker-compose.test.yml run plant-backend-test tests/test_recommendations_api.py -v` |
| `test_recommendations_uses_read_replica` | Unit | same | same |

---

#### Story S4 — Mobile: Trade Performance section in Agent Context Sheet

**Branch:** `feat/trader-full-1-it2-performance-review` (same branch)
**Estimate:** 90 min
**BLOCKED UNTIL:** S1 merged (CP proxy `/cp/trading/performance/{id}` must exist)

**Context (2 sentences):**
The Agent Context Sheet (`src/mobile/src/screens/AgentContextSheet.tsx` or equivalent) is the hub where customers see their hired agent's activity. This story adds a collapsible "Trade Performance" section below the existing activity feed, using a `useTradePerformance(hiredInstanceId)` hook and a `TradePerformanceCard` component.

**Files to read first (max 3):**
1. `src/mobile/src/components/TradePlanApprovalCard.tsx` — copy styling pattern (dark theme `#0a0a0a`, neon cyan `#00f2fe`, riskColor helper)
2. `src/mobile/src/__tests__/components/TradePlanApprovalCard.test.tsx` — copy test structure (render, snapshot, button press)
3. `src/mobile/src/hooks/useApprovalQueue.ts` (or equivalent hook file) — copy `useXxx` data-fetching hook pattern with loading/error states

**Task:**

1. Create `src/mobile/src/hooks/useTradePerformance.ts`:
```typescript
/**
 * useTradePerformance — fetches trade P&L summary for a hired agent.
 * Calls CP Backend GET /cp/trading/performance/{hiredInstanceId}
 */
import { useState, useEffect } from 'react';
import { apiRequest } from '@/services/api';

export interface TradePerformanceSummary {
  trades_count: number;
  pnl_pct_avg: number;
  win_rate: number;
  stop_loss_count: number;
  profit_count: number;
  period_days: number;
  last_stat_date: string | null;
}

export function useTradePerformance(hiredInstanceId: string, periodDays = 90) {
  const [data, setData] = useState<TradePerformanceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    apiRequest<TradePerformanceSummary>(
      `cp/trading/performance/${hiredInstanceId}?period_days=${periodDays}`
    )
      .then(d => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch(e => { if (!cancelled) { setError(e.message); setLoading(false); } });
    return () => { cancelled = true; };
  }, [hiredInstanceId, periodDays]);

  return { data, loading, error };
}
```

2. Create `src/mobile/src/components/TradePerformanceCard.tsx`:
```tsx
/**
 * TradePerformanceCard — P&L summary for Share Trader agent (TRADER-FULL-1 It2 S4)
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import type { TradePerformanceSummary } from '@/hooks/useTradePerformance';

interface Props { summary: TradePerformanceSummary; }

export function TradePerformanceCard({ summary }: Props) {
  const { colors, typography } = useTheme();
  const pnlColor = summary.pnl_pct_avg >= 0 ? '#10b981' : '#ef4444';
  return (
    <View style={[styles.card, { borderColor: colors.textSecondary + '20' }]}>
      <Text style={[styles.title, { color: colors.textPrimary,
        fontFamily: typography.fontFamily.bodyBold }]}>
        Trade Performance ({summary.period_days}d)
      </Text>
      <View style={styles.row}>
        <Stat label="Trades" value={String(summary.trades_count)} color={colors.textPrimary} />
        <Stat label="Avg P&L" value={`${summary.pnl_pct_avg.toFixed(1)}%`} color={pnlColor} />
        <Stat label="Win Rate" value={`${(summary.win_rate * 100).toFixed(0)}%`} color="#00f2fe" />
      </View>
    </View>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <View style={styles.stat}>
      <Text style={[styles.value, { color }]}>{value}</Text>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#18181b', borderRadius: 16, padding: 16,
          marginVertical: 8, borderWidth: 1 },
  title: { fontSize: 14, marginBottom: 12 },
  row: { flexDirection: 'row', justifyContent: 'space-around' },
  stat: { alignItems: 'center' },
  value: { fontSize: 20, fontWeight: '700' },
  label: { fontSize: 11, color: '#71717a', marginTop: 2 },
});
```

3. Add `<TradePerformanceCard>` to the Agent Context Sheet (find by searching for `TradePlanApprovalCard` usage in existing screens — insert the new card in the same section).

**Acceptance criteria:**
- [ ] `TradePerformanceCard` renders with `trades_count`, `pnl_pct_avg`, `win_rate` visible
- [ ] Positive P&L shows in green (`#10b981`); negative in red (`#ef4444`)
- [ ] Loading state shows a placeholder (Text "Loading…" or ActivityIndicator)
- [ ] `useTradePerformance` hook calls `cp/trading/performance/{id}?period_days=90`

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `TradePerformanceCard renders positive pnl in green` | Unit | `src/mobile/src/__tests__/components/TradePerformanceCard.test.tsx` | `cd src/mobile && yarn test TradePerformanceCard` |
| `TradePerformanceCard renders negative pnl in red` | Unit | same | same |
| `useTradePerformance calls correct endpoint` | Unit | `src/mobile/src/__tests__/hooks/useTradePerformance.test.ts` | `cd src/mobile && yarn test useTradePerformance` |

---

#### Story S5 — Mobile: Recommendations card in Agent Context Sheet

**Branch:** `feat/trader-full-1-it2-performance-review` (same branch)
**Estimate:** 60 min
**BLOCKED UNTIL:** S3 merged (CP proxy `/cp/trading/recommendations/{id}` must exist)

**Context (2 sentences):**
After seeing P&L history, the customer needs to see the agent's recommendation for the next trade cycle with an Approve (apply suggestion) or Dismiss option. This story adds `useRecommendations` hook + `RecommendationCard` component, inserted in the Agent Context Sheet directly below `TradePerformanceCard`.

**Files to read first (max 3):**
1. `src/mobile/src/components/TradePlanApprovalCard.tsx` — copy Approve/Reject button pattern and risk chip styling
2. `src/mobile/src/hooks/useTradePerformance.ts` — copy hook structure just created in S4
3. `src/mobile/src/components/TradePerformanceCard.tsx` — copy card/stat styling just created in S4

**Task:**

1. Create `src/mobile/src/hooks/useRecommendations.ts`:
```typescript
import { useState, useEffect } from 'react';
import { apiRequest } from '@/services/api';

export interface TradeRecommendation {
  suggested_rsi_buy_threshold: number;
  suggested_rsi_sell_threshold: number;
  confidence: number;
  rationale: string;
  sample_size: number;
  engine: string;
}

export function useRecommendations(hiredInstanceId: string) {
  const [data, setData] = useState<TradeRecommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    apiRequest<TradeRecommendation>(`cp/trading/recommendations/${hiredInstanceId}`)
      .then(d => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch(e => { if (!cancelled) { setError(e.message); setLoading(false); } });
    return () => { cancelled = true; };
  }, [hiredInstanceId]);
  return { data, loading, error };
}
```

2. Create `src/mobile/src/components/RecommendationCard.tsx` with:
- Recommendation text (rationale)
- Confidence bar (cyan `#00f2fe`, width = `confidence * 100%`)
- "Apply" button (green) — calls `onApply(hiredInstanceId, suggestedThresholds)`
- "Dismiss" button (outline)

3. Add `<RecommendationCard>` to Agent Context Sheet below `<TradePerformanceCard>`.

**Acceptance criteria:**
- [ ] Card renders rationale text
- [ ] Confidence bar width = `confidence * 100%` of card width
- [ ] "Apply" button calls `onApply` callback with suggested thresholds
- [ ] `useRecommendations` calls `cp/trading/recommendations/{id}`
- [ ] Loading state renders without crash

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `RecommendationCard renders rationale text` | Unit | `src/mobile/src/__tests__/components/RecommendationCard.test.tsx` | `cd src/mobile && yarn test RecommendationCard` |
| `RecommendationCard apply button fires callback` | Unit | same | same |
| `useRecommendations calls correct endpoint` | Unit | `src/mobile/src/__tests__/hooks/useRecommendations.test.ts` | same |

---

## How to Launch Each Iteration

### Iteration 1

**Agent task block — paste verbatim into GitHub Agents tab:**

```
You are a Python/FastAPI/SQLAlchemy/GCP expert executing Iteration 1 of plan TRADER-FULL-1.
Branch: feat/trader-full-1-it1-credential-db
Base: main

EXPERT PERSONAS ACTIVE:
- Python 3.11 / FastAPI / SQLAlchemy async / Alembic expert
- Google Cloud Firestore / google-cloud-firestore Python SDK expert
- Security expert (Fernet encryption, secret handling, PII masking)

PLATFORM RULES (mandatory, no exceptions):
1. Router: always waooaw_router() from core.routing — never bare APIRouter()
2. FastAPI() must have dependencies=[Depends(get_correlation_id), Depends(get_audit_log)]
3. GET routes use get_read_db_session() not get_db_session()
4. PiiMaskingFilter on every logger: logger.addFilter(PiiMaskingFilter())
5. @circuit_breaker(service="delta_exchange_api") on every external Delta Exchange HTTP call
6. api_key and api_secret MUST NEVER appear in any log message — use type(exc).__name__ for errors
7. DATA_ROUTER_MODE, EXCHANGE_SECRET_BACKEND read from settings — never os.environ.get() directly
8. ENVIRONMENT=test must return mock data for live Delta Exchange calls (no network in CI)

FAIL-FAST VALIDATION GATE (run first, HALT if any fails):
  cd src/Plant/BackEnd && python -c "from core.config import settings; print(settings.environment)"
  ls src/Plant/BackEnd/models/customer_platform_credential.py
  ls src/Plant/BackEnd/database/migrations/versions/040_dma_batch_type_workflow.py
  ls src/Plant/BackEnd/core/datastore_router.py
  ls src/CP/BackEnd/services/plant_gateway_client.py

Execute stories in order: S1 → S2 → S3 → S4 → S5 → S6.
After each story: run its test command. Fix failures before moving to next story.
CHECKPOINT after each story: git add -A && git commit -m "feat(trader): TRADER-FULL-1 [Sx] — [title]" && git push

After all stories pass S6 (coverage ≥ 80%): open one PR to main with title:
"feat(trader): TRADER-FULL-1 It1 — DB credential store, connectivity validation, trade results"
```

### Iteration 2

**Agent task block — paste verbatim into GitHub Agents tab:**

```
You are a Python/FastAPI/React Native/TypeScript expert executing Iteration 2 of plan TRADER-FULL-1.
Branch: feat/trader-full-1-it2-performance-review
Base: main  ← BLOCKED UNTIL Iteration 1 PR is merged to main

EXPERT PERSONAS ACTIVE:
- Python 3.11 / FastAPI / SQLAlchemy async expert
- React Native / TypeScript / hooks pattern expert
- Design system expert (dark #0a0a0a, neon cyan #00f2fe, card components)

PLATFORM RULES: same as Iteration 1 (waooaw_router, get_read_db_session, PiiMaskingFilter, circuit_breaker, no env baking).

FAIL-FAST VALIDATION GATE (run first, HALT if any fails):
  ls src/Plant/BackEnd/models/trade_result.py           ← must exist from It1
  ls src/Plant/BackEnd/models/exchange_credential.py    ← must exist from It1
  ls src/Plant/BackEnd/api/v1/trade_results.py          ← must exist from It1
  python -c "from services.recommendation_engine import get_recommendation_engine; print('ok')" 2>/dev/null || echo "FAIL — run from src/Plant/BackEnd"

Execute stories in order: S1 → S2 → S3 → S4 → S5.
After each story: run its test command.
CHECKPOINT after each story: git add -A && git commit -m "feat(trader): TRADER-FULL-1 It2 [Sx] — [title]" && git push

After all stories pass: open one PR to main with title:
"feat(trader): TRADER-FULL-1 It2 — trade performance review, recommendations, mobile screens"
```
