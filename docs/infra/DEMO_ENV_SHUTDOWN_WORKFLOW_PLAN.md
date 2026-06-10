# Demo Environment Cost Reduction — Workflow Batch Plan (Understanding + Approach)

Date: 2026-06-10  
Status: Planning only (no implementation in this step)

## 1) Task understanding

The ask is to design a workflow batch that can stop and start demo runtime assets so billing drops as low as possible, while staying aligned with the repo's CI/CD model and Terraform ownership.

Requested runtime scope for this batch:
- CP asset
- PP asset
- API Gateway asset (Plant Gateway)

Requested constraint for this batch:
- No Google Cloud configuration mutation (no Terraform state changes, no infra create/destroy, no LB/DNS/Cloud SQL topology changes).

This plan is intentionally implementation-ready but code-free. It defines how we should implement later, what each mode does, and the guardrails to avoid accidental outages in UAT/prod.

## 2) Current platform and CI/CD understanding

### 2.1 Core deployment control plane

Primary active deployment workflows:
- .github/workflows/waooaw-deploy.yml: Builds/pushes images and applies per-environment app stacks (`plant`, `cp`, `pp`).
- .github/workflows/waooaw-foundation-deploy.yml: Applies shared LB/foundation stack.
- .github/workflows/waooaw-drift.yml: Plans drift for foundation + CP and opens issues.

Other workflows reviewed are CI/regression/security/mobile/automation and do not directly own environment lifecycle teardown.

### 2.2 Terraform ownership map for runtime infra

- cloud/terraform/stacks/plant: Plant backend, gateway, OPA, Cloud SQL, VPC connector, NEGs.
- cloud/terraform/stacks/cp: CP frontend/backend, VPC connector, NEGs.
- cloud/terraform/stacks/pp: PP frontend/backend, VPC connector, NEGs.
- cloud/terraform/stacks/foundation: Shared global LB, URL maps, certs, forwarding rules, backend services reading remote state from app stacks.

### 2.3 Architectural constraints from master docs

- One-image promotion must be preserved (demo -> uat -> prod); no env values baked into images.
- Runtime config only via Cloud Run env vars and Secret Manager references.
- CP/PP are thin proxy layers; Plant holds runtime core.
- Existing deploy path is Terraform-first; ad-hoc gcloud delete should be emergency-only.

## 3) Cost-driver findings for demo

## Root cause analysis

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| Plant demo min_instances = 1 in cloud/terraform/stacks/plant/environments/demo.tfvars | Always-on Cloud Run charges even with no traffic | Add a hibernate profile setting min_instances=0 for all demo Cloud Run services |
| Each stack creates VPC access connectors with min_instances=2 | Persistent connector baseline cost in demo | In hibernate mode: reduce connector min/max to minimum valid values; in deep-sleep mode: destroy app stacks |
| Plant stack provisions Cloud SQL instance | Baseline DB compute/storage/backup cost remains even at low traffic | Outside stop/start scope if config mutation is disallowed; document as residual cost |
| Foundation shared LB resources kept active | Fixed LB/cert/forwarding/backends costs continue | Optional include in destroy mode: disable demo routing in foundation or keep shared LB if needed for quick resume |
| Secret versions/images/log retention naturally accumulate | Storage/ops costs drift upward over time | Add optional housekeeping steps (artifact retention, log retention tuning) with explicit safeguards |

## 4) Why current cost may be around INR 15,000/month

Based on current terraform settings and stack architecture, likely contributors are:
- Always-on Plant Cloud Run baseline (min instance > 0).
- VPC connectors running in multiple stacks.
- Cloud SQL instance (even small tier) plus backups/storage.
- Shared LB and backend services/certs.
- Possible extra artifacts/logging/storage over time.

A stop/start-only approach for CP, PP, and API Gateway will reduce a major portion of runtime cost, but it will not reach absolute minimum if DB/LB/connectors must remain unchanged.

## 5) Proposed workflow batch (implementation design)

### 5.1 Workflow set

Planned new workflows (manual only):
1. .github/workflows/waooaw-demo-runtime-batch.yml (single batch with action=stop|start)
2. .github/workflows/waooaw-demo-cost-report.yml

### 5.2 Runtime actions (single batch)

Action: stop
- Stop only demo runtime services for CP, PP, and API Gateway.
- Do not alter Terraform state, tfvars, or provisioned infrastructure.

Action: start
- Start the same demo runtime services for CP, PP, and API Gateway.
- Restore service-level runtime to pre-defined defaults without infra topology changes.

Implementation note:
- This design intentionally excludes destroy-mode operations to honor the no-config-change requirement.

## 6) Resource targeting matrix

| Resource class | Stop action | Start action | Notes |
|---|---|---|---|
| CP runtime services (frontend/backend) | Stop | Start | In scope |
| PP runtime services (frontend/backend) | Stop | Start | In scope |
| API Gateway runtime service | Stop | Start | In scope |
| Plant backend/OPA | Optional linked handling | Optional linked handling | Include only if required dependency for Gateway start health |
| VPC connectors | No change | No change | Out of scope by constraint |
| Cloud SQL demo instance | No change | No change | Out of scope by constraint |
| Foundation LB/routes/DNS/certs | No change | No change | Out of scope by constraint |
| Static global IP | No change | No change | Out of scope by constraint |

## 7) Safety and guardrails for implementation

Mandatory controls for later implementation:
- workflow_dispatch only, no schedule trigger.
- Environment hard-locked to demo; refuse uat/prod values.
- Single action input: stop or start.
- Two-step confirmation input for stop action.
- No terraform apply/destroy in this batch.
- Concurrency group lock for demo lifecycle workflows.
- Post-action verification using gcloud inventory snapshots.
- Rollback path documented in the same workflow summary.

## 8) Recommended implementation order

1. Add non-destructive cost report workflow first (inventory + current estimated contributors).
2. Add one runtime batch workflow with input action=stop|start for CP, PP, and API Gateway.
3. Add strict no-config-mutation guard checks (no terraform, no foundation operations).
4. Add post-stop and post-start health/status verification for the same three assets.
5. Add optional report-only housekeeping suggestions (not mutation) for residual fixed-cost resources.

## 9) Risks and mitigations

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| Accidental destroy outside demo | Severe outage risk | Hard-code demo checks and fail closed on any other env |
| Any unintended foundation/config change | Multi-env incident | Exclude all foundation and terraform mutation logic from this batch |
| Cloud SQL deletion loses demo data | Demo data loss | Provide keep_data boolean and default to keep in first release |
| Drift workflow raising expected alerts during suspend | Noise/confusion | Teach drift workflow to skip/annotate suspended mode |
| Resume complexity after max-savings mode | Longer recovery time | Provide one-click resume workflow that reapplies stacks in correct order |

## 10) Implementation-ready acceptance criteria

The later implementation will be considered complete when:
- Demo runtime can be stopped and started via a single workflow batch only.
- The stop/start scope includes CP, PP, and API Gateway on demo.
- No Terraform apply/destroy or other GCP configuration mutation occurs in this batch.
- Workflows provide clear summaries of what changed and expected billing effect.
- No uat/prod resource can be targeted by mistake.

## 11) Practical recommendation

Start with a single stop/start runtime batch for CP, PP, and API Gateway immediately, because it meets your safety constraint of no cloud config changes while still lowering runtime spend.

This gives controlled savings with fast recovery, and keeps deeper cost-optimization options as separate future work if you later allow infrastructure mutation.
