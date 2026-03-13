# WAOOAW Agents Session Handoff

Date: 2026-03-13
Repo: WAOOAW
Current branch at handoff: feat/plant-catalog-1-it1-e1

## Runtime Authority Update

- The executable Plant runtime source of truth is [docs/PP/AGENT-CONSTRUCT-DESIGN.md](docs/PP/AGENT-CONSTRUCT-DESIGN.md).
- Repo-wide documentation alignment is now complete for active drift-risk surfaces: runtime-facing docs should use Plant construct vocabulary such as `AgentSpec`, `ConstructBindings`, `ConstraintPolicy`, `LifecycleHooks`, `HiredAgent`, `Skill`, `SkillRun`, and `Deliverable`.
- Older terms such as `Agent DNA`, `Base Agent Anatomy`, `ConfigureMe`, `OperateMe`, `EEPROM`, `organs`, and filesystem-memory initialization may still appear in historical or conceptual files, but they should no longer be read as the literal current runtime contract.

## Documentation Alignment Outcome

- The top-level repo docs, `main/` foundational docs, active governance charters, active templates, and Plant README surfaces were updated to defer runtime semantics to [docs/PP/AGENT-CONSTRUCT-DESIGN.md](docs/PP/AGENT-CONSTRUCT-DESIGN.md).
- Historical amendment, precedent, diagram, and session files now carry explicit notes when they preserve legacy vocabulary for constitutional or archival reasons.
- The intended end state is not zero mentions of older words; it is zero unmarked surfaces that teach legacy runtime semantics as current implementation truth.

## CP Auth Outcome

- CP sign-in and sign-up were redesigned with a startup-style split layout and clearer OTP flow hierarchy.
- The redesign was isolated into a clean PR and opened as PR #925: feat(cp-auth): redesign startup sign-in and sign-up.
- Validation completed on the clean auth branch with:
  - focused CP auth/frontend tests: 32 passed
  - CP frontend build: passed

## Landing Page Outcome

- A separate experimental landing-page worktree and branch were created for exploration.
- The user rejected the landing-page redesign direction.
- Final decision: do not carry the landing experiment forward; keep the existing demo landing page.

## Digital Marketing Agent Direction For Next Session

- Next focus is the Digital Marketing Agent setup flow, starting in PP.
- PP should define the agent and configure skills cleanly so CP feels natural for the customer.
- The likely initial DMA skill grouping is:
  - Theme Discovery
  - Video Creator
  - YouTube Publisher

## YouTube Integration Findings

- WAOOAW should not assume the CP login identity and the YouTube identity are the same.
- Correct model: the customer may sign into CP with a business email, then connect a different Google account for YouTube channel access.
- CP identity proves who the customer is in WAOOAW.
- YouTube OAuth identity proves which external channel the hired agent may act on.

## Recommended Customer Flow

1. Customer hires the Digital Marketing Agent.
2. Customer opens the CP agent configuration wizard.
3. Customer selects the YouTube creation/publishing capability.
4. CP prompts the customer to connect YouTube via OAuth.
5. After OAuth, CP fetches channel metadata and asks the customer to confirm the channel identity.
6. Customer completes Theme Discovery, cadence, and content settings.
7. Agent creates drafts.
8. Customer reviews exact content.
9. Publish remains approval-gated and uses the connected YouTube credential.

## Important Technical Conclusions

- YouTube should use OAuth access_token and refresh_token, not a raw API-key setup flow.
- CP already has the right high-level pattern for platform connections:
  - store raw credentials in Secret Manager
  - persist only an opaque secret_ref for Plant runtime use
- Plant already contains YouTube-specific runtime code and credential resolution plumbing.
- Current gap: YouTube publishing is not fully wired into the real destination adapter path everywhere; some publisher-engine paths still treat youtube as simulated.

## Existing Relevant Files

- CP Secret Manager write path:
  - src/CP/BackEnd/api/cp_skills.py
  - src/CP/BackEnd/services/secret_manager.py
- CP internal credential resolution path:
  - src/CP/BackEnd/api/internal_plant_credential_resolver.py
  - src/CP/BackEnd/services/platform_credentials.py
- Plant credential resolution and YouTube integration:
  - src/Plant/BackEnd/services/social_credential_resolver.py
  - src/Plant/BackEnd/integrations/social/youtube_client.py
  - src/Plant/BackEnd/agent_mold/skills/publisher_engine.py

## Cross-Platform Connector View

- YouTube: strong fit for OAuth-based external account connection.
- Facebook and Instagram: similar OAuth/business-asset pattern, not customer app-secret harvesting.
- LinkedIn: OAuth-based identity and organization/page permission pattern.
- X: possible, but commercial/API stability is weaker than YouTube, Meta, and LinkedIn.
- WhatsApp: business onboarding flow is different and more operationally specific than a simple social connect flow.

## Product Rule To Preserve

- Never couple WAOOAW account login identity to external publishing identity.
- Always show the customer exactly which external channel/account/page/organization is connected before enabling publish.
- Approval-gated publishing and truthful runtime readiness must remain visible in both CP and PP.

## Agent Design Board Direction (2026-03-13)

- PP should be treated as a design board and release gate for hireable agent supply, even though Plant remains the canonical system of record.
- The near-term goal is not generic no-code agent creation. The near-term goal is to let a platform contributor make the Digital Marketing Agent hire ready with explicit platform-approved values.
- Plant should own lifecycle truth, versioning, and customer continuity. PP should help a human review and publish that truth. CP should only show agents that are explicitly approved for new hire.

## Base Agent Contract Ground Rule

- Every new WAOOAW agent should begin from a static Base Agent Contract presented in PP, not from a blank page and not from ad hoc raw JSON.
- This Base Agent Contract should be treated as a governed authoring skeleton, not as a single monolithic Python base class.
- The purpose is to reduce drift in structure, make required interfaces explicit, and let PP tell the user what is mandatory, optional, incomplete, or unsafe before Plant implementation starts.

### Base Agent Contract sections

| Section | Status | Why it is part of the base |
|---|---|---|
| Identity | Mandatory | Every agent needs a stable platform identity and a clear public purpose |
| Skill composition | Mandatory | The required capabilities must be explicit before authoring can continue |
| Customer configuration schema | Mandatory | CP setup cannot be hand-built per agent forever |
| Goal templates | Mandatory | The agent must declare what it is expected to do repeatedly |
| Construct bindings | Mandatory | Plant needs an explicit runtime wiring contract |
| Constraint policy | Mandatory | Approval mode, quotas, and guardrails are product decisions, not afterthoughts |
| Lifecycle and approval behavior | Mandatory | PP and CP must know how the agent behaves through trial, approval, pause, cancel, and retirement |
| Extensions | Optional | Agent-specific additions are allowed only after the base contract is satisfied |

### PP to Plant lifecycle rule

1. A platform user sketches a new agent in PP using the Base Agent Contract view.
2. PP validates completeness and highlights mandatory versus optional sections.
3. The design package moves into Plant for runtime build-out as `AgentSpec`, `AgentTypeDefinition`, and supporting code-defined components where needed.
4. Once runtime validation is complete, the candidate comes back to PP for review and approval.
5. Only after approval should Plant mark a catalog release as eligible for CP new hire.

### Why this rule matters

- Without a fixed base contract, each new agent risks inventing its own structure, lifecycle language, and approval assumptions.
- Without the PP-first authoring step, Plant becomes the accidental place where product shape is decided through implementation details.
- Without the PP return-for-approval step, CP risks exposing agents that are technically runnable but not operationally or commercially ready.

## Hire-Ready Digital Marketing Agent Contract

The Digital Marketing Agent should not appear in CP just because an `Agent` row exists. It should appear only after a platform contributor approves a hire-ready release.

### Minimum public fields required before CP can list the agent

| Field group | Required fields | Why it matters |
|---|---|---|
| Marketplace identity | `public_name`, `short_description`, `industry_name`, `job_role_label` | CP discovery and detail pages need clear customer-facing copy |
| Commercials | `monthly_price_inr`, `trial_days`, `allowed_durations` | CP card, detail, and booking flows already rely on pricing/trial metadata |
| Runtime identity | `agent_id`, `agent_type_id`, `internal_definition_version_id`, `external_catalog_version` | Hire flow must carry explicit type/version instead of relying on ID prefixes |
| Availability | `catalog_status`, `approved_for_new_hire`, `retired_from_catalog_at` | CP should show only approved supply and stop silently exposing every active agent |
| Setup expectations | `required_setup_steps`, `supported_channels`, `approval_mode` | Customer should know what must be configured before work starts |

### Recommended lifecycle states

- `draft`: being designed in PP, not visible in CP
- `design_review`: values are being reviewed by platform staff
- `approved_for_catalog`: ready for new hires in CP
- `live_on_cp`: currently visible in the ready-to-hire list
- `retired_from_catalog`: hidden from new hires, but historical runtime remains valid
- `servicing_only`: no new hires, but existing customer contracts continue normally

## Customer Continuity Rule

- Removing an agent from CP must mean catalog retirement, not runtime deletion.
- Existing hired customers must keep service if their contract is active.
- Every hired instance should keep the release snapshot it was sold against, including agent type and catalog version identifiers.
- Future releases may replace older public versions for new sales without rewriting existing customer runtime history.

## Current Implementation Baseline

### What Plant already supports

- Skill creation and certification through Genesis.
- Job role creation tied to required skills.
- Raw agent creation with `name`, `skill_id`, `job_role_id`, `industry_id`, and `governance_agent_id`.
- Versioned agent type definitions stored in Plant.
- Hired agent persistence already includes `agent_type_id` and `definition_version_id`.

### What PP already supports

- Agent type definition publishing/editing.
- A guided authoring surface for construct bindings, constraint policy, and hooks.
- Operator workflows for approvals, denials, and hired-agent diagnostics.

### What is still missing

- A first-class hire-readiness approval layer for agents.
- An explicit Plant catalog-release record that gates CP visibility.
- A PP design-board workflow that shows recommended values and approval status for a concrete agent release.
- CP lifecycle rendering that shows whether an agent is live, retired, or servicing-only.
- Generic component creation in PP. Today components are still code-defined and registry-backed.

## Creation vs Packaging Model

To keep design discussions clear, separate the layers:

| Layer | Current source of truth | Required fields now | Notes |
|---|---|---|---|
| Skill | Genesis / Plant | `skill_key`, `name`, `description`, `category`, `governance_agent_id` | Add `goal_schema` when CP must render dynamic configuration |
| Job Role | Genesis / Plant | `name`, `description`, `required_skills`, `seniority_level`, `governance_agent_id` | Defines the required skill chain |
| Agent Type Definition | PP authoring + Plant storage | `agent_type_id`, `version`, `required_skill_keys`, `config_schema`, `goal_templates`, `enforcement_defaults` | This is the best current design-board surface |
| Hireable Agent Release | PP review + Plant lifecycle | public identity, commercials, availability, explicit versions, setup requirements | This is the missing layer needed for safe CP listing |
| Component | Plant code registry | Python class + `register_component()` | Out of scope for the near-term PP design-board release workflow |

## Near-Term Product Direction

- Treat the Digital Marketing Agent as the first fully governed hire-ready release.
- Add a Plant-owned catalog lifecycle record and use PP to review/approve the release values.
- Make CP discovery read only the approved catalog-release surface.
- Show lifecycle and version truth to customers in discovery, hire setup, and hired-agent views.

## Immediate Product Framing For PP And CP

- PP Agent Management should evolve toward an internal design board and release gate, not a generic no-code runtime builder.
- Plant remains the system of record for lifecycle truth, versioning, hired-agent continuity, and construct execution.
- CP should only surface agents that have an explicit approved-for-catalog or live-on-CP release state, while preserving service for existing hired customers when a catalog release is retired.