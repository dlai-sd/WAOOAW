# WAOOAW — Agent Construct Low-Level Design & Specification

## Document Metadata

| Field | Value |
|---|---|
| Document ID | `AGENT-CONSTRUCT-DESIGN` |
| Version | **v2** (supersedes v1 dated 2026-03-06) |
| Area | Platform Architecture — Plant BackEnd |
| Created | 2026-03-06 |
| Last revised | 2026-03-07 |
| Status | Living document — updated as constructs evolve |
| Parent | `docs/CONTEXT_AND_INDEX.md` §3 (Architecture), §4.3 (Plant BackEnd) |
| Codebase root | `src/Plant/BackEnd/` |

### What changed in v2

| # | Change | Rationale |
|---|---|---|
| 1 | `ConstructBindings` added to `AgentSpec` | Per-agent Processor selection; removes global `EXECUTOR_BACKEND` assumption |
| 2 | `LifecycleHooks` ABC — all platform lifecycle events defined | Mould declares every hook; agents override only what they need |
| 3 | `BaseProcessor` ABC extracted from skills | Unifies ContentCreatorProcessor + TradingProcessor under a common mould contract |
| 4 | `BasePump` ABC + `GoalConfigPump` (platform default) | Pump is no longer an implicit concept — named, testable, quota-aware |
| 5 | `ProcessorInput` / `ProcessorOutput` base types | Type-safe pipeline across all agents |
| 6 | Hook stages mapped to construct execution points | Intercept at each of: Pump pull, Processor execute, Publisher publish |
| 7 | `ConstraintPolicy` on AgentSpec | Trading risk limits and content rate limits enforced in the mould, not downstream |
| 8 | §7 Agent Profile Validation — Share Trader vs Content Creator | Every design decision validated against two real agents |

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

**The mould is in-memory.** `AgentSpec` objects are created at process startup from
`agent_mold/reference_agents.py` and held in a `DimensionRegistry` + `SkillRegistry`
in RAM. There is no DB persistence of the mould itself — only the *hired instance*
(`hired_agents` row) and its runtime artefacts are persisted. This is intentional
for the current iteration; mould DB persistence is a future concern.

---

## 2. Construct Hierarchy

```
AgentSpec (blueprint / mould — in-memory)
  ├── Dimensions          (Skill, Industry, Team, Integrations, Budget, Trial, UI, L10n)
  ├── ConstructBindings   (which Pump / Processor / Publisher / Connector to use)
  ├── ConstraintPolicy    (risk limits, rate limits, cost gates)
  └── LifecycleHooks      (on_hire, on_trial_end, on_cancel … — all defined, agents override)
        │
        └── Skill
              └── GoalSchema        ← what success looks like (Outcome definition)
              └── GoalConfig        ← per-instance runtime parameters (customer-set)
              │
              ├── CONSTRUCT: Scheduler    ← PLATFORM CORE — when to run
              ├── CONSTRUCT: Pump         ← PLATFORM CORE — what data flows in
              ├── CONSTRUCT: Processor    ← AGENT-SPECIFIC — what happens to data (the AI brain)
              ├── CONSTRUCT: Connector    ← PLATFORM CORE — credentials + protocol
              └── CONSTRUCT: Publisher    ← PLATFORM CORE — where results go out
```

### Critical platform rule: Platform Core vs Agent-Specific

| Construct | Owner | Rationale |
|---|---|---|
| Scheduler | **Platform Core** | Cadence, retry, DLQ are identical across all agents |
| Pump | **Platform Core** | Data assembly from DB + config is identical; only the *schema* of output differs |
| Connector | **Platform Core** | Credential lifecycle, Secret Manager resolution — never agent-specific |
| Publisher | **Platform Core** | Destination adapter registry is common; adapters are plugged in, not per-agent |
| **Processor** | **Agent-Specific** | The AI reasoning, LLM calls, domain logic — only this varies per agent type |

**Invariant:** Constructs are stateless. State lives in the database.
A construct reads from DB on entry, writes on exit.

---

## 3. Mould Anatomy (AgentSpec and its contracts)

The mould is the *blueprint* for an agent type. It is not the agent itself — it is
the mould from which a hired instance is cast. One mould can produce millions of
hired instances.

---

### 3.1 AgentSpec — the blueprint

**Purpose:** Declarative spec defining what an agent *is*, what dimensions it has,
which constructs to use, what constraints govern it, and what lifecycle hooks it
registers.

**Design principle:** The mould is purely declarative. It contains no runtime I/O.
All execution logic lives in Constructs and the services that run them.

#### Data Model (in-memory, not DB)

```
agent_type_entity               ← the DB catalogue entry (reference data)
  agent_type_id   UUID PK
  name            VARCHAR(255)
  description     TEXT
  industry        VARCHAR(100)   ← marketing | education | sales | trading
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

#### Interface Contract (v2 — with ConstructBindings + ConstraintPolicy)

```python
class AgentSpec(BaseModel):
    agent_id:          str               # e.g. "AGT-TRADING-001"
    agent_type:        str               # e.g. "trading"
    version:           str = "1.0"
    dimensions:        Dict[DimensionName, DimensionSpec]
    construct_bindings: ConstructBindings = Field(default_factory=ConstructBindings)
    constraint_policy:  ConstraintPolicy  = Field(default_factory=ConstraintPolicy)

# DimensionName enum values:
# SKILL, INDUSTRY, TEAM, INTEGRATIONS, UI, LOCALIZATION, TRIAL, BUDGET
```

#### Key Code

| File | Purpose |
|---|---|
| `agent_mold/spec.py` | `AgentSpec`, `CompiledAgentSpec`, `DimensionSpec`, `DimensionName` |
| `agent_mold/registry.py` | `DimensionRegistry`, `SkillRegistry` — startup wiring |
| `agent_mold/enforcement.py` | `default_hook_bus()` singleton — builds the platform HookBus |
| `agent_mold/contracts.py` | `DimensionContract` ABC — validate/materialize/register_hooks/observe |
| `agent_mold/reference_agents.py` | Marketing, tutor, trading reference agent definitions |
| `api/v1/agents.py` | CRUD for `agent_type_entity` |
| `api/v1/hired_agents_simple.py` | Hire / list / cancel for `hired_agents` |

#### Platform Rules for AgentSpec
- A hired agent MUST have a `SKILL` dimension with `present=True` to be runnable.
- `agent_type_id` is immutable after hire.
- Trial enforcement: `trial_end_date` is checked by Scheduler before every firing.
- `construct_bindings.processor_class` is **required** — no agent runs without declaring its Processor.

---

### 3.2 ConstructBindings — wiring the pipeline

**Purpose:** Each `AgentSpec` declares which Processor class to use. Platform Core
classes (Scheduler, Pump, Connector, Publisher) have platform defaults that all
agents inherit. An agent may override only if it has a domain-specific reason.

```python
class ConstructBindings(BaseModel):
    """Wires an AgentSpec to its construct implementation classes.

    Platform defaults are used for all constructs except Processor,
    which MUST be declared by every agent type.
    """
    # Platform Core — agents inherit these; override only for specialist behaviour
    scheduler_class: str = "platform.schedulers.GoalScheduler"
    pump_class:      str = "platform.pumps.GoalConfigPump"
    connector_class: str = "platform.connectors.SecretManagerConnector"
    publisher_class: str = "platform.publishers.DestinationPublisher"

    # Agent-Specific — REQUIRED. Must name a registered BaseProcessor subclass.
    processor_class: str  # e.g. "agent_mold.skills.content_creator.ContentCreatorProcessor"
                          # e.g. "agent_mold.skills.trading_executor.TradingProcessor"
```

**Why this matters for Share Trader vs Content Creator:**

| | Share Trader | Content Creator |
|---|---|---|
| `scheduler_class` | platform default | platform default |
| `pump_class` | platform default | platform default |
| `processor_class` | `TradingProcessor` | `ContentCreatorProcessor` |
| `connector_class` | platform default | platform default |
| `publisher_class` | platform default (simulated) | platform default (DestinationPublisher) |

This eliminates the global `EXECUTOR_BACKEND` env var antipattern. Both agents
can run simultaneously — the mould tells the Scheduler which Processor to instantiate.

---

### 3.3 LifecycleHooks — all platform events defined in the mould

**Purpose:** The mould declares every lifecycle event the platform will ever fire.
Specific agent implementations override only the hooks they care about.
Default implementation for all hooks is a **no-op** — safe to ignore.

**Design principle:** Any new platform lifecycle event is first added here as an
abstract method with a default no-op. This makes the mould the single source of
truth for what events exist. An agent that hasn't implemented a hook will never
crash — it simply inherits the no-op.

```python
@dataclass(frozen=True)
class LifecycleContext:
    """Passed to every lifecycle hook."""
    hired_instance_id: str
    customer_id:       str
    agent_id:          str          # from AgentSpec
    correlation_id:    str
    timestamp:         datetime
    payload:           Dict[str, Any] = field(default_factory=dict)


class AgentLifecycleHooks(ABC):
    """All lifecycle hooks an agent MAY respond to.

    Platform fires these at well-defined moments.
    Default = no-op on every hook.
    Agents subclass this and override only what they need.
    """

    # ── Hire & Trial lifecycle ─────────────────────────────────────────────
    async def on_hire(self, ctx: LifecycleContext) -> None:
        """Fired once when a customer hires this agent. Setup / welcome."""

    async def on_trial_start(self, ctx: LifecycleContext) -> None:
        """Fired when 7-day trial begins (immediately after on_hire)."""

    async def on_trial_day_N(self, ctx: LifecycleContext, day: int) -> None:
        """Fired each day of the trial. [day] = 1..7.
        Use for value-delivery nudges or daily summaries."""

    async def on_trial_end(self, ctx: LifecycleContext) -> None:
        """Fired when trial period expires.
        Agents use this to send final trial summary / conversion prompt."""

    async def on_trial_convert(self, ctx: LifecycleContext) -> None:
        """Fired when customer converts from trial to paid."""

    # ── Active lifecycle ───────────────────────────────────────────────────
    async def on_pause(self, ctx: LifecycleContext) -> None:
        """Fired when customer pauses the agent."""

    async def on_resume(self, ctx: LifecycleContext) -> None:
        """Fired when customer resumes after a pause."""

    async def on_cancel(self, ctx: LifecycleContext) -> None:
        """Fired when customer cancels. Cleanup, farewell, retention offer."""

    # ── GoalRun lifecycle ──────────────────────────────────────────────────
    async def on_goal_run_start(self, ctx: LifecycleContext) -> None:
        """Fired immediately before Pump pulls data for a GoalRun."""

    async def on_goal_run_complete(self, ctx: LifecycleContext) -> None:
        """Fired after Publisher writes the Deliverable."""

    async def on_goal_run_fail(self, ctx: LifecycleContext) -> None:
        """Fired when a GoalRun fails after all retries are exhausted."""

    async def on_goal_run_dlq(self, ctx: LifecycleContext) -> None:
        """Fired when a GoalRun lands in the Dead Letter Queue."""

    # ── Deliverable lifecycle ──────────────────────────────────────────────
    async def on_deliverable_pending_review(self, ctx: LifecycleContext) -> None:
        """Fired when approval_mode=per_item and item awaits customer review."""

    async def on_deliverable_approved(self, ctx: LifecycleContext) -> None:
        """Fired when customer approves a deliverable.
        Share Trader: triggers actual order placement.
        Content Creator: triggers Publisher to post to social channels."""

    async def on_deliverable_rejected(self, ctx: LifecycleContext) -> None:
        """Fired when customer rejects a deliverable."""

    async def on_deliverable_expired(self, ctx: LifecycleContext) -> None:
        """Fired when an approval window expires without decision."""

    # ── Quota / Budget lifecycle ───────────────────────────────────────────
    async def on_quota_low(self, ctx: LifecycleContext) -> None:
        """Fired when quota_remaining falls below threshold (Booster pack phase)."""

    async def on_quota_exhausted(self, ctx: LifecycleContext) -> None:
        """Fired when quota_remaining = 0. Scheduler will pause until refilled."""

    async def on_budget_threshold(self, ctx: LifecycleContext) -> None:
        """Fired when cumulative cost approaches constraint_policy.max_cost_per_month_usd."""
```

**Agent implementation examples:**

| Hook | Share Trader behaviour | Content Creator behaviour |
|---|---|---|
| `on_hire` | Validate Delta Exchange credentials ping | Send welcome campaign setup guide |
| `on_trial_start` | Schedule first demo trade run | Schedule first content theme generation |
| `on_trial_day_N` | Send daily P&L summary | Send "Day N posts published" notification |
| `on_trial_end` | Summarise total simulated returns | Publish trial portfolio of posts |
| `on_deliverable_approved` | **Place actual order on Delta Exchange** | **Trigger Publisher to post to socials** |
| `on_deliverable_rejected` | Log rejected order intent | Queue post for revision |
| `on_cancel` | Close all open positions (if any) | Archive campaign artefacts |
| `on_quota_exhausted` | Pause all scheduled trades | Pause scheduled posts |

---

### 3.4 ProcessorInput and ProcessorOutput — the pipeline contract

**Purpose:** Typed base models that flow through the construct pipeline.
`BasePump.pull()` produces a `ProcessorInput`. `BaseProcessor.execute()` consumes it
and produces a `ProcessorOutput`. `PlatformPublisher.publish()` consumes that.

```python
class ProcessorInput(BaseModel):
    """Assembled by Pump; consumed by Processor.

    Every field here is available to every Processor regardless of agent type.
    Agents extend this with a typed subclass for their domain inputs.
    """
    goal_instance_id:  str
    hired_instance_id: str
    customer_id:       str
    agent_id:          str               # from AgentSpec
    correlation_id:    str
    goal_config:       Dict[str, Any]    # customer-set runtime params (CampaignBrief etc.)
    customer_context:  Dict[str, Any]    # brand_name, industry, locale
    quota_remaining:   Optional[int] = None   # Booster pack phase
    fired_at:          datetime


class ProcessorOutput(BaseModel):
    """Produced by Processor; consumed by Publisher.

    Agents extend this with a typed subclass for their domain outputs.
    """
    goal_instance_id:  str
    hired_instance_id: str
    agent_id:          str
    correlation_id:    str
    deliverable_type:  str               # "content_campaign" | "trade_order" | …
    payload:           Dict[str, Any]    # agent-specific output (campaign, trade intent…)
    cost_estimate:     Optional[CostEstimate] = None
    produced_at:       datetime
    metadata:          Dict[str, Any] = {}


# ── Typed subclasses (agent-specific) ────────────────────────────────────────

class ContentProcessorInput(ProcessorInput):
    """Input for ContentCreatorProcessor."""
    campaign_brief: CampaignBrief

class ContentProcessorOutput(ProcessorOutput):
    """Output from ContentCreatorProcessor."""
    campaign:         Campaign
    daily_theme_list: List[DailyThemeItem]
    posts:            List[ContentPost]


class TradingProcessorInput(ProcessorInput):
    """Input for TradingProcessor."""
    coin:           str
    units:          float
    side:           str    # long | short
    action:         str    # enter | exit
    market:         bool
    limit_price:    Optional[float]

class TradingProcessorOutput(ProcessorOutput):
    """Output from TradingProcessor."""
    order_intent:   TradingOrderIntent
    draft_only:     bool = True    # True until on_deliverable_approved fires
    executed:       bool = False
    execution:      Optional[Dict[str, Any]] = None
```

---

### 3.5 ConstraintPolicy — mould-level guardrails

**Purpose:** Constraints declared in the mould that the platform enforces at
hook registration time — not buried in downstream service logic.

```python
class ConstraintPolicy(BaseModel):
    """Declared constraints for this agent type.

    Platform enforces these via HookBus before any construct fires.
    Defaults = no limits (permissive baseline).
    """
    # Execution limits
    max_goal_runs_per_day:      Optional[int]   = None   # e.g. 10 for trading
    max_cost_per_run_usd:       Optional[float] = None

    # Trading-specific
    max_position_size_usd:      Optional[float] = None
    max_concurrent_positions:   Optional[int]   = None
    allowed_exchanges:          List[str]       = []     # e.g. ["delta_exchange_india"]

    # Content-specific
    max_posts_per_day:          Optional[int]   = None
    allowed_channels:           List[str]       = []     # e.g. ["linkedin", "instagram"]
    approval_required_before_publish: bool      = True   # overridable per agent

    # Budget (maps to BUDGET dimension)
    max_cost_per_month_usd:     Optional[float] = None
    budget_alert_threshold_pct: float           = 0.8    # alert at 80% spend
```

**Agent profiles:**

| Constraint | Share Trader | Content Creator |
|---|---|---|
| `max_goal_runs_per_day` | 10 | 3 |
| `max_cost_per_run_usd` | 0.0 (no LLM calls) | 0.0 (Grok free tier) |
| `max_position_size_usd` | 500 | — |
| `max_concurrent_positions` | 5 | — |
| `allowed_exchanges` | `["delta_exchange_india"]` | — |
| `allowed_channels` | — | `["linkedin","instagram","youtube"]` |
| `approval_required_before_publish` | `True` | `True` |

---

## 4. Platform Core Constructs

All four constructs below are **owned by the platform**. No agent-specific code
lives inside them. Adding a new agent type never touches these files.

---

### 4.1 Scheduler (Platform Core)

**Purpose:** Decides *when* a Skill's GoalRun is triggered. Fires goal instances
on a cadence (daily, weekly, cron) or on-demand. Completely decoupled from
*what* runs — it only creates a `scheduled_goal_run` row, resolves the agent's
`ConstructBindings` from the registry, and invokes the Pump → Processor → Publisher
pipeline.

**Design principle:** One shared durable scheduler serves all agents. Per-agent
schedules are stored as data (rows in `scheduled_goal_runs`), not as separate
processes. Critical for Cloud Run cost control at scale.

**Responsibility boundary:** Scheduler does NOT know what a campaign is or what a
trade is. It fires, checks constraints, invokes Pump, and routes the result.

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

#### Pre-fire checklist (platform enforced, not agent code)

```
1. scheduler_state.is_paused = false?
2. hired_agents.status in ['trial', 'active']?
3. trial_end_date not expired?
4. ConstraintPolicy.max_goal_runs_per_day not exceeded today?
5. quota_remaining > 0 (Booster pack phase)?
→ All pass → fire; any fail → skip + audit log, emit on_goal_run_fail hook
```

#### Error Handling

| Error type | Behaviour |
|---|---|
| `TransientError` (network, timeout, LLM rate limit) | Exponential backoff: 3× at 1s / 2s / 4s + jitter |
| `PermanentError` (bad config, auth failure) | Fast-fail to DLQ immediately, fire `on_goal_run_dlq` hook |
| Trial expired | Skip silently + audit event, fire `on_trial_end` hook if not already fired |
| ConstraintPolicy violated | Skip + audit event, fire `on_quota_exhausted` or `on_budget_threshold` hook |

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
    goal_instance_id:  str
    status:            GoalRunStatus   # pending|running|completed|failed|retrying
    deliverable_id:    Optional[str]
    error_message:     Optional[str]
    error_type:        Optional[ErrorType]   # transient | permanent
    attempts:          int
    total_duration_ms: Optional[int]
```

---

### 4.2 Pump (Platform Core)

**Purpose:** Assembles the `ProcessorInput` from all data sources that a Processor
needs. The Pump is **read-only and idempotent** — it never modifies source data.

**Important:** In v1 the Pump was embedded inside `GoalSchedulerService`. In v2 it
is a named ABC. The platform provides `GoalConfigPump` as the default implementation.
An agent with unusual data requirements (e.g. fetching live market prices before
a trade) may register a custom Pump in its `ConstructBindings.pump_class`.

#### BasePump ABC

```python
class BasePump(ABC):
    """Platform contract for all Pump implementations.

    Implementations MUST be read-only and idempotent.
    State changes are forbidden inside pull().
    """

    @abstractmethod
    async def pull(self, ctx: PumpContext) -> ProcessorInput:
        """Assemble and return a ProcessorInput for one GoalRun.

        Args:
            ctx: Contains hired_instance_id, skill_id, correlation_id, fired_at.

        Returns:
            ProcessorInput (or typed subclass) ready for the Processor.
        """

    @abstractmethod
    def describe(self) -> str:
        """One-line description of what this Pump reads. Used in health/diagnostic APIs."""


@dataclass(frozen=True)
class PumpContext:
    hired_instance_id: str
    skill_id:          str
    agent_id:          str
    customer_id:       str
    correlation_id:    str
    fired_at:          datetime
    quota_remaining:   Optional[int] = None
```

#### GoalConfigPump (platform default)

```python
class GoalConfigPump(BasePump):
    """Default platform Pump.

    Reads from:
    - agent_skills.goal_config JSONB         (customer-configured params)
    - customer_entity                         (brand_name, industry, locale)
    - hired_agents                            (status, trial_end_date, agent_type_id)
    - performance_stats                       (historical metrics for personalisation)

    Does NOT call any external API.
    Does NOT know what a CampaignBrief or TradingOrderIntent is —
    it only assembles the raw data bag. Typed subclass construction
    is done by each Processor from the base ProcessorInput.
    """

    async def pull(self, ctx: PumpContext) -> ProcessorInput:
        goal_config       = await self._read_goal_config(ctx.hired_instance_id, ctx.skill_id)
        customer_context  = await self._read_customer(ctx.customer_id)
        return ProcessorInput(
            goal_instance_id  = str(uuid4()),
            hired_instance_id = ctx.hired_instance_id,
            customer_id       = ctx.customer_id,
            agent_id          = ctx.agent_id,
            correlation_id    = ctx.correlation_id,
            goal_config       = goal_config,
            customer_context  = customer_context,
            quota_remaining   = ctx.quota_remaining,
            fired_at          = ctx.fired_at,
        )

    def describe(self) -> str:
        return "Reads goal_config JSONB + customer_entity from DB"
```

#### TradingPump (custom Pump for Share Trader)

The Share Trader needs live position data and open order state *before* the
Processor decides whether to enter or exit. This is why Pump override exists.

```python
class TradingPump(BasePump):
    """Pump for TradingProcessor.

    In addition to GoalConfigPump sources, also reads:
    - platform_connections → DeltaExchange credentials (via CredentialResolver)
    - DeltaExchangeClient.get_positions() → current open positions
    This produces a TradingProcessorInput instead of the base ProcessorInput.
    """

    async def pull(self, ctx: PumpContext) -> TradingProcessorInput:
        base     = await GoalConfigPump().pull(ctx)
        creds    = await self._resolve_delta_credentials(ctx.hired_instance_id)
        positions = await self._fetch_open_positions(creds)
        goal_cfg  = base.goal_config
        return TradingProcessorInput(
            **base.model_dump(),
            coin         = goal_cfg["coin"],
            units        = goal_cfg["units"],
            side         = goal_cfg["side"],
            action       = goal_cfg["action"],
            market       = goal_cfg.get("market", True),
            limit_price  = goal_cfg.get("limit_price"),
            open_positions = positions,
        )
```

**Note:** `ConstructBindings.pump_class` for Share Trader is set to
`"agent_mold.skills.trading_pump.TradingPump"`. For Content Creator it uses
the platform default `GoalConfigPump`.

---

### 4.3 Connector (Platform Core)

**Purpose:** Manages the *relationship* between an agent and an external system.
Holds a `credential_ref` (pointer to GCP Secret Manager, never the raw secret).
Verifies connection status.

**Design principle:** `secret_ref` is accepted on `POST` but **never returned in
any GET response**. This is a hard security boundary — auditors, ops, and even
the customer's own API calls cannot retrieve stored credentials. Only the Processor
(via `CredentialResolver`) can resolve `secret_ref` at runtime.

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

#### Interface Contract

```python
# POST /v1/hired-agents/{hired_instance_id}/platform-connections
class CreateConnectionRequest(BaseModel):
    skill_id:     str
    platform_key: str
    secret_ref:   str   # "projects/.../secrets/.../versions/latest"

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

#### Credential Lifecycle

```
Connector.create()  → stores secret_ref, status=pending
Connector.verify()  → calls CredentialResolver, status=connected|error
Connector.resolve() → used by Processor at runtime, never cached
[future] CredentialExpiringSoon event → 48h before OAuth expiry
[future] auto_renew: bool → connector attempts refresh_token before expiry
```

#### Key Code

| File | Purpose |
|---|---|
| `api/v1/platform_connections.py` | CRUD. `secret_ref` is write-only. |
| `services/credential_resolver.py` | Resolves `secret_ref` → actual secret via GCP Secret Manager |
| `services/social_credential_resolver.py` | OAuth-specific credential resolution |
| `core/encryption.py` | AES-256 encryption of credential payloads at rest |

---

### 4.4 Publisher (Platform Core)

**Purpose:** Pushes a finished `ProcessorOutput` to an external destination via
a registered `DestinationAdapter`. Returns a `PublishReceipt`. Idempotent
by design — calling twice with the same `deliverable_id` must not produce
duplicate outputs.

**Design principle:** The Publisher knows nothing about content or trade orders —
it only takes a `PublishInput` and calls the registered `DestinationAdapter`.
Adding a new destination requires only a new adapter file + `registry.register(...)`.
**Zero changes to the Publisher engine or any agent code.**

#### Interface Contract

```python
class DestinationAdapter(ABC):
    DESTINATION_TYPE: str      # e.g. "simulated", "linkedin", "delta_exchange"

    @abstractmethod
    def publish(self, inp: PublishInput) -> PublishReceipt:
        """Idempotent. Same deliverable_id must not publish twice."""

    def estimate_cost(self, inp: PublishInput) -> float:
        """Cost in USD. Default: 0.0 (free tier / simulated)."""
        return 0.0


class PublishInput(BaseModel):
    deliverable_id:   str
    goal_instance_id: str
    hired_instance_id: str
    destination_type: str         # registered adapter key
    payload:          Dict[str, Any]   # ProcessorOutput.payload
    credential_ref:   Optional[str]    # from Connector, if needed
    correlation_id:   str
    scheduled_at:     datetime


class PublishReceipt(BaseModel):
    deliverable_id:     str
    destination_type:   str
    platform_receipt_id: Optional[str]   # real post ID, order ID, etc.
    published_at:       datetime
    cost_usd:           float
    success:            bool
    error:              Optional[str] = None
    metadata:           Dict[str, Any] = {}
```

#### Adapter Registry (startup wiring)

```python
# main.py or lifespan — register all adapters at startup
registry.register("simulated",       SimulatedAdapter)
registry.register("linkedin",        LinkedInAdapter)      # Phase 2
registry.register("instagram",       InstagramAdapter)     # Phase 2
registry.register("delta_exchange",  DeltaTradeAdapter)    # Share Trader
```

**Share Trader Publisher note:** `DeltaTradeAdapter.publish()` places the actual
order on Delta Exchange. This adapter is only invoked *after* `on_deliverable_approved`
fires — i.e., customer has explicitly approved the trade intent.

#### Key Code

| File | Purpose |
|---|---|
| `agent_mold/skills/publisher_engine.py` | `DestinationAdapter` ABC + `DestinationRegistry` + `PublisherEngine` |
| `agent_mold/skills/adapters_publish.py` | `SimulatedAdapter` (live today) |
| `integrations/delta_exchange/orders.py` | Delta order placement (used by DeltaTradeAdapter) |
| `integrations/social/linkedin_client.py` | LinkedIn posting (used by LinkedInAdapter) |

---

## 5. Agent-Specific Construct: Processor

The Processor is the **only** construct that varies per agent type. It is the AI
brain. It takes a `ProcessorInput` and produces a `ProcessorOutput`. It may make
LLM API calls, domain API calls, or pure computation — but it never touches the DB
directly (that is the Publisher's job) and it never manages credentials
(that is the Connector's job).

---

### 5.1 BaseProcessor — the common contract

```python
class BaseProcessor(ABC):
    """Every agent's Processor must implement this interface.

    The mould references a Processor by class path in ConstructBindings.
    The platform instantiates it at GoalRun time.
    """

    PROCESSOR_ID: ClassVar[str]     # e.g. "content.creator.v1"
    PROCESSOR_VERSION: ClassVar[str] = "1.0.0"

    @abstractmethod
    async def execute(self, input: ProcessorInput) -> ProcessorOutput:
        """Core execution. May call LLMs, external APIs, or run pure logic.

        Must NOT access the database.
        Must NOT manage credentials (use input.goal_config for references).
        Must NOT publish outputs (Publisher handles that).
        """

    def estimate_cost(self, input: ProcessorInput) -> CostEstimate:
        """Pre-execution cost estimate. Called by Scheduler before firing.
        Default: zero cost. Override if processor makes paid API calls.
        """
        return CostEstimate(total_theme_items=0, total_posts=0, llm_calls=0,
                           cost_per_call_usd=0.0, total_cost_usd=0.0, total_cost_inr=0.0,
                           model_used="none")

    def describe(self) -> str:
        """One-line description for health/diagnostic APIs."""
        return f"{self.PROCESSOR_ID} v{self.PROCESSOR_VERSION}"
```

---

### 5.2 ContentCreatorProcessor

**Skill:** `content.creator.v1`
**What it does:** Given a `ContentProcessorInput` (containing `CampaignBrief`),
produces a `ContentProcessorOutput` (DailyThemeList + ContentPosts) using either
the deterministic template engine or the Grok-3 API.

```python
class ContentCreatorProcessor(BaseProcessor):
    PROCESSOR_ID      = "content.creator.v1"
    PROCESSOR_VERSION = "1.0.0"

    async def execute(self, input: ProcessorInput) -> ContentProcessorOutput:
        typed = ContentProcessorInput.from_base(input)   # cast + validate
        campaign = self._build_campaign(typed)

        if _executor_backend() == "grok":
            theme_list = await self._grok_theme_list(campaign)
        else:
            theme_list = self._deterministic_theme_list(campaign)

        posts = [self._generate_posts(item) for item in theme_list]
        return ContentProcessorOutput(
            goal_instance_id  = input.goal_instance_id,
            hired_instance_id = input.hired_instance_id,
            agent_id          = input.agent_id,
            correlation_id    = input.correlation_id,
            deliverable_type  = "content_campaign",
            payload           = {},   # populated from campaign/theme_list/posts below
            produced_at       = datetime.now(timezone.utc),
            campaign          = campaign,
            daily_theme_list  = theme_list,
            posts             = posts,
        )

    def estimate_cost(self, input: ProcessorInput) -> CostEstimate:
        brief = CampaignBrief(**input.goal_config)
        model = "grok-3-latest" if _executor_backend() == "grok" else "deterministic"
        return estimate_cost(brief, model_used=model)
```

**Engine selection (per-agent, not global):**

The `EXECUTOR_BACKEND` env var is an *instance default* that the agent's
`ConstructBindings` can override via a `processor_config` dict. This removes the
platform-wide global switch antipattern — different customers hiring the same agent
type CAN use different backends in future.

#### Key Code

| File | Purpose |
|---|---|
| `agent_mold/skills/content_creator.py` | `ContentCreatorSkill` (v1 implementation — to be refactored to `ContentCreatorProcessor`) |
| `agent_mold/skills/content_models.py` | All content/campaign models |
| `agent_mold/skills/grok_client.py` | Async HTTP wrapper for xAI API with circuit breaker |
| `agent_mold/skills/adapters.py` | Channel adapters: LinkedIn, Instagram, YouTube, Facebook, WhatsApp |
| `agent_mold/skills/executor.py` | `execute_marketing_multichannel_v1()` channel pipeline |

---

### 5.3 TradingProcessor

**Skill:** `trading.delta.futures.manual.v1`
**What it does:** Given a `TradingProcessorInput` (pre-assembled by TradingPump
including live position state), produces a `TradingProcessorOutput` containing a
`TradingOrderIntent` in *draft* mode. The order is NOT placed here.
Actual placement happens in `on_deliverable_approved` → `DeltaTradeAdapter`.

```python
class TradingProcessor(BaseProcessor):
    PROCESSOR_ID      = "trading.delta.futures.manual.v1"
    PROCESSOR_VERSION = "1.0.0"

    async def execute(self, input: ProcessorInput) -> TradingProcessorOutput:
        typed = TradingProcessorInput.from_base(input)

        intent = TradingOrderIntent(
            exchange_provider    = "delta_exchange_india",
            exchange_account_id  = typed.goal_config.get("exchange_account_id", ""),
            coin                 = typed.coin.upper(),
            units                = typed.units,
            side                 = typed.side,
            action               = typed.action,
            order_type           = "market" if typed.market else "limit",
            limit_price          = typed.limit_price,
        )
        return TradingProcessorOutput(
            goal_instance_id  = input.goal_instance_id,
            hired_instance_id = input.hired_instance_id,
            agent_id          = input.agent_id,
            correlation_id    = input.correlation_id,
            deliverable_type  = "trade_order",
            payload           = intent.model_dump(),
            produced_at       = datetime.now(timezone.utc),
            order_intent      = intent,
            draft_only        = True,    # Publisher will not call Delta until approval
            executed          = False,
        )

    def estimate_cost(self, input: ProcessorInput) -> CostEstimate:
        # Trading processor makes zero LLM calls — no cost
        return CostEstimate(llm_calls=0, total_cost_usd=0.0, total_cost_inr=0.0,
                           model_used="none", total_theme_items=0, total_posts=0,
                           cost_per_call_usd=0.0)
```

**Draft → Execute flow (critical for trading):**

```
TradingProcessor.execute() → TradingProcessorOutput(draft_only=True)
      ↓ Publisher stores as Deliverable(status=pending_review)
      ↓ LifecycleHook: on_deliverable_pending_review → notify customer
      ↓ Customer approves via /cp/deliverables/{id}/approve
      ↓ LifecycleHook: on_deliverable_approved
      ↓ DeltaTradeAdapter.publish(PublishInput) → places order on Delta Exchange
      ↓ PublishReceipt written → Deliverable(status=published, platform_receipt_id=<order_id>)
```

**Why draft-only from Processor?** The Processor never has side effects on external
systems. This is a constitutional rule — it makes every Processor unit-testable
without mocking external APIs, and gives the approval gate a natural home outside
the Processor.

#### Key Code

| File | Purpose |
|---|---|
| `agent_mold/skills/trading_executor.py` | `execute_trading_delta_futures_manual_v1()` (v1 — to be refactored to `TradingProcessor`) |
| `integrations/delta_exchange/client.py` | `DeltaExchangeClient` — HMAC-signed HTTP wrapper |
| `integrations/delta_exchange/orders.py` | Order placement + response parsing |
| `integrations/delta_exchange/risk_engine.py` | Pre-order risk checks |

---

## 6. Hook Architecture

### 6.1 Overview

The platform has two complementary hook systems:

| System | Scope | Purpose |
|---|---|---|
| **HookBus** (construct-level) | Per GoalRun execution | Gate external actions (publish, place_order) at each construct boundary |
| **LifecycleHooks** (agent-level) | Platform lifecycle events | React to hire/trial/cancel/approval events |

These are distinct by design. HookBus is synchronous and blocking (a DENY stops
execution). LifecycleHooks are async and non-blocking (they fire-and-observe).

### 6.2 HookBus — construct-level interception

#### Stage mapping to construct pipeline

```python
class HookStage(str, Enum):
    # ── Platform lifecycle ─────────────────────────────────────────────────
    SESSION_START   = "session_start"     # hired agent first activated
    SESSION_END     = "session_end"       # hired agent cancelled/expired

    # ── GoalRun pipeline ──────────────────────────────────────────────────
    PRE_PUMP        = "pre_pump"          # NEW: before Pump.pull() — quota check
    PRE_PROCESSOR   = "pre_processor"     # replaces PRE_SKILL — before Processor.execute()
    PRE_TOOL_USE    = "pre_tool_use"      # before any external API call inside Processor
    POST_TOOL_USE   = "post_tool_use"     # after external API call — log cost/receipt
    POST_PROCESSOR  = "post_processor"    # replaces POST_SKILL — after Processor produces output
    PRE_PUBLISH     = "pre_publish"       # NEW: before Publisher.publish() — approval gate
    POST_PUBLISH    = "post_publish"      # NEW: after Publisher.publish() — receipt audit
```

**Migration note:** `PRE_SKILL` and `POST_SKILL` are kept as aliases for
`PRE_PROCESSOR` / `POST_PROCESSOR` during the transition period. Remove aliases
in v3.

#### HookBus decision chain

```
HookBus.emit(event: HookEvent) → HookDecision
  ├── iterate registered hooks for stage in order
  ├── first DENY → stop chain, return DENY with decision_id
  └── all ALLOW or abstain → return ALLOW with decision_id
```

#### Platform hooks registered at startup

| Stage | Hook | What it enforces |
|---|---|---|
| `PRE_PUMP` | `QuotaGateHook` | `quota_remaining > 0` (Booster pack) |
| `PRE_PUMP` | `SchedulerPauseHook` | `scheduler_state.is_paused = false` |
| `PRE_PROCESSOR` | `ConstraintPolicyHook` | `max_goal_runs_per_day` not exceeded |
| `PRE_TOOL_USE` | `ApprovalRequiredHook` | External actions need `approval_id` |
| `PRE_PUBLISH` | `ApprovalGateHook` | `approval_mode != auto` requires approval before publish |
| `POST_PUBLISH` | `CostAuditHook` | Log cost to metering service |

#### Per-agent hook registration

Each AgentSpec's `DimensionContract.register_hooks()` is called at mould
compilation time. Example for Share Trader INTEGRATIONS dimension:

```python
class TradingIntegrationsDimension(DimensionContract):
    name = DimensionName.INTEGRATIONS

    def register_hooks(self, hook_bus: HookBus) -> None:
        # Only allow orders on allowed exchanges from ConstraintPolicy
        hook_bus.register(HookStage.PRE_TOOL_USE,
            AllowedExchangeHook(allowed=["delta_exchange_india"]))
        # Log every order attempt to trading audit trail
        hook_bus.register(HookStage.POST_TOOL_USE,
            TradingAuditHook())
```

### 6.3 LifecycleHooks wiring

```python
# At hire time (api/v1/hired_agents_simple.py)
spec      = registry.get_spec(agent_type_id)
hooks_cls = spec.construct_bindings.lifecycle_hooks_class  # e.g. TradingLifecycleHooks
hooks     = hooks_cls()
await hooks.on_hire(ctx)
await hooks.on_trial_start(ctx)

# At deliverable approval (api/v1/deliverables.py)
await hooks.on_deliverable_approved(ctx)      ← this triggers DeltaTradeAdapter for trading
                                              ← this triggers Publisher.publish() for content
```

---

## 7. Agent Profile Validation

This section validates every design decision in §3–§6 against the two canonical agents.

### 7.1 Share Trader — full profile

| Property | Value |
|---|---|
| `agent_id` | `AGT-TRADING-001` |
| `agent_type` | `trading` |
| `processor_class` | `TradingProcessor` |
| `pump_class` | `TradingPump` (custom — fetches live positions) |
| `publisher_class` | platform default (`DestinationPublisher`) |
| `connector_class` | platform default (`SecretManagerConnector`) |
| Required dimensions | SKILL, INTEGRATIONS, INDUSTRY, TRIAL, BUDGET |
| `ConstraintPolicy` | `max_goal_runs_per_day=10`, `max_position_size_usd=500`, `allowed_exchanges=["delta_exchange_india"]` |
| Approval required | Yes — `approval_required_before_publish=True` |

**End-to-end execution:**

```
1. Scheduler fires at cron expression
2. HookBus: PRE_PUMP → SchedulerPauseHook (pass) → ConstraintPolicyHook (check daily limit)
3. TradingPump.pull() → reads goal_config + resolves Delta creds + fetches open positions
4. HookBus: PRE_PROCESSOR (pass)
5. TradingProcessor.execute() → produces TradingProcessorOutput(draft_only=True, order_intent)
6. HookBus: POST_PROCESSOR (pass)
7. HookBus: PRE_PUBLISH → ApprovalGateHook → DENY (approval required, draft mode)
8. Deliverable stored as pending_review
9. LifecycleHook: on_deliverable_pending_review → push notification to customer
10. Customer approves → LifecycleHook: on_deliverable_approved
11. HookBus: PRE_PUBLISH → ApprovalGateHook → ALLOW (approval_id present)
12. DeltaTradeAdapter.publish() → places order → PublishReceipt(platform_receipt_id=<order_id>)
13. LifecycleHook: on_goal_run_complete
```

**Hooks implemented (overrides from AgentLifecycleHooks):**

```python
class TradingLifecycleHooks(AgentLifecycleHooks):
    async def on_hire(self, ctx):
        await ping_delta_exchange_credentials(ctx)   # validate API key works

    async def on_trial_day_N(self, ctx, day):
        await send_daily_pnl_summary(ctx)

    async def on_trial_end(self, ctx):
        await send_simulated_returns_report(ctx)

    async def on_deliverable_approved(self, ctx):
        # Trigger actual order — this is the only place real money moves
        await DeltaTradeAdapter().execute_approved_order(ctx)

    async def on_cancel(self, ctx):
        await close_all_open_positions_if_any(ctx)

    async def on_quota_exhausted(self, ctx):
        await notify_operator_trading_paused(ctx)
```

---

### 7.2 Content Creator — full profile

| Property | Value |
|---|---|
| `agent_id` | `AGT-MKT-BEAUTY-001` (example) |
| `agent_type` | `marketing` |
| `processor_class` | `ContentCreatorProcessor` |
| `pump_class` | platform default `GoalConfigPump` |
| `publisher_class` | platform default (`DestinationPublisher`) |
| `connector_class` | platform default (`SecretManagerConnector`) |
| Required dimensions | SKILL, INDUSTRY, TRIAL, BUDGET |
| `ConstraintPolicy` | `max_goal_runs_per_day=3`, `allowed_channels=["linkedin","instagram"]`, `approval_required_before_publish=True` |

**End-to-end execution:**

```
1. Scheduler fires at cron expression
2. HookBus: PRE_PUMP → all platform hooks pass
3. GoalConfigPump.pull() → reads CampaignBrief from goal_config + customer brand_name
4. HookBus: PRE_PROCESSOR (pass)
5. ContentCreatorProcessor.execute() → generates DailyThemeList + ContentPosts
6. HookBus: POST_PROCESSOR (pass)
7. HookBus: PRE_PUBLISH → ApprovalGateHook → DENY (approval_mode=per_item, themes need approval)
8. DailyThemeItems stored as pending_review deliverables
9. LifecycleHook: on_deliverable_pending_review → push notification to customer
10a. Customer approves theme → on_deliverable_approved → posts for that day become publishable
10b. Customer rejects theme → on_deliverable_rejected → theme queued for revision
11. For each approved ContentPost:
    HookBus: PRE_PUBLISH → ApprovalGateHook → ALLOW
    LinkedInAdapter / InstagramAdapter → PublishReceipt
12. LifecycleHook: on_goal_run_complete
```

**Hooks implemented:**

```python
class ContentCreatorLifecycleHooks(AgentLifecycleHooks):
    async def on_hire(self, ctx):
        await send_campaign_setup_guide(ctx)

    async def on_trial_day_N(self, ctx, day):
        await send_posts_published_today_summary(ctx, day)

    async def on_trial_end(self, ctx):
        await publish_trial_portfolio_summary(ctx)

    async def on_deliverable_approved(self, ctx):
        # Trigger publisher for approved posts
        await trigger_post_publishing(ctx)

    async def on_deliverable_rejected(self, ctx):
        await queue_content_for_revision(ctx)

    async def on_cancel(self, ctx):
        await archive_campaign_artefacts(ctx)
```

---

### 7.3 Side-by-side comparison

| Design Decision | Share Trader | Content Creator | Platform handles? |
|---|---|---|---|
| Pump type | Custom `TradingPump` | Default `GoalConfigPump` | Both — platform calls `pump_class` from ConstructBindings |
| Processor type | `TradingProcessor` | `ContentCreatorProcessor` | Both — platform calls `processor_class` |
| Publisher adapter | `DeltaTradeAdapter` (real money) | `LinkedInAdapter` / `SimulatedAdapter` | Both — registry lookup by destination_type |
| Draft-only gate | Yes — order intent only | Yes — theme + posts need approval | Both — `ApprovalGateHook` at PRE_PUBLISH |
| Approval triggers side effect | Actual order on Delta Exchange | Post to social platform | Both handled in `on_deliverable_approved` hook override |
| Lifecycle hooks needed | 6 overrides | 5 overrides | Rest are no-ops in base class |
| ConstraintPolicy | Risk limits + exchange allowlist | Channel allowlist + posts/day cap | Both — `ConstraintPolicyHook` at PRE_PROCESSOR |
| External credentials | Delta API key (via Secret Manager) | OAuth tokens (LinkedIn, etc.) | Both — `SecretManagerConnector` (platform default) |

---

## 8. Construct Execution Flow (v2)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SCHEDULER (Platform Core)                                                   │
│  GoalSchedulerService fires at next_run_at                                  │
│  Resolves: ConstructBindings from in-memory AgentSpec registry              │
│  Checks: trial valid? scheduler not paused? constraint_policy passes?       │
│  HookBus: PRE_PUMP → QuotaGateHook, SchedulerPauseHook                     │
│  Creates: goal_instances row (status=running)                               │
│  Fires LifecycleHook: on_goal_run_start                                     │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PUMP (Platform Core — default GoalConfigPump OR custom per ConstructBindings)│
│  Reads: agent_skills.goal_config JSONB                                      │
│  Reads: customer_entity (brand, industry)                                   │
│  Reads: hired_agents (status, trial_end_date)                               │
│  [TradingPump also] Reads: platform_connections + live positions            │
│  Assembles: ProcessorInput (or typed subclass)                              │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PROCESSOR (Agent-Specific — class from ConstructBindings.processor_class)   │
│  HookBus: PRE_PROCESSOR → ConstraintPolicyHook                              │
│  Calls: LLM (ContentCreatorProcessor) or pure logic (TradingProcessor)      │
│  HookBus: PRE_TOOL_USE → ApprovalRequiredHook (for any external API call)  │
│  Produces: ProcessorOutput(draft_only=True for trading/approval-gated)      │
│  HookBus: POST_PROCESSOR                                                    │
│  Does NOT write to DB. Does NOT call Publisher. Purely computational.       │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼ (approval gate — may pause here)
┌─────────────────────────────────────────────────────────────────────────────┐
│ CONNECTOR (Platform Core — SecretManagerConnector)                          │
│  Reads: platform_connections.secret_ref for destination                     │
│  Calls: CredentialResolver → GCP Secret Manager                            │
│  Provides: live credential to Publisher (never stored in memory longer)     │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PUBLISHER (Platform Core — DestinationPublisher)                            │
│  HookBus: PRE_PUBLISH → ApprovalGateHook                                   │
│  Calls: DestinationAdapter.publish(PublishInput) → PublishReceipt           │
│  HookBus: POST_PUBLISH → CostAuditHook                                     │
│  Persists: deliverables row (status=published)                              │
│  Updates: goal_instances status=completed                                   │
│  Fires LifecycleHook: on_goal_run_complete                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. NFR Requirements Per Construct

Every construct invocation point **must** satisfy the platform-wide NFR standards
from `docs/CP/iterations/NFRReusable.md`:

| NFR | Where applied |
|---|---|
| `waooaw_router()` factory | All API routes in `scheduler_admin.py`, `platform_connections.py`, `campaigns.py` |
| `get_read_db_session` on GETs | Pump reads, Scheduler health, Publisher receipt reads |
| `PIIMaskingFilter` on all loggers | All construct service files — email, phone, name never logged raw |
| `@circuit_breaker(service=...)` | `GrokClient` (ContentCreatorProcessor), `CredentialResolver` (Connector), `DeltaExchangeClient` (TradingPump), `DestinationAdapter.publish()` (Publisher) |
| `X-Correlation-ID` propagation | Threaded from Scheduler through every construct to PublishReceipt |
| OTel span per construct | `"scheduler.fire"`, `"pump.pull"`, `"processor.execute"`, `"connector.resolve"`, `"publisher.publish"` |
| Audit log on state mutation | GoalRun create/complete/fail, Deliverable approve/reject, PublishReceipt write, Order placement |

---

## 10. Environment Flags Governing Constructs

| Flag | Default | Effect |
|---|---|---|
| `EXECUTOR_BACKEND` | `deterministic` | Per-agent default backend for `ContentCreatorProcessor`; overridden by `ConstructBindings` |
| `CAMPAIGN_PERSISTENCE_MODE` | `memory` | `db` → Processor writes to PostgreSQL |
| `XAI_API_KEY` | unset | Required when `EXECUTOR_BACKEND=grok` |
| `CIRCUIT_BREAKER_ENABLED` | `true` | Set `false` in test only |
| `SCHEDULER_ENABLED` | `true` | Set `false` to disable all Scheduler firing |
| `APPROVAL_GATE_ENABLED` | `true` | Set `false` to bypass ApprovalGateHook in dev/demo |

---

## 11. Gap Register (v2 — updated)

Items resolved in v2 are marked ✅. Open gaps are carried forward.

| # | Gap | Status | Impact | Planned in |
|---|---|---|---|---|
| G1 | `BaseProcessor` ABC absent — ContentCreatorSkill / TradingExecutor not connected to mould | **Design ready in §5** — implementation in next sprint | Cannot unit test processors against a common contract | Next sprint |
| G2 | `BasePump` ABC absent — embedded in GoalSchedulerService | **Design ready in §4.2** — implementation in next sprint | Cannot add quota-awareness without touching Scheduler | Next sprint |
| G3 | No `LifecycleHooks` on mould | **Design ready in §3.3** — full ABC defined | Lifecycle behaviour scattered across services | Next sprint |
| G4 | No `ConstructBindings` in `AgentSpec` | **Design ready in §3.2** | Global EXECUTOR_BACKEND env var unsuitable for multi-agent simultaneous runs | Next sprint |
| G5 | No `ProcessorInput`/`ProcessorOutput` base types | **Design ready in §3.4** | Untyped pump→processor→publisher chain | Next sprint |
| G6 | `HookStage` disconnected from construct pipeline boundaries | **Design updated in §6.2** — `PRE_PUMP`, `PRE_PUBLISH`, `POST_PUBLISH` added | Cannot intercept at construct level | Next sprint |
| G7 | `DimensionContract.register_hooks()` / `observe()` always return None | Open — `BasicDimension` still a no-op | TRIAL quota / BUDGET enforcement only in docs | Booster Pack plan |
| G8 | `ConstraintPolicy` not in `AgentSpec` | **Design ready in §3.5** | Trading risk + content rate limits not enforced at mould level | Next sprint |
| G9 | No `OutcomeMetric` definition | Open | Cannot auto-trigger trial-to-paid conversion | Outcome Scoring plan |
| G10 | `approval_mode=auto` not enforced by Scheduler | Open | Posts sit in `pending_review` forever | Next sprint (quick fix) |
| G11 | `CredentialExpiringSoon` event missing | Open | OAuth tokens expire silently | Connector Marketplace Phase 2 |
| G12 | A2A pipe (one agent's Publisher → another's Pump) | Open | Platform locked to single-agent workflows | Platform Iteration 2 |
| G13 | `DeltaTradeAdapter` not yet implemented | Open | Trading stays draft-only until adapter is built | Trading Phase 2 |

---

## 13. CP — Customer Portal: Agent-Centric Experience

> **Metaphor**: The customer is the **car driver**. They see the dashboard — speed, fuel, warning lights, controls that matter for the journey. They never open the bonnet. Constructs run the engine; the CP dashboard surfaces only outcome-relevant signals.

### 13.1 Design Philosophy

| Driver sees | What maps to it |
|---|---|
| Fuel gauge | Trial budget: `tasks_used / trial_task_limit` |
| RPM / speed | Cadence card: "Posts 3×/day · Next at 2pm" |
| Warning light | Hook event: credential expiring, DLQ entry, approval pending |
| Gear selection | approval_mode: MANUAL (driver controls) vs AUTO (cruise control) |
| Dashboard readout | Deliverable card: outcome of last agent run |
| Navigation lane | Goal config: customer tells the agent *where* to drive |
| Service due light | LifecycleHook `POST_PUBLISH` failure or connector nearing expiry |

**Customer must never see**: Pump latency, HookBus stages, DB table names, secret references, processor backend names, LLM costs, raw cron expressions, DLQ internals.

### 13.2 How Constructs Surface in CP UX

| Plant Construct | CP UX Layer | Mobile Screen | Customer Experience |
|---|---|---|---|
| `AgentSpec` (mould) | Agent Catalogue card | DiscoverScreen, AgentDetailScreen | "What this agent does, what it costs, what I get" |
| HireWizard + `ConstructBindings` | Hire setup wizard | HireWizardScreen | "Connect my exchange / give my campaign brief" |
| `Scheduler` + `ScheduledGoalRun` | Cadence indicator on agent card | MyAgentsScreen | "Active · Posts daily at 9am" |
| `BasePump` + data source | Data source setup section | HireWizardScreen | "Where does your agent get its data?" |
| `BaseProcessor` | Hidden — spinner only | MyAgentsScreen | Agent status: 🟡 Working / 🟢 Ready |
| `LifecycleHooks` | Push notification + status badge | NotificationsScreen | "⚠️ Trade plan ready for your approval" |
| `Publisher` + `Deliverable` | Deliverable card | HiredAgentsListScreen | "Here is what your agent delivered" |
| `Connector` + credential | Platform connections UI | HireWizardScreen + profile | "LinkedIn ✅ · Expires in 17 days ⚠️" |
| `ConstraintPolicy` | Risk profile + trial gauge | TrialDashboardScreen | "Max 5 trades/day · Trial: 3 of 10 used" |
| `approval_mode` | Approve/reject flow | TrialDashboardScreen | "Review before posting" toggle |

### 13.3 Gateway → CP Route Architecture

```
Customer App (mobile)
        │  JWT (issued by CP BackEnd / Razorpay identity)
        ▼
CP BackEnd  ──── PlantGatewayClient (internal JWT) ────►  Plant Gateway
                                                                │
                                              ┌─────────────────┤
                                              │  OPA checks:    │
                                              │  1. trial_mode  │ → caps tasks_used ≤ 10
                                              │  2. governor_role│ → 5 sensitive actions need approval token
                                              │  3. sandbox_routing │ → trial hires → Plant sandbox
                                              └─────────────────┤
                                                                │
                                                                ▼
                                                      Plant BackEnd
```

**Governor-gated actions** (customer must hold an approval token for these CP routes):

| CP Route | Governor reason |
|---|---|
| `POST /cp/trading/approve-execute` | Financial action — irreversible |
| `POST /cp/hired-agents/{id}/platform-connections` | OAuth credential storage |
| `DELETE /cp/hired-agents/{id}/platform-connections/{conn_id}` | Credential removal |
| `POST /cp/hire/wizard/finalize` | Subscription commitment |
| `PATCH /cp/hired-agents/{id}/skills/{skill_id}/goal-config` | Goal override in production |

### 13.4 CP Route Surface (Current + Recommended)

#### Hire Journey
| Method | Route | CP → Plant | Purpose |
|---|---|---|---|
| `PUT` | `/cp/hire/wizard/draft` | Plant: upsert draft hire | Save progress |
| `GET` | `/cp/hire/wizard/by-subscription/{id}` | Plant: get hire by subscription | Resume wizard |
| `POST` | `/cp/hire/wizard/finalize` | Plant: finalize + create subscription | Commit hire |

#### Active Agent Management
| Method | Route | CP → Plant | Purpose |
|---|---|---|---|
| `GET` | `/cp/hired-agents/{id}/goals` | Plant: list goals | View schedule |
| `PUT` | `/cp/hired-agents/{id}/goals` | Plant: upsert goal | Update cadence |
| `DELETE` | `/cp/hired-agents/{id}/goals` | Plant: delete goal | Pause agent |
| `GET` | `/cp/hired-agents/{id}/deliverables` | Plant: list deliverables | Outcome history |
| `POST` | `/cp/deliverables/{id}/review` | Plant: review deliverable | Approve/reject result |
| `GET` | `/cp/hired-agents/{id}/performance-stats` | Plant: stats aggregation | Outcome metrics |

#### Content Agent Routes
| Method | Route | CP → Plant | Purpose |
|---|---|---|---|
| `GET` | `/cp/marketing/draft-batches` | Plant: get pending themes | Customer review queue |
| `POST` | `/cp/marketing/draft-posts/approve` | Plant: approve + schedule | Approve a post |
| `POST` | `/cp/marketing/draft-posts/reject` | Plant: reject with reason | Reject with feedback |
| `POST` | `/cp/marketing/draft-posts/schedule` | Plant: schedule post | Defer to specific time |

#### Trading Routes
| Method | Route | CP → Plant | Purpose |
|---|---|---|---|
| `POST` | `/cp/trading/draft-plan` | Plant: generate draft plan | Request trade plan |
| `POST` | `/cp/trading/approve-execute` | Plant → DeltaExchangeClient | Approve + execute trade |

#### Setup & Connections
| Method | Route | CP → Plant | Purpose |
|---|---|---|---|
| `GET` | `/cp/hired-agents/{id}/skills` | Plant: list skills | What capabilities are active |
| `PATCH` | `/cp/hired-agents/{id}/skills/{skill_id}/goal-config` | Plant: save config | Tune skill parameters |
| `GET/POST/DELETE` | `/cp/hired-agents/{id}/platform-connections` | Plant: manage credentials | OAuth/API key setup |

#### ⚠️ Missing Routes — Recommended Additions

| Method | Proposed Route | Purpose | Priority |
|---|---|---|---|
| `GET` | `/cp/hired-agents/{id}/scheduler-summary` | Customer-facing cadence: "Runs daily · Next: 2pm · Today: 3/5 tasks" — hides cron | High |
| `GET` | `/cp/hired-agents/{id}/trial-budget` | Trial task gauge: `{used: 7, limit: 10, resets_at: ...}` | High |
| `POST` | `/cp/hired-agents/{id}/pause` | Customer can pause/resume without deleting the goal | High |
| `GET` | `/cp/hired-agents/{id}/notifications-config` | Notification preferences per agent hire | Medium |
| `GET` | `/cp/hired-agents/{id}/approval-queue` | Unified approval queue (posts + trade plans) | Medium |

### 13.5 Share Trader CP Experience — End-to-End

**Customer: Priya, 34, retail investor, 7-day trial**

#### Step 1 — Discovery (DiscoverScreen)
```
┌───────────────────────────────────────┐
│  🤖  Share Trader                      │
│  Algo trading · NSE/BSE                │
│  ⭐ 4.8  |  342 hires  |  ₹12,000/mo  │
│  "I analyse markets and execute        │
│   trades when conditions are right"    │
│  [Start 7-Day Trial]                   │
└───────────────────────────────────────┘
```
Backend: GET /agents (Plant) → AgentSpec `trading_agent` from `reference_agents.py`

#### Step 2 — Hire Wizard Setup (HireWizardScreen)
Four steps surfaced to customer (maps to ConstructBindings):

| Wizard Step | Customer Sees | Maps To |
|---|---|---|
| Exchange connect | "Connect Delta Exchange account" | `Connector` — POST /cp/.../platform-connections → DeltaConnector |
| Risk profile | "Max ₹50,000 per trade · 5 trades/day" | `ConstraintPolicy.max_position_size_inr`, `max_trades_per_day` |
| Approval mode | "Review each trade before execution" toggle | `ConstraintPolicy.approval_mode = MANUAL` |
| Schedule | "Active during market hours" | `Scheduler` cron `0 9 * * Mon-Fri` |

Customer never sees: `DeltaExchangeClient`, `TradingPump`, `secret_ref`, cron syntax.

#### Step 3 — MyAgentsScreen Trial Tab
```
┌─────────────────────────────────────────┐
│  Share Trader          🟡 Analysing     │
│  Trial · 2 of 10 tasks used             │
│  Active: market hours                   │
│  Last action: Draft plan ready  ──────► │
└─────────────────────────────────────────┘
```
Data: GET /cp/hired-agents (summary) + GET /cp/hired-agents/{id}/trial-budget (proposed)

#### Step 4 — Approval Flow (TrialDashboardScreen)
```
┌──────────────────────────────────────────┐
│  📋 Trade Plan Ready                      │
│  NIFTY50 PUT · Qty: 1 lot                 │
│  Entry: ₹47,500 · SL: ₹46,800            │
│  Estimated risk: ₹700 (1.4% of limit)    │
│                                          │
│         [Reject]    [Approve & Execute]  │
└──────────────────────────────────────────┘
```
On approve: POST /cp/trading/approve-execute → Plant Gateway (governor check) → TradingProcessor → DeltaExchangeClient

#### Step 5 — Outcome (HiredAgentsListScreen)
```
┌─────────────────────────────────────────┐
│  ✅ Trade Executed                       │
│  NIFTY50 PUT · 16 Jan 2024 · 10:23 AM   │
│  Realised P&L: +₹1,200                  │
│  Receipt: TXN-2024-001847               │
│  [View Details]                         │
└─────────────────────────────────────────┘
```
Data: GET /cp/hired-agents/{id}/deliverables → `deliverable.publish_receipt` JSONB

#### Step 6 — Performance Card
```
  Win rate:    68% (17/25 trades)
  Total return: +₹8,400 (trial period)
  Max drawdown: -₹2,100
  Avg trade duration: 2h 14m
```
Data: GET /cp/hired-agents/{id}/performance-stats

**UI Compliance rules for Share Trader:**
- Show instrument, quantity, price range, estimated risk — hide DeltaExchangeClient, Pump lag, HookBus stage names
- API key setup via `/cp/hired-agents/{id}/platform-connections` only — raw key never touches app state
- Approval modal is non-dismissable until customer taps Approve or Reject (no accidental swipe-away)

### 13.6 Content Creator CP Experience — End-to-End

**Customer: Rahul, 28, beauty brand owner, hired (post-trial)**

#### Step 1 — Discovery (DiscoverScreen)
```
┌───────────────────────────────────────┐
│  ✍️  Content Creator                   │
│  Beauty & wellness · Instagram/LinkedIn│
│  ⭐ 4.9  |  218 hires  |  ₹9,000/mo  │
│  "Daily content that builds your brand"│
│  [Hire Now]                            │
└───────────────────────────────────────┘
```

#### Step 2 — Hire Wizard Setup
| Wizard Step | Customer Sees | Maps To |
|---|---|---|
| Campaign brief | "Product: GlowRevive Serum · Tone: Warm · Target: 25-35 F" | `GoalConfigPump` source — PATCH /cp/.../goal-config |
| Connect accounts | "Connect Instagram / LinkedIn" | `Connector` — POST /cp/.../platform-connections → OAuthConnector |
| Posting schedule | "3 posts per day: 8am, 1pm, 6pm" | `Scheduler` cron `0 8,13,18 * * *` |
| Review preference | "I'll review each post before it goes live" | `ConstraintPolicy.approval_mode = MANUAL` |

#### Step 3 — MyAgentsScreen (hired, not trial)
```
┌─────────────────────────────────────────┐
│  Content Creator       🟢 Campaign live │
│  Hired · 3 posts/day                    │
│  Today: 5 drafts awaiting your review   │
│  Next post window: 1:00 PM              │
└─────────────────────────────────────────┘
```

#### Step 4 — Draft Review (Approval Queue)
```
  📚 Theme: "Morning glow ritual — Day 14"
  ┌──────────────┬──────────────┬──────────────┐
  │ Instagram     │ LinkedIn      │ Twitter/X    │
  │ [Image mock]  │ [Article hook]│ [Thread 1/3] │
  │ "Start your   │ "How GlowRev" │ "#SkinCare"  │
  │  day with..." │  ...          │              │
  │ ✓ Approve    │ ✓ Approve    │ ✗ Reject     │
  └──────────────┴──────────────┴──────────────┘
       [Approve All in Theme]   [Reject Theme]
```
Data: GET /cp/marketing/draft-batches → grouped by `daily_theme_items.theme_title`
Actions: POST /cp/marketing/draft-posts/approve (per post) or bulk via theme root

On reject: customer enters reason → stored in `daily_theme_items.rejection_reason` → feeds `PRE_PROCESSOR` hook on next cycle so ContentCreatorProcessor sees the feedback.

#### Step 5 — Outcome
```
  ✅ Instagram · Posted 16 Jan 1:04 PM
     Reach: 1,248  |  Likes: 87  |  Comments: 12
  ✅ LinkedIn  · Posted 16 Jan 1:06 PM
     Views: 432   |  Reactions: 34
```
Data: GET /cp/hired-agents/{id}/deliverables → `deliverable.publish_receipt` JSONB per platform

**UI Compliance rules for Content Creator:**
- Batch-by-theme UX is mandatory — customer approves a *theme batch*, not individual posts one by one
- Reject requires a free-text reason (min 10 chars) — this feeds processor feedback loop
- Post preview must render exact character count + hashtags visible (not truncated)
- Token expiry warning (≤ 7 days) shown inline on connection card, not buried in settings

---

## 14. PP — Partner Portal: Platform-IT Diagnostic Toolkit

> **Metaphor**: The PP user is the **service center technician**. They open the bonnet, plug in the diagnostic computer, and read actual engine codes — RPM curves, fault codes, sensor readings. They tune parameters, requeue failed jobs, rotate credentials, and push/pull agent type configurations. Everything the customer never sees, the PP user can see and control.

### 14.1 Design Philosophy

| Technician sees | What maps to it |
|---|---|
| Diagnostic sensor readings | Construct health: Pump latency, Processor error rate, Publisher receipt rate |
| Electronic fault codes | DLQ entries: failed execution details, hook stage that failed |
| Live parameter dial | `ConstraintPolicy` live-tune: approval_mode, max_tasks |
| Engine timing display | `Scheduler` panel: cron expression, lag, next_run_at |
| Battery/ECU module view | `Connector` panel: credential status, expiry timestamp, secret_ref |
| Service log book | Hook trace: last N lifecycle events with timestamp + result |
| Parts catalogue | `AgentSpec` registry: agent type definitions, construct bindings |
| Fleet management screen | Ops hired agents: all hires across all customers |

**PP must expose**: Raw cron expressions, secret_refs (masked last 4), processor backend names, LLM call counts, cost-per-run in INR, DLQ entries, hook stage trace, OPA role assignments.

### 14.2 Construct Visibility Matrix in PP

| Construct | Panel Name | Key Parameters Shown | Tunable |
|---|---|---|---|
| `Scheduler` | **Scheduler Health Panel** | `cron_expression`, `next_run_at`, `last_run_at`, `lag_seconds`, `dlq_depth`, `pause_state` | pause / resume |
| `BasePump` | **Data Ingestion Panel** | `source_type`, `last_fetch_at`, `fetch_latency_ms`, `records_pulled`, `error_count` | — |
| `BaseProcessor` | **Execution Panel** | `backend_type`, `calls_today`, `cost_today_inr`, `avg_latency_ms`, `error_rate`, `last_error` | `backend_type` override flag |
| `Connector` | **Credentials Panel** | `platform`, `status`, `last_verified_at`, `expiry_at`, `secret_ref` (masked) | trigger re-verify |
| `Publisher` | **Output Panel** | `adapter_type`, `receipts_today`, `failed_count`, `last_publish_at`, `receipt_rate_pct` | requeue failed |
| `ConstraintPolicy` | **Policy Panel** | `max_tasks`, `used_tasks`, `max_trade_value`, `approval_mode` toggle, `trial_mode` | `approval_mode`, `max_tasks` |
| `LifecycleHooks` | **Hook Trace Log** | last 20 hook events: `stage`, `timestamp`, `result`, `hook_class` | — |

### 14.3 PP Route Architecture and RBAC

PP BackEnd enforces 7-role RBAC via OPA. Each route has a minimum required role.

```
PP BackEnd
    │
    ├── RBAC via OPA (rbac.py)
    │   Roles:  admin > customer_admin > developer > manager > analyst > support > viewer
    │   Checked on every non-public route
    │
    ├── Construct diagnostic routes (new — see §14.4)
    │   Required: admin, developer
    │
    ├── Ops read routes (existing)
    │   Required: manager, analyst, support, admin
    │
    └── Agent type management (existing)
        Required: admin
```

| Resource | Minimum Role | Route |
|---|---|---|
| Agent type publish/unpublish | `admin` | `PUT /pp/agent-types/{id}` |
| Agent setup upsert | `admin`, `developer` | `PUT /pp/agent-setups` |
| Mint approval token | `admin`, `developer` | `POST /pp/approvals` |
| Metering debug | `admin`, `developer` | `POST /pp/metering-debug/envelope` |
| Scheduler diagnostics (proposed) | `admin`, `developer` | `GET /pp/ops/hired-agents/{id}/scheduler-diagnostics` |
| Construct health (proposed) | `admin`, `developer` | `GET /pp/ops/hired-agents/{id}/construct-health` |
| DLQ console (proposed) | `admin`, `developer` | `GET /pp/ops/dlq` |
| DLQ requeue (proposed) | `admin` | `POST /pp/ops/dlq/{id}/requeue` |
| Hook trace (proposed) | `admin`, `developer` | `GET /pp/ops/hired-agents/{id}/hook-trace` |
| Constraint policy tune (proposed) | `admin` | `PATCH /pp/agent-setups/{id}/constraint-policy` |
| View all hired agents | `manager`, `analyst`, `support`, `admin` | `GET /pp/ops/hired-agents` |
| View deliverables / goals | `manager`, `analyst`, `admin` | `GET /pp/ops/hired-agents/{id}/deliverables` |

### 14.4 PP Route Surface (Current + Recommended)

#### Agent Configuration
| Method | Route | Purpose |
|---|---|---|
| `PUT` | `/pp/agent-setups` | Define/update agent type's construct bindings + ConstraintPolicy defaults |
| `GET` | `/pp/agent-setups` | List all configured agent types with current binding snapshots |

#### Ops Monitoring (existing)
| Method | Route | Purpose |
|---|---|---|
| `GET` | `/pp/ops/hired-agents` | All active hires — health indicator per hire |
| `GET` | `/pp/ops/hired-agents/{id}` | Single hire deep-dive |
| `GET` | `/pp/ops/hired-agents/{id}/deliverables` | Deliverable history |
| `GET` | `/pp/ops/hired-agents/{id}/goals` | Goal schedule status |

#### Approval Workflow (existing)
| Method | Route | Purpose |
|---|---|---|
| `POST` | `/pp/approvals` | Mint approval token (used as governor_role gate) |
| `GET` | `/pp/approvals` | All pending approvals |
| `GET` | `/pp/approvals/{id}` | Single approval detail |

#### Agent Type Management (existing)
| Method | Route | Purpose |
|---|---|---|
| `GET` | `/pp/agent-types` | All registered agent types |
| `GET` | `/pp/agent-types/{id}` | Single agent type |
| `PUT` | `/pp/agent-types/{id}` | Publish / unpublish agent type |
| `POST` | `/pp/metering-debug/envelope` | Inject debug metering event |

#### ⚠️ Missing PP Routes — Critical for Service Center Vision

| Method | Proposed Route | RBAC | Purpose | Priority |
|---|---|---|---|---|
| `GET` | `/pp/ops/hired-agents/{id}/scheduler-diagnostics` | developer | Full scheduler state: cron, next_run, lag, dlq_depth, pause_state for a specific hire | **P0** |
| `GET` | `/pp/ops/hired-agents/{id}/construct-health` | developer | Per-construct snapshot — all 6 constructs in one response | **P0** |
| `POST` | `/pp/ops/hired-agents/{id}/scheduler/pause` | admin | Ops-side pause (overrides customer goal state) | **P0** |
| `POST` | `/pp/ops/hired-agents/{id}/scheduler/resume` | admin | Resume after ops pause | **P0** |
| `GET` | `/pp/ops/dlq` | developer | All DLQ entries across all hires, sortable by age / agent type | **P1** |
| `POST` | `/pp/ops/dlq/{entry_id}/requeue` | admin | Requeue a failed execution from DLQ | **P1** |
| `GET` | `/pp/ops/hired-agents/{id}/hook-trace` | developer | Last N hook events: stage, timestamp, hook_class, result | **P1** |
| `GET` | `/pp/agent-setups/{agent_type_id}/construct-spec` | developer | Read current ConstructBindings for an agent type | **P1** |
| `PATCH` | `/pp/agent-setups/{agent_type_id}/constraint-policy` | admin | Live-tune: toggle approval_mode, update max_tasks — no redeploy | **P1** |
| `GET` | `/pp/ops/hired-agents/{id}/cost-breakdown` | manager | LLM call count + cost-per-run by date — ops cost control | **P2** |

### 14.5 Share Trader PP Diagnostic View

**PP tech: Vikram (developer role), debugging customer C-001's Share Trader hire `HA-7812`**

```
GET /pp/ops/hired-agents/HA-7812/construct-health
─────────────────────────────────────────────────────
SCHEDULER PANEL
  cron_expression:     "0 9 * * Mon-Fri"    ← market-open daily
  next_run_at:         2024-01-16 09:00 IST
  last_run_at:         2024-01-15 09:02 IST
  lag_seconds:         2                    ← healthy (alert: > 30s)
  dlq_depth:           0                    ← clean
  pause_state:         RUNNING              ← [Pause]

GET /pp/ops/hired-agents/HA-7812/scheduler-diagnostics
─────────────────────────────────────────────────────
PUMP PANEL  (TradingPump)
  source_type:         delta_exchange
  last_fetch_at:       2024-01-15 09:01:58 IST
  fetch_latency_ms:    340                  ← healthy (alert: > 2000ms)
  records_pulled:      47 positions + ticks
  error_count:         0

PROCESSOR PANEL  (TradingProcessor)
  backend_type:        gpt-4o              ← [flag to override]
  calls_today:         3
  cost_today_inr:      ₹2.40
  avg_latency_ms:      1,240
  error_rate:          0.0%
  last_error:          none

CONNECTOR PANEL  (DeltaConnector)
  platform:            delta_exchange
  status:              VALID               ← [Trigger re-verify]
  last_verified_at:    2024-01-15 08:59 IST
  expiry_at:           n/a (API key, no expiry)
  secret_ref:          sm://waooaw-oauth/delta-api-key-****-c001-prod

PUBLISHER PANEL  (DirectTradePublisher)
  adapter_type:        delta_exchange_order
  receipts_today:      2
  failed_count:        0
  last_publish_at:     2024-01-15 11:23 IST
  receipt_rate_pct:    100%

POLICY PANEL
  max_trades_per_day:     5
  trades_today:           2 / 5
  max_position_size_inr:  ₹50,000
  approval_mode:          MANUAL          ← [Toggle → AUTO]
  trial_mode:             false           ← (converted to paid)
  tasks_used_today:       2

HOOK TRACE (last 5 events)
  09:02:01  PRE_PUMP            TradingPump                 OK
  09:02:01  PRE_PROCESSOR       ConstraintPolicyHook        OK
  09:02:03  PRE_TOOL_USE        AuditHook                   OK
  09:02:05  POST_PROCESSOR      ApprovalRequiredHook        HALTED → approval pending
  11:23:44  POST_PUBLISH        AuditHook                   OK
```

**Vikram's diagnostic actions:**
1. DLQ depth = 0 → no stuck executions
2. Processor cost ₹2.40/day → within budget
3. approval_mode = MANUAL → correct for customer's preference
4. `POST_PROCESSOR` HALTED on ApprovalRequiredHook → normal — customer approved at 11:23
5. No action needed; system healthy

### 14.6 Content Creator PP Diagnostic View

**PP tech: Aisha (admin role), responding to customer report: "My posts stopped going out"**

```
GET /pp/ops/hired-agents/HA-9034/construct-health
─────────────────────────────────────────────────────
SCHEDULER PANEL
  cron_expression:     "0 8,13,18 * * *"   ← 3 × daily
  next_run_at:         2024-01-16 08:00 IST
  last_run_at:         2024-01-15 18:00 IST
  lag_seconds:         0                   ← healthy
  dlq_depth:           3                   ← ⚠️ 3 FAILED EXECUTIONS

PUMP PANEL  (GoalConfigPump)
  source_type:         goal_config_db
  last_fetch_at:       2024-01-15 18:00:01 IST
  fetch_latency_ms:    12                  ← healthy
  records_pulled:      1 (CampaignBrief v4)

PROCESSOR PANEL  (ContentCreatorProcessor)
  backend_type:        gpt-4o-mini
  calls_today:         6
  cost_today_inr:      ₹0.45
  avg_latency_ms:      820
  error_rate:          0.0%

CONNECTOR PANEL
  instagram:    VALID      last_verified: 2024-01-15 07:58 IST
  linkedin:     EXPIRED    expiry_at: 2024-01-14 00:00 IST  ← ⚠️ ROOT CAUSE
                           secret_ref: sm://waooaw-oauth/li-token-****-9034-prod

PUBLISHER PANEL  (SocialMediaPublisher)
  adapter_type:        instagram + linkedin
  receipts_today:      6  (3 Instagram OK, 3 LinkedIn FAILED)
  failed_count:        3
  last_publish_at:     2024-01-15 13:04 IST  (Instagram only)
  receipt_rate_pct:    50%                   ← ⚠️

HOOK TRACE (last 5 events)
  18:00:05  PRE_PUBLISH   LinkedInPublisher   FAILED → token_expired
  13:01:02  PRE_PUBLISH   LinkedInPublisher   FAILED → token_expired
  08:00:04  PRE_PUBLISH   LinkedInPublisher   FAILED → token_expired
  18:00:05  POST_PUBLISH  InstagramPublisher  OK
  13:01:02  POST_PUBLISH  InstagramPublisher  OK
```

**Aisha's diagnostic actions:**
1. DLQ depth = 3 → 3 LinkedIn publish failures → matches hook trace: `token_expired`
2. Root cause: LinkedIn OAuth token expired 2024-01-14 → silence because G11 (CredentialExpiringSoon event) is still open
3. Action: notify customer to reconnect LinkedIn via `/cp/hired-agents/9034/platform-connections`
4. After customer reconnects: `POST /pp/ops/dlq/{entry_id}/requeue` × 3 to replay missed posts
5. Recommend: fast-track G11 — add `CredentialExpiringSoon` check in `PRE_PUMP` hook at T-7 days

---

## 15. Key DB Tables Quick Reference

| Table | Owned by | Purpose |
|---|---|---|
| `agent_type_entity` | Agent (mould reference) | Catalogue of agent types — maps to in-memory AgentSpec |
| `hired_agents` | Agent | One row per customer-agent hire |
| `agent_skills` | Agent / Pump | Skills attached to a hire + `goal_config` JSONB |
| `platform_connections` | Connector | Credential references per hire (secret_ref only) |
| `scheduled_goal_runs` | Scheduler | Cadence definitions |
| `scheduler_state` | Scheduler | Singleton pause/resume state |
| `scheduler_dlq` | Scheduler | Failed executions pending review |
| `goal_instances` | Scheduler | One row per fired execution |
| `campaigns` | ContentCreatorProcessor | Campaign created for content agents |
| `daily_theme_items` | ContentCreatorProcessor | One row per campaign day |
| `content_posts` | ContentCreatorProcessor / Publisher | One row per post; `publish_receipt` JSONB |
| `deliverables` | Publisher | Final deliverable row — applies to ALL agent types |

---

## 16. Suggested Improvements — Drastic Changes Needing User Sign-Off

These are changes that materially alter the UX or architecture. None should be implemented without explicit product/user confirmation.

### 16.1 WebSocket real-time approval queue (CP — High impact)

| Dimension | Detail |
|---|---|
| **Root cause** | CP currently polls `GET /cp/marketing/draft-batches` — customer must pull-to-refresh |
| **Impact** | High-frequency reviewers (3 posts/day × multiple hires) miss new drafts; approval latency adds scheduling delay |
| **Proposed fix** | Add WebSocket channel on Plant Gateway → push `DRAFT_READY` event to connected mobile client on `POST_PROCESSOR` hook → mobile updates approval queue in real-time without polling |
| **What needs sign-off** | WebSocket layer in Plant Gateway; mobile `useWebSocket` hook; impacts auth flow |

### 16.2 Swipe-to-approve UX for trading (CP mobile — Medium impact)

| Dimension | Detail |
|---|---|
| **Root cause** | Approval modal uses two tap targets (Approve, Reject) — high-stakes action needs a deliberate gesture |
| **Impact** | Accidental approvals on mobile are possible; friction is too low for a financial action |
| **Proposed fix** | Swipe-right = approve, swipe-left = reject. Requires hold + swipe beyond 70% threshold to prevent accidental trigger. Standard mobile gesture for financial apps (Robinhood, Zerodha). No backend change needed. |
| **What needs sign-off** | TrialDashboardScreen redesign; HireConfirmationScreen gesture; UX test with users |

### 16.3 Aggregate construct health badge on agent card (CP — Medium impact)

| Dimension | Detail |
|---|---|
| **Root cause** | MyAgentsScreen agent card shows only name + status emoji — no health signal |
| **Impact** | Customer cannot see connector expiry or DLQ issues without drilling in |
| **Proposed fix** | Add single health dot (🟢/🟡/🔴) to each agent card, driven by `GET /cp/hired-agents/{id}/scheduler-summary` (proposed new route). Score = worst of: DLQ depth > 0, lag > 30s, connector expiry ≤ 7 days. |
| **What needs sign-off** | New CP route; badge component on AgentCard.tsx; definition of health scoring function |

### 16.4 Live DLQ console in PP (PP — High impact for ops)

| Dimension | Detail |
|---|---|
| **Root cause** | No DLQ visibility in PP today — ops must query DB directly to find failed executions |
| **Impact** | G10 (approval_mode=auto posts sit forever) and G11 (silent token expiry) are invisible without DB access |
| **Proposed fix** | `GET /pp/ops/dlq` — paginated list of all `scheduler_dlq` entries with group-by agent type + requeue action `POST /pp/ops/dlq/{id}/requeue`. One sprint, ~45min backend + minimal table UI. |
| **What needs sign-off** | New PP routes (2); PP UI table component; ops runbook update |

### 16.5 ConstraintPolicy live-tune toggle (PP — High impact for ops)

| Dimension | Detail |
|---|---|
| **Root cause** | `approval_mode` is set at hire time in `agent_skills.goal_config` JSONB — ops cannot change it without a customer-facing re-hire or DB patch |
| **Impact** | Content agents whose customers never come back to review are stuck in `pending_review` with no posts going out (G10 open) |
| **Proposed fix** | `PATCH /pp/agent-setups/{agent_type_id}/constraint-policy` — ops toggles `approval_mode` from MANUAL → AUTO for a specific hire. Also enables ops to lower `max_tasks_per_day` during cost incident. |
| **What needs sign-off** | New PP route; audit log entry mandatory; `admin` role only; customer notification on mode change |

### 16.6 OAuth token expiry countdown in CP (CP — Medium impact)

| Dimension | Detail |
|---|---|
| **Root cause** | `GET /cp/hired-agents/{id}/platform-connections` does not return `days_until_expiry` — the `platform_connections` table stores `secret_ref` only, not expiry |
| **Impact** | LinkedIn token expires silently (G11 open) — customer has no warning; posts fail day-of with no notification |
| **Proposed fix** | (a) Store `expires_at` in `platform_connections` at OAuth time; (b) Return `days_until_expiry` from CP route; (c) Mobile shows amber warning ≤ 7 days, red ≤ 1 day on connector card. Resolves G11. |
| **What needs sign-off** | DB migration (add `expires_at` column), CP service layer change, mobile connector card update |

### 16.7 Approval-mode per-hire override via CP (CP — Low impact, high value)

| Dimension | Detail |
|---|---|
| **Root cause** | Customer can set approval_mode once in HireWizard but cannot flip it for an active hire without re-hiring |
| **Impact** | Customers switch between "I'm busy this week — just post" (AUTO) and "I want to review" (MANUAL) frequently |
| **Proposed fix** | Expose toggle in `PATCH /cp/hired-agents/{id}/skills/{skill_id}/goal-config` — `approval_mode` field. CP BackEnd writes to `agent_skills.goal_config.approval_mode`. GoalSchedulerService reads this at next trigger. |
| **What needs sign-off** | CP route change (already exists, just add field); mobile settings gear on agent card |
