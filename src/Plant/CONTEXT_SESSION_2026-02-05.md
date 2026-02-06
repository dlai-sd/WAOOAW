# Plant — Context Session Snapshot
**Date**: 2026-02-05
**Scope**: Plant hardening + PP portal adoption planning
**Status**: ✅ Plant execution checklist complete; ✅ PP adoption epics/stories added to implementation doc

---

## 1) What we completed today (high signal)

### A) Final checklist item: Trusted Metering Envelope (AI Explorer → Plant)
**Goal**: prevent spoofing of metering fields (tokens/model/cost) when budget enforcement is enabled.

**What’s implemented**
- A signed, env-gated “trusted metering envelope” verifier in Plant backend.
- Enforcement: when plan budgets are configured AND `METERING_ENVELOPE_SECRET` is set, Plant rejects requests unless the trusted envelope is present + valid.
- Envelope values override JSON body metering fields for enforcement and usage event recording (so the body can’t spoof).

**Where**
- Backend verification + signing helpers: `src/Plant/BackEnd/services/metering.py`
- Enforcement wired into:
  - `src/Plant/BackEnd/api/v1/agent_mold.py` (skill execution)
  - `src/Plant/BackEnd/api/v1/reference_agents.py` (reference agent run)
- Unit tests:
  - `src/Plant/BackEnd/tests/unit/test_trusted_metering_envelope.py`

**Runtime contract (headers)**
- Required headers:
  - `X-Metering-Timestamp` (unix seconds)
  - `X-Metering-Tokens-In` (int)
  - `X-Metering-Tokens-Out` (int)
  - `X-Metering-Model` (string; may be empty)
  - `X-Metering-Cache-Hit` (`0/1`, optional)
  - `X-Metering-Cost-USD` (float, optional)
  - `X-Metering-Signature` (base64url HMAC-SHA256)

**Signature canonical string**
`ts|correlation_id|tokens_in|tokens_out|model|cache_hit|cost_usd`
- `cost_usd` canonicalized to 6 decimal places.

**Enforcement toggle / TTL**
- Enabled when env var `METERING_ENVELOPE_SECRET` is set.
- Timestamp freshness enforced by `METERING_ENVELOPE_TTL_SECONDS` (default 300s).

**Denial semantics** (all return 429 Usage Limit Denied)
- `metering_envelope_required` (missing envelope)
- `metering_envelope_invalid` (bad format/signature)
- `metering_envelope_expired` (stale timestamp)

---

### B) Updated the execution checklist
- Marked the final row (trusted metering envelope / AI Explorer integration) ✅ in:
  - `src/Plant/Docs/agents_implementation.md`

---

### C) PP portal adoption planning: epics/stories + exact API details
**Goal**: make the newly built Plant functionality visible and usable in PP (Platform Portal).

**What was added**
- A new end-section “PP Portal Adoption (Make Plant Visible in PP)” with:
  - Epics/stories
  - PP landing spots (exact PP FE/BE files)
  - Plant endpoints used
  - Definitions of Done
  - A “Plant API details” sub-section with copy/paste endpoint contracts: headers, params, response shape, error reasons.

**Where**
- `src/Plant/Docs/agents_implementation.md`

---

## 2) Key current architecture (relevant integration points)

### Plant backend endpoints used by PP adoption plan
- Reference agents:
  - `GET /api/v1/reference-agents`
  - `POST /api/v1/reference-agents/{agent_id}/run`
- Usage events:
  - `GET /api/v1/usage-events`
  - `GET /api/v1/usage-events/aggregate`
- Policy denial audit:
  - `GET /api/v1/audit/policy-denials`
- AgentSpec schema:
  - `GET /api/v1/agent-mold/schema/agent-spec`
- Skill execution (Agent Mold example):
  - `POST /api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute`

### PP portal current state (as of repo inspection)
- PP backend is a thin proxy to Plant Gateway:
  - `src/PP/BackEnd/main_proxy.py` proxies `/api/{path}` → `PLANT_GATEWAY_URL/api/{path}`.
  - PP mounts its own admin endpoints under `/api/pp/*`.
- PP frontend uses a central fetch wrapper:
  - `src/PP/FrontEnd/src/services/gatewayApiClient.ts`
- Existing PP pages are partly placeholder/static:
  - `GovernorConsole.tsx` is currently static.
  - `CustomerManagement.tsx` is currently static.

---

## 3) Validation / Testing performed (docker-first)
- Added new unit tests for trusted envelope:
  - `src/Plant/BackEnd/tests/unit/test_trusted_metering_envelope.py` (3 tests)
- Tests were executed inside Docker containers.
- Note: running a *single* test file under Plant’s pytest config can fail CI locally due to subproject-wide coverage thresholds; tests were also re-run with `--cov-fail-under=0` to validate behavior.

---

## 4) Known follow-ups (optional / operational)
These are not required for the Plant checklist anymore, but improve end-to-end security/UX:

1) **PP proxy header hygiene**
- Strip inbound `X-Metering-*` headers in `src/PP/BackEnd/main_proxy.py` to prevent browsers from injecting spoofed envelope headers.

2) **Plant Gateway envelope injection**
- If AI Explorer calls Plant Gateway, gateway should remove any user-supplied `X-Metering-*` and only forward trusted envelope headers from a trusted caller.

3) **Implement PP adoption epics in code**
- Highest leverage first slice:
  - Reference Agents list + run
  - Usage events list for a customer
  - Policy denials list/drilldown

---

## 5) Source of truth docs
- Execution checklist + PP adoption plan: `src/Plant/Docs/agents_implementation.md`
- Backend trusted metering implementation: `src/Plant/BackEnd/services/metering.py`

