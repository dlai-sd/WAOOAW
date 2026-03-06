# WAOOAW — Agent Construct Low-Level Design & Specification

## Document Metadata

| Field | Value |
|---|---|
| Document ID | `AGENT-CONSTRUCT-DESIGN` |
| Area | Platform Architecture — Plant BackEnd |
| Created | 2026-03-06 |
| Status | Living document — updated as constructs evolve |
| Parent | `docs/CONTEXT_AND_INDEX.md` §3 (Architecture), §4.3 (Plant BackEnd) |
| Codebase root | `src/Plant/BackEnd/` |

---

## 1. Platform Model (Read First)

Every AI agent on WAOOAW is **hired** by a customer. After hiring, the agent works
**anonymously** — the customer sees deliverables and outcomes, not internal mechanics.

The hierarchy that governs this:

```
Customer
  └── HiredAgent          (one instance of an agent type, hired by one customer)
        └── Skill          (a capability declared on the agent type)
              └── GoalRun  (one execution of a skill, triggered by Scheduler)
                    └── Deliverable  (the output — one per GoalRun)
```

**Constructs** are the internal building blocks that make a GoalRun happen.
A customer never interacts with constructs directly — they interact only with
the Skill API surface (configure → run → approve → receive deliverable).

---

## 2. Construct Hierarchy

```
AgentSpec (blueprint)
  └── Dimensions (Skill, Industry, Team, Integrations, Budget, Trial, UI, L10n)
        └── Skill
              └── GoalSchema        ← what success looks like (Outcome definition)
              └── GoalConfig        ← per-instance runtime parameters (customer-set)
              │
              ├── CONSTRUCT: Scheduler    ← when to run
              ├── CONSTRUCT: Pump         ← what data flows in
              ├── CONSTRUCT: Processor    ← what happens to data (the AI brain)
              ├── CONSTRUCT: Connector    ← credentials + protocol for external systems
              └── CONSTRUCT: Publisher    ← where results go out
```

**Invariant:** Constructs are stateless. State lives in the database
(`goal_instances`, `scheduled_goal_runs`, `campaigns`, `content_posts`,
`deliverables`). A construct reads from DB on entry, writes on exit.

---

## 3. Construct Specifications

---

### 3.1 Agent (The Blueprint)

**Purpose:** A declarative spec that defines what an agent *is*, what dimensions
it has, and what constraints govern its execution. It is not the agent itself — it
is the mould from which a hired instance is cast.

**Design principle:** Agents have personality and specialisation but no runtime
logic. All logic lives in Constructs. An agent is always uniquely identified by
`hired_instance_id` (the customer's copy), not by `agent_type_id` (the catalogue
entry).

#### Data Model

```
agent_type_entity               ← the catalogue entry (reference data)
  agent_type_id   UUID PK
  name            VARCHAR(255)
  description     TEXT
  industry        VARCHAR(100)   ← marketing | education | sales
  specialisation  VARCHAR(255)
  avatar_config   JSONB          ← gradient, initials, personality metadata

hired_agents                    ← the customer's live instance
  hired_instance_id  UUID PK
  customer_id        FK → customer_entity
  agent_type_id      FK → agent_type_entity
  trial_end_date     TIMESTAMPTZ
  status             VARCHAR(50)  ← trial | active | paused | cancelled
  hired_at           TIMESTAMPTZ
```

#### Key Code

| File | Purpose |
|---|---|
| `agent_mold/spec.py` | `AgentSpec` + `DimensionSpec` Pydantic models |
| `agent_mold/registry.py` | In-memory registry of all agent types registered at startup |
| `agent_mold/enforcement.py` | Validates agentSpec at hire time — rejects unknown dimensions |
| `agent_mold/contracts.py` | `DimensionContract` ABC — each dimension implements `validate()` + `compile()` |
| `agent_mold/reference_agents.py` | Catalogue of reference agent definitions |
| `api/v1/agents.py` | CRUD for `agent_type_entity` |
| `api/v1/hired_agents_simple.py` | Hire / list / cancel for `hired_agents` |

#### Interface Contract

```python
class AgentSpec(BaseModel):
    agent_id:   str               # e.g. "AGT-MARKETING-001"
    agent_type: str               # e.g. "marketing"
    version:    str = "1.0"
    dimensions: Dict[DimensionName, DimensionSpec]

class DimensionSpec(BaseModel):
    name:    DimensionName        # skill | industry | team | integrations | ...
    present: bool = True          # False = dimension explicitly absent
    version: str  = "1.0"
    config:  Dict[str, Any] = {}

# DimensionName enum values:
# SKILL, INDUSTRY, TEAM, INTEGRATIONS, UI, LOCALIZATION, TRIAL, BUDGET
```

#### Platform Rules for Agent
- A hired agent MUST have a `SKILL` dimension with `present=True` to be runnable.
- `agent_type_id` is immutable after hire — you cannot change what kind of agent was hired.
- Trial enforced by `trial_end_date` — GoalSchedulerService checks this before firing.
- Booster packs will increment a `quota_remaining` counter on the hired_agent record (to be added in the Booster plan).

---

### 3.2 Scheduler

**Purpose:** Decides *when* a Skill's GoalRun is triggered. Fires goal instances
on a cadence (daily, weekly, cron) or on-demand. Completely decoupled from
*what* runs — it only creates a `scheduled_goal_run` row and enqueues execution.

**Design principle:** One shared durable scheduler serves all agents. Per-agent
schedules are stored as data (rows in `scheduled_goal_runs`), not as separate
processes. This is critical for Cloud Run cost control at scale.

#### Data Model

```
scheduled_goal_runs
  id                 SERIAL PK
  hired_instance_id  FK → hired_agents
  skill_id           FK → skill_entity
  cron_expression    VARCHAR(100)        ← "0 9 * * *" = daily at 9am UTC
  next_run_at        TIMESTAMPTZ
  last_run_at        TIMESTAMPTZ
  is_active          BOOLEAN DEFAULT true
  created_at         TIMESTAMPTZ

scheduler_state
  id           INTEGER PK = 1            ← singleton row
  is_paused    BOOLEAN DEFAULT false
  paused_at    TIMESTAMPTZ
  paused_by    VARCHAR(255)
  pause_reason TEXT

scheduler_dlq                            ← Dead Letter Queue for failed runs
  id                  SERIAL PK
  goal_instance_id    VARCHAR(255)
  hired_instance_id   FK → hired_agents
  error_message       TEXT
  error_type          VARCHAR(50)        ← transient | permanent
  attempts            INTEGER
  failed_at           TIMESTAMPTZ
  resolved_at         TIMESTAMPTZ
```

#### Error Handling

| Error type | Behaviour |
|---|---|
| `TransientError` (network, timeout, LLM rate limit) | Exponential backoff: 3 retries at 1s / 2s / 4s + jitter |
| `PermanentError` (bad config, auth failure) | Fast-fail to DLQ immediately, no retry |
| Trial expired | Skip silently, log audit event |
| `scheduler_state.is_paused = true` | All firing halted until resumed by operator |

#### Key Code

| File | Purpose |
|---|---|
| `services/goal_scheduler_service.py` | `GoalSchedulerService` — core firing logic, retry, DLQ routing |
| `services/scheduler_admin_service.py` | Pause / resume / force-trigger operations |
| `services/scheduler_persistence_service.py` | Persists schedule rows, `next_run_at` updates |
| `services/scheduler_dlq_service.py` | DLQ read / resolve / replay |
| `services/scheduler_health_service.py` | Health check: lag, queue depth, paused state |
| `api/v1/scheduler_admin.py` | Operator API: `POST /scheduler/pause`, `/resume`, `/trigger` |
| `api/v1/scheduler_health.py` | `GET /scheduler/health` |

#### Interface Contract

```python
class GoalRunResult:
    goal_instance_id: str
    status:           GoalRunStatus       # pending | running | completed | failed | retrying
    deliverable_id:   Optional[str]
    error_message:    Optional[str]
    error_type:       Optional[ErrorType] # transient | permanent
    attempts:         int
    total_duration_ms: Optional[int]

class GoalRunStatus(Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    RETRYING  = "retrying"
```

#### Future: Booster Pack Hook
When a Booster plan is executed, the Scheduler must gate on `quota_remaining > 0`
before firing. The quota decrement happens atomically with the `GoalRunResult`
write inside a single DB transaction.

---

### 3.3 Pump

**Purpose:** Pulls the data that a Processor needs before it can execute. Today
the Pump is embedded inside goal execution — it reads `goal_config` JSONB and
customer context. It will be extracted as a named construct when Booster packs
are built (quota-aware ingestion).

**Design principle:** The Pump is read-only and idempotent. It never modifies
source data. All it does is assemble the `ProcessorInput` bag from multiple
sources: DB state, customer config, external data references.

#### Current Sources (implicit Pump)

| Source | What it provides | Read endpoint |
|---|---|---|
| `agent_skills.goal_config` JSONB | Customer-configured runtime params (brief, schedule, tone) | `PATCH /cp/hired-agents/{id}/skills/{skill_id}/goal-config` |
| `customer_entity` | Customer profile (brand_name, industry, locale) | `GET /v1/customers/{id}` |
| `hired_agents` | Hired instance status, trial_end_date, agent_type_id | `GET /v1/hired-agents/{id}` |
| `performance_stats` | Historical metrics (used to personalise content themes) | `GET /v1/performance-stats` |
| `usage_events` | Past execution events (deduplication, continuity) | `GET /v1/usage-events` |

#### Data Model (assembled ProcessorInput)

```python
# Not yet a named class — embedded in each Skill executor.
# Will become: class ProcessorInput(BaseModel) in the Pump refactor.

{
  "goal_config":     { ... }          # CampaignBrief or SkillGoalConfig
  "customer_id":     "CUST-uuid",
  "brand_name":      "WAOOAW",
  "industry":        "marketing",
  "hired_instance_id": "uuid",
  "correlation_id":  "uuid"           # X-Correlation-ID thread
}
```

#### Extraction Roadmap (Booster Pack phase)
- Name the class: `class Pump(ABC)` with method `async def pull(context) -> ProcessorInput`
- Add `quota_remaining: int` field to `ProcessorInput`
- Implement `GoalConfigPump(Pump)` — wraps current embedded logic
- Scheduler checks `quota_remaining` before firing; Pump decrements after pull

---

### 3.4 Processor

**Purpose:** The AI brain. Takes a `ProcessorInput`, thinks, and produces a
structured output. Today there are two Processor implementations for campaign
content: `deterministic` (no LLM, template-based) and `grok` (Grok-3 API via
`EXECUTOR_BACKEND` env var). The Processor is the only construct that may make
LLM API calls.

**Design principle:** The Processor is pluggable via `EXECUTOR_BACKEND` env var.
Swapping engines (Grok → GPT-4o → Gemini) requires zero code change. All
cost estimation is computed by a pure function before any LLM call is made.

#### Processor Implementations

| Backend | Env | Cost | LLM calls | When to use |
|---|---|---|---|---|
| `deterministic` | `EXECUTOR_BACKEND=deterministic` | ₹0 | 0 | Development, demo, free tier |
| `grok` | `EXECUTOR_BACKEND=grok` + `XAI_API_KEY` | Grok free tier = ₹0 | 1 (theme list) + N (posts) | Production |
| *(future)* `openai` | `EXECUTOR_BACKEND=openai` + `OPENAI_API_KEY` | Pay-per-call | same | Premium tier |

#### Key Code

| File | Purpose |
|---|---|
| `agent_mold/skills/content_creator.py` | `ContentCreatorSkill` — main Processor for campaigns; two backends |
| `agent_mold/skills/grok_client.py` | `GrokClient` — async HTTP wrapper for xAI API with circuit breaker |
| `agent_mold/skills/executor.py` | `execute_marketing_multichannel_v1()` — channel adapter pipeline |
| `agent_mold/skills/playbook.py` | `SkillPlaybook`, `CanonicalMessage`, `SkillExecutionResult` |
| `agent_mold/skills/trading_executor.py` | Trading skill Processor (separate domain) |

#### Interface Contract

```python
# Input (assembled by Pump, passed into Processor)
class CampaignBrief(BaseModel):
    theme:              str
    start_date:         date
    duration_days:      int               # ge=1, le=365
    destinations:       List[DestinationRef]
    schedule:           PostingSchedule
    brand_name:         str
    audience:           str
    tone:               str               # "professional" | "inspiring" | "casual"
    language:           str               # ISO 639-1
    approval_mode:      ApprovalMode      # per_item | batch | auto
    additional_context: str

# Output (produced by Processor, passed to Publisher)
class ContentCreatorOutput(BaseModel):
    campaign:         Campaign
    daily_theme_list: List[DailyThemeItem]
    posts:            List[ContentPost]

class DailyThemeItem(BaseModel):
    theme_item_id:    str      # uuid
    campaign_id:      str
    day_number:       int
    scheduled_date:   date
    theme_title:      str
    theme_description: str
    review_status:    ReviewStatus    # pending_review | approved | rejected
    approved_at:      Optional[datetime]

class ContentPost(BaseModel):
    post_id:          str      # uuid
    campaign_id:      str
    theme_item_id:    str
    channel:          ChannelName
    content:          str
    destination:      DestinationRef
    review_status:    ReviewStatus
    publish_status:   PublishStatus   # not_published | published | failed
    publish_receipt:  Optional[PublishReceipt]
    scheduled_at:     datetime
```

#### Cost Estimation (pure function, no I/O)

```python
def estimate_cost(brief: CampaignBrief, model_used: str) -> CostEstimate:
    total_theme_items = brief.duration_days
    posts_per_day     = brief.schedule.times_per_day * len(brief.destinations)
    total_posts       = total_theme_items * posts_per_day
    llm_calls         = 1 + total_posts          # 1 for theme list + 1 per post
    cost_per_call_usd = 0.0                      # Grok free tier
    # Returns CostEstimate with total_cost_inr = 0.0 on free tier
```

---

### 3.5 Connector

**Purpose:** Manages the *relationship* between an agent and an external system.
Holds a `credential_ref` (a pointer to GCP Secret Manager, never the raw secret).
Verifies connection status. Completely stateless — it never stores secrets in the DB.

**Design principle:** `secret_ref` is accepted on `POST` but **never returned in any
GET response**. This is a hard security boundary — auditors, ops, and even the
customer's own API calls cannot retrieve stored credentials. Only the Processor
at runtime can resolve `secret_ref` via `CredentialResolver`.

#### Data Model

```
platform_connections
  id                 UUID PK
  hired_instance_id  FK → hired_agents
  skill_id           FK → skill_entity
  platform_key       VARCHAR(100)    ← "delta_exchange" | "linkedin" | "instagram"
  secret_ref         VARCHAR(500)    ← GCP Secret Manager path ONLY. NEVER returned in API.
  status             VARCHAR(50)     ← pending | connected | error
  connected_at       TIMESTAMPTZ
  last_verified_at   TIMESTAMPTZ
  created_at, updated_at  TIMESTAMPTZ
```

#### Key Code

| File | Purpose |
|---|---|
| `api/v1/platform_connections.py` | CRUD for connections. `secret_ref` write-only. |
| `services/credential_resolver.py` | Resolves `secret_ref` → actual secret at runtime via GCP Secret Manager |
| `services/social_credential_resolver.py` | OAuth-specific credential resolution for social platforms |
| `agent_mold/skills/adapters.py` | Channel adapters (LinkedIn, Instagram, YouTube, Facebook, WhatsApp) |
| `core/encryption.py` | Encrypts credential payloads at rest (AES-256) before they reach the DB |

#### Interface Contract

```python
# POST /v1/hired-agents/{hired_instance_id}/platform-connections
class CreateConnectionRequest(BaseModel):
    skill_id:     str
    platform_key: str
    secret_ref:   str   # GCP Secret Manager path: "projects/.../secrets/.../versions/latest"

# GET response — secret_ref intentionally absent
class ConnectionResponse(BaseModel):
    id:                 str
    hired_instance_id:  str
    skill_id:           str
    platform_key:       str
    status:             str      # pending | connected | error
    connected_at:       Optional[datetime]
    last_verified_at:   Optional[datetime]
    created_at:         datetime
    updated_at:         datetime
```

#### Credential Lifecycle (Booster Pack / Connector Marketplace — Phase 2)
When partner-supplied connectors are introduced, the Connector construct
will gain a `credential_lifecycle` field: `{expires_at, refresh_token_ref,
auto_renew: bool}`. The Connector will emit a `CredentialExpiringSoon` event
48h before expiry so the Scheduler can pause execution cleanly.

---

### 3.6 Publisher

**Purpose:** Pushes a finished `ContentPost` to an external destination via
a registered `DestinationAdapter`. Returns a `PublishReceipt`. Idempotent
by design — calling twice with the same `post_id` must not create duplicate posts.

**Design principle:** The Publisher knows nothing about content — it only takes
a `PublishInput` and a `DestinationAdapter` and fires. Adding a new destination
(LinkedIn, Twitter/X, email newsletter) requires only a new adapter file and a
`registry.register(...)` call at startup. Zero changes to the Publisher engine.

#### Key Code

| File | Purpose |
|---|---|
| `agent_mold/skills/publisher_engine.py` | `DestinationAdapter` ABC + `DestinationRegistry` |
| `agent_mold/skills/adapters_publish.py` | `SimulatedPublishAdapter` (live today: logs + stores receipt, no real API call) |

#### Interface Contract

```python
class DestinationAdapter(ABC):
    DESTINATION_TYPE: str      # e.g. "simulated", "linkedin", "instagram"

    @abstractmethod
    def publish(self, inp: PublishInput) -> PublishReceipt:
        """Idempotent. Same post_id must not publish twice."""

    def estimate_cost(self, inp: PublishInput) -> float:
        """Cost in USD. Default: 0.0 (free tier / simulated)."""
        return 0.0

class PublishInput(BaseModel):
    post_id:        str
    channel:        ChannelName
    content:        str
    destination:    DestinationRef   # contains credential_ref for Connector lookup
    scheduled_at:   datetime

class PublishReceipt(BaseModel):
    post_id:        str
    destination_type: str
    platform_post_id: Optional[str]   # real post ID on LinkedIn, etc.
    published_at:   datetime
    cost_usd:       float
    status:         str               # success | failed
    metadata:       Dict[str, Any]    # platform-specific response
```

#### Adapter Registry (startup wiring)

```python
# Registered in app startup (main.py or lifespan)
from agent_mold.skills.publisher_engine import registry
from agent_mold.skills.adapters_publish import SimulatedPublishAdapter

registry.register("simulated", SimulatedPublishAdapter)
# registry.register("linkedin", LinkedInAdapter)    ← Phase 2
# registry.register("instagram", InstagramAdapter)  ← Phase 2
```

#### PublishReceipt Storage
`publish_receipt` is stored as JSONB in `content_posts.publish_receipt`.
This is the platform's machine-readable proof of delivery — the foundation
for the future Outcome-gated billing and trial value proof.

---

## 4. Construct Execution Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ SCHEDULER                                                           │
│  GoalSchedulerService fires at next_run_at                          │
│  Checks: trial valid? scheduler not paused? quota > 0?             │
│  Creates: goal_instances row (status=running)                       │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PUMP (embedded in GoalSchedulerService today)                       │
│  Reads: agent_skills.goal_config JSONB                              │
│  Reads: customer_entity (brand, industry)                           │
│  Reads: hired_agents (status, trial_end_date)                       │
│  Assembles: ProcessorInput bag                                      │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PROCESSOR (ContentCreatorSkill or other Skill executor)             │
│  Calls: GrokClient or deterministic template engine                 │
│  Produces: DailyThemeList + ContentPosts                            │
│  Persists: campaigns, daily_theme_items, content_posts tables       │
│  (CAMPAIGN_PERSISTENCE_MODE=db required for PostgreSQL persistence) │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼ (after customer approval via /cp/campaigns API)
┌─────────────────────────────────────────────────────────────────────┐
│ CONNECTOR (PlatformConnection lookup)                               │
│  Reads: platform_connections.secret_ref for destination             │
│  Calls: CredentialResolver → GCP Secret Manager                    │
│  Provides: live credential to Publisher                             │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PUBLISHER (PublisherEngine + DestinationAdapter)                    │
│  Calls: DestinationAdapter.publish(PublishInput)                    │
│  Returns: PublishReceipt                                            │
│  Persists: content_posts.publish_status + publish_receipt JSONB     │
│  Updates: goal_instances status=completed                           │
│  Creates: deliverables row                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. NFR Requirements Per Construct

Every construct invocation point (service method or API route) **must** satisfy
the platform-wide NFR standards from `docs/CP/iterations/NFRReusable.md`:

| NFR | Where applied |
|---|---|
| `waooaw_router()` factory | All API routes in `api/v1/scheduler_admin.py`, `platform_connections.py`, `campaigns.py` |
| `get_read_db_session` on GETs | Pump reads, Scheduler health, Publisher receipt reads |
| `PIIMaskingFilter` on every logger | All construct service files — email, phone, name never logged raw |
| `@circuit_breaker(service=...)` | `GrokClient` (Processor), `CredentialResolver` (Connector), `DestinationAdapter.publish()` (Publisher) |
| `X-Correlation-ID` propagation | Passed from Scheduler through every construct to PublishReceipt |
| OTel span per construct | `tracer.start_as_current_span("scheduler.fire")`, `"processor.execute"`, `"publisher.publish"` |
| Audit log on state mutation | GoalRun create/complete/fail, ContentPost approve/reject, PublishReceipt write |

---

## 6. Environment Flags Governing Constructs

| Flag | Default | Effect |
|---|---|---|
| `EXECUTOR_BACKEND` | `deterministic` | `grok` → activates Grok-3 Processor |
| `CAMPAIGN_PERSISTENCE_MODE` | `memory` | `db` → Processor writes to PostgreSQL |
| `XAI_API_KEY` | unset | Required when `EXECUTOR_BACKEND=grok` |
| `CIRCUIT_BREAKER_ENABLED` | `true` | Set `false` in test only |
| `SCHEDULER_ENABLED` | `true` | Set `false` to disable all Scheduler firing |

---

## 7. Gap Register (Pending Design Work)

| Gap | Impact | Planned in |
|---|---|---|
| `Pump` is not a named class | Cannot add quota-awareness without touching Processor | Booster Pack plan |
| `CredentialExpiringSoon` event missing | OAuth tokens expire silently, Publisher fails | Connector Marketplace plan (Phase 2) |
| No `Outcome` measurement on `PublishReceipt` | Cannot auto-trigger trial-to-paid conversion | Outcome Scoring plan |
| A2A pipe — one agent's Publisher feeds another's Pump | Platform locked to single-agent workflows | Platform Iteration 2 |
| `approval_mode=auto` not yet enforced by Scheduler | Posts sit in `pending_review` forever unless customer takes action | Next sprint |

---

## 8. Key DB Tables Quick Reference

| Table | Owned by | Purpose |
|---|---|---|
| `agent_type_entity` | Agent | Reference catalogue of all agent types |
| `hired_agents` | Agent | One row per customer-agent hire |
| `agent_skills` | Agent / Pump | Skills attached to a hire + `goal_config` JSONB |
| `platform_connections` | Connector | Credential references per hire |
| `scheduled_goal_runs` | Scheduler | Cadence definitions |
| `scheduler_state` | Scheduler | Singleton pause/resume state |
| `scheduler_dlq` | Scheduler | Failed executions pending review |
| `goal_instances` | Scheduler | One row per fired execution |
| `campaigns` | Processor | Campaign created by ContentCreatorSkill |
| `daily_theme_items` | Processor | One row per campaign day |
| `content_posts` | Processor / Publisher | One row per post; `publish_receipt` JSONB |
| `deliverables` | Publisher | Final deliverable row linked to goal_instance |
