# Tech Debt: Clean PR Branch Verification Gap

---

# Tech Debt: CP Activation Journey Is Split Across Handoff Screens Instead of One Inline Studio

## Story

The current customer activation path asks users to think in terms of multiple surfaces at once: the hire/payment completion flow, a separate `Hire Setup` route, and the `My Agents` workspace that already contains the operational context they actually need. That split created product confusion and led to UI clutter, duplicated status/setup summaries, and button behavior that felt broken because the user expectation was to keep working in place.

The deeper issue is structural, not cosmetic. CP still treats setup as a handoff from one page to another rather than as one stable studio shell where the customer can review progress, open a stage, edit identity or YouTube details inline, and continue without route churn.

## Why This Matters

- Customers should experience one activation workspace, not a chain of overlapping setup surfaces.
- Separate handoff and setup pages make state continuity, QA coverage, and support diagnosis harder.
- Repeated summary/setup chrome wastes the most valuable screen area on the exact journey where customers need focused input controls.

## Debt Item

**Name:** Unify CP customer activation into one inline studio

**Problem:** Customer setup is fragmented between `Hire Setup` and `My Agents`, with stage actions that imply inline editing but still rely on separate routes or redundant panels.

**Impact:** The activation journey feels inconsistent, users lose context during setup, and frontend fixes keep landing as local patches instead of solving the underlying surface-design problem.

**Root cause:** The product flow evolved incrementally around payment and review checkpoints, but the CP experience was never consolidated into a single Agent-Studio-style shell with explicit handoff boundaries.

## What Is Needed To Pay This Debt Down

1. Make `My Agents` the only customer setup studio after hire activation.
2. Reduce `Hire Setup` to a payment-success handoff surface with a clear CTA back into `My Agents`.
3. Replace duplicated summary/setup cards with a stable shell modeled on the PP Agent Studio layout: fixed navigation and descriptive chrome, scrollable working pane.
4. Keep identity and YouTube editing inline in the current studio pane so stage actions do not trigger route changes.
5. Add end-to-end coverage that proves portal entry, handoff, inline editing, and completion all work as one journey.

## Recommended Follow-up

Execute `CP-STUDIO-1` as the first consolidation pass, then reassess whether any remaining `Hire Setup` route behavior still serves a real customer need. If not, the next iteration should delete the leftover route-specific setup UI instead of maintaining two parallel activation surfaces.

## Story

We created PR 918 as a clean, main-based replay of fixes that were already implemented and tested on `feat/ui-ux-revamp`. That improved reviewability, but it also introduced a verification debt: several commits had to be replayed with conflict resolution, and the resulting clean branch was not fully revalidated in its own environment.

The risk is not a known functional break. The risk is that a replayed or conflict-resolved file could differ slightly from the already-tested source branch, while the clean branch still looks correct in code review.

When we tried to remove that risk, the temporary worktree did not have a usable local test toolchain. CP and PP frontend reruns fell back to `npx`, which tried to fetch a newer `vitest` incompatible with the available Node 18 runtime. Mobile reruns similarly fell back to on-demand package resolution instead of using a ready local Jest toolchain. That means the branch is based on previously validated work, but the branch-specific final verification pass is still missing.

## Why This Matters

- PR 918 contains manual cherry-pick conflict resolution in CP, PP, and docs files.
- Review confidence is lower without a clean-branch verification pass.
- The current gap is environmental and process-related, not clearly product-related.

## Debt Item

**Name:** Clean branch test-environment parity for reviewer PRs

**Problem:** We can replay tested commits onto a clean branch faster than we can prove that the clean branch has the same executable state.

**Impact:** Reviewers may merge a branch that is logically correct but not independently revalidated after conflict resolution.

**Root cause:** The temporary PR worktree was missing ready-to-use local frontend and mobile test dependencies, and the fallback package install path was incompatible with the available Node runtime.

## What Is Needed To Pay This Debt Down

1. Install or reuse the correct local dependencies in the clean PR worktree for:
   - `src/CP/FrontEnd`
   - `src/PP/FrontEnd`
   - `src/mobile`
2. Re-run the targeted CP, PP, and mobile test suites on the clean PR branch itself.
3. Re-check the files that required conflict resolution during cherry-pick replay.
4. Treat clean-branch verification as part of PR packaging whenever replay or conflict resolution is involved.

## Approximate Dependency Cost

- CP frontend test toolchain: `250-400 MB`
- PP frontend test toolchain: `250-400 MB`
- Mobile Jest/Expo toolchain: `800 MB-1.5 GB`
- Optional Playwright browser binaries for browser smoke coverage: `600 MB-1 GB`

Practical mitigation size for this debt is roughly `1.3-2.3 GB` without Playwright, or higher if browser binaries are also installed.

## Recommended Follow-up

The next time we cut a clean PR from a larger branch, we should budget dependency setup as part of the PR-prep workflow, not as an afterthought. That converts this from a review-confidence risk into a routine packaging step.

---

# Tech Debt: Alembic Migration Reliability Across Demo, UAT, and Prod

## Story

PP agent authoring drafts now persist correctly in Cloud SQL, but the migration path exposed a real release-engineering gap: Alembic migration runs against demo did not provide a trustworthy promotion signal for the latest revision. The work reached a state where the feature schema had to be verified and completed directly on Cloud SQL rather than being confidently advanced through the normal migration flow.

The debt is not about whether migrations exist. The debt is that we still need to prove that Alembic migration to demo, UAT, and prod migration works as a repeatable platform path, without manual DDL intervention or ambiguous success reporting.

## Why This Matters

- Schema-backed features are not production-ready if migration behavior is only trustworthy in local Docker.
- Demo is the required proving ground before promoting the same migration shape into UAT and prod.
- A migration runner that logs success but does not give a reliable persisted outcome creates release risk and rollback uncertainty.

## Debt Item

**Name:** Alembic promotion reliability for demo, UAT, and prod

**Problem:** The platform does not yet have a fully trusted, end-to-end verified Alembic promotion path for demo, UAT, and prod environments.

**Impact:** Future schema stories can appear complete in development while still carrying deployment risk at the environment-promotion layer.

**Root cause:** The migration execution path and environment-specific connectivity behavior are not yet sufficiently validated as one repeatable release process.

## What Is Needed To Pay This Debt Down

1. Reproduce the Alembic promotion flow against demo with full exit-code and post-migration state verification.
2. Verify the same migration runner path works unchanged for UAT and prod promotion rules.
3. Add a deployment smoke check that confirms both `alembic_version` and the expected schema objects after each environment migration.
4. Treat "alembic migration to demo/uat and prod migration works" as a release gate for schema-backed stories.

## Recommended Follow-up

Close this debt by hardening the migration runner and promotion checklist, then validating one full schema change through demo, UAT, and prod using the same release path. Until that is done, schema delivery still has platform-level operational risk even when feature code is correct.

---

# Tech Debt: Demo Cloud SQL Public-IP Drift Breaks Codespaces Proxy Path

## Story

The documented Codespaces path for live demo DB work depends on the Cloud SQL Auth Proxy connecting to `plant-sql-demo` over its public IP. In practice, the instance drifted back to `ipv4Enabled=false`, which left the proxy process apparently healthy but unable to open real SQL sessions; the first concrete signal was `/tmp/cloud-sql-proxy.log` reporting `instance does not have IP of type "PUBLIC"`.

That drift created two separate failures at once: Codespaces `psql` access broke, and runtime/debugging became misleading because the proxy bootstrapped far enough to look alive before the first real connection failed. We corrected the live instance with `gcloud sql instances patch plant-sql-demo --assign-ip --project=waooaw-oauth --quiet` and encoded the demo public-IP requirement in Terraform.

## Why This Matters

- Demo persistence validation is required to use Cloud SQL through the supported Auth Proxy path, not Docker Postgres.
- When public IP drifts off, developers lose the fastest reliable way to verify schema, data, and connection behavior from Codespaces.
- The failure mode is noisy and expensive: the proxy starts, but all real SQL connections fail later.

## Debt Item

**Name:** Cloud SQL network-mode drift prevention for demo

**Problem:** Demo Cloud SQL can drift away from the network mode required by the documented Codespaces/Auth Proxy workflow.

**Impact:** DB smoke checks, migration validation, and live debugging from Codespaces fail even though the instance itself remains RUNNABLE.

**Root cause:** Public-IP intent for demo was not explicit in Terraform, so manual or automation changes could leave `plant-sql-demo` private-only while the documented developer workflow still assumed a public-IP-backed Auth Proxy.

## What Is Needed To Pay This Debt Down

1. Keep the demo Cloud SQL public-IP requirement explicit in Terraform and review drift plans for any `ipv4_enabled` change.
2. Add a CI or scheduled drift assertion that fails when demo Cloud SQL no longer matches the expected network mode.
3. Keep the Codespaces bootstrap fail-fast so the exact recovery command is shown before developers waste time on dead `psql` retries.
4. Decide deliberately whether UAT/prod should stay private-only or share the same access model; do not leave that as implicit behavior.

## Recommended Follow-up

The next hardening step is an automated drift check focused specifically on `settings.ipConfiguration.ipv4Enabled` for `plant-sql-demo`. That converts this from a recurring hidden infrastructure surprise into a small, reviewable config diff caught before it blocks deployment or DB debugging.