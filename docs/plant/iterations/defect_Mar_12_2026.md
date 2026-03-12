# Demo Deployment Review - 2026-03-12

## Objective

Customers of the WAOOAW platform are empowered to hire AI agents with zero cost and zero commitment for the first 7 days.

The customer should be able to hire a Digital Marketing Agent (DMA) that creates refined content and publishes it to YouTube based on the customer's submitted story and requested date and time. DMA is expected to expose skills such as theme creation, content creation, and content publishing. The design and implementation must also support future skill expansion so the same agent can later create and publish content to LinkedIn, Facebook, and other channels without redesigning the platform.

The CP portal must empower customers to perform the operations required to run and monitor their agent tasks. The PP portal must empower platform users to create, operate, and maintain the platform with strong health and hygiene so customers receive the best possible value from it.

## Story Compliance Lens

Every DMA story should be accepted only if it supports the objective above in a customer-visible or operator-visible way.

| Story area | Objective compliance required |
|---|---|
| Iteration 1 stories | Must create a real, hireable DMA runtime with usable skills, truthful approval-gated publishing, and extensibility for future channels |
| Iteration 2 stories | Must let the customer actually use CP/mobile to create briefs, review drafts, approve work, and understand publish readiness |
| Iteration 3 stories | Must let PP users support, diagnose, govern, and release the DMA in a way that protects customer value |
| Release-closeout story | Must prove the above objective on deployed portals with real runtime data, not just code and local tests |

## Story-By-Story Compliance Verdict

| Story | Verdict | Reason |
|---|---|---|
| I1-S1 - Register the Digital Marketing Agent and its three visible skills | Partially met | The DMA contract and visible skills were implemented in code, but demo does not prove a hireable DMA journey to a customer. |
| I1-S2 - Persist the Theme Discovery brief and draft workflow as first-class runtime state | Partially met | The schema and runtime model exist, but demo has no campaign, brief, or draft data to show the workflow in practice. |
| I1-S3 - Enforce approval-gated YouTube publish eligibility and credential execution | Partially met | Approval-gated publish logic exists, but demo has no real deliverable, approval, or YouTube connection state to validate the behavior end to end. |
| I1-S4 - Expose thin CP proxy routes for the new digital marketing runtime | Partially met | The CP routes are deployed, but the customer cannot exercise a real DMA journey on demo because the runtime data is missing. |
| I2-S1 - Build the CP Theme Discovery conversation and brief summary workflow | Missed on demo | The UI work exists in code, but the promised customer-visible brief journey is not actually observable on demo. |
| I2-S2 - Build the CP content review, approval, and YouTube readiness workflow | Missed on demo | The CP approval/readiness UI is implemented, but demo has no DMA deliverable or YouTube state to render the promised workflow. |
| I2-S3 - Bring Theme Discovery and brief review to mobile | Not proven | This review did not validate mobile, and there is no matching demo runtime state proving the DMA journey beyond local code/tests. |
| I2-S4 - Bring approval, publish readiness, and progress state to mobile | Not proven | Same issue as I2-S3: code may exist, but the customer-value proof was not established on a deployed runtime. |
| I3-S1 - Build PP oversight for briefs, approvals, and YouTube publish state | Missed on demo | PP routes and UI exist, but operators cannot inspect a real DMA instance because no DMA runtime data exists in demo. |
| I3-S2 - Build PP diagnostics for blocked publish, credentials, and scheduler traces | Partially met | The diagnostics surfaces are present in code and bundle text, but there is no real DMA runtime in demo to validate the operator workflow truthfully. |
| I3-S3 - Add audit, metrics, and run-history alignment for the agent lifecycle | Partially met | Supporting telemetry logic exists, but the lack of live DMA runs in demo means the lifecycle spine is not proven in customer/operator reality. |
| I3-S4 - Add regression coverage and release-closeout for the first sellable agent | Missed | This is the clearest miss: the story claimed sellable release readiness, but deployed demo does not show a real DMA customer journey or operator journey end to end. |

## Scope Reviewed

- PR 921: `feat(plant): complete DMA MVP story chain through I3-S4`
- Plan: `docs/plant/iterations/PLANT-DMA-1-digital-marketing-agent-youtube.md`
- Live portals: `https://cp.demo.waooaw.com` and `https://pp.demo.waooaw.com`

## Method

- Read the DMA plan and PR 921 file-change summary.
- Inspected the live portal shells, runtime config, deployed frontend bundles, and live API routes.
- Probed public documentation endpoints and key PR 921 routes without authentication.

## Important Limitation

- This review was done without authenticated customer or operator credentials, so the findings below cover the externally observable deployment surface, deployed assets, and route availability.
- The PR 921 routes do exist behind auth on both CP and PP, so the main issues found are release-quality and deployment-behavior defects, not total route absence.

## What PR 921 Achieved

- It completed the DMA story chain through `I3-S4` in code and in the plan status table, covering Plant, CP, PP, and mobile-related regression work.
- It shipped the first-class `Digital Marketing Agent`, structured `Theme Discovery`, approval-gated YouTube runtime, PP diagnostics, scheduler and hook-trace signals, and cross-surface regression coverage.
- The live CP bundle contains DMA customer-facing strings such as `Theme Discovery`, `YouTube channel status`, `Publish readiness`, `Blocked by approval`, and `Approve exact deliverable`.
- The live PP bundle contains operator-facing DMA diagnostics such as `Theme Discovery brief`, `Publish gate status`, `Missing YouTube credential`, and `Approval gate halted publish`.
- The key PR 921 backend routes are present in demo behind auth: CP DMA routes and PP operator routes all respond with `401`, which confirms route registration rather than `404` route absence.

## What PR 921 Missed Relative To The Plan

The plan's `I3-S4` outcome says the first sellable Digital Marketing Agent should have enough regression coverage, smoke validation, and release-closeout to ship confidently as a real marketplace offering. The deployed demo does not fully satisfy that release-closeout bar.

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| Public documentation paths were not exempted from auth and budget middleware expectations. | The demo APIs cannot self-describe in production, which weakens release-closeout, supportability, and smoke-verification confidence. | Exclude `/openapi.json`, `/docs`, and related schema assets from JWT-budget enforcement or fail with a clean `401/403/404` instead of `500`. |
| PR 921 closed release hardening while accepting known noisy validation outside the narrow regression slice. | The release note is truthful about residual noise, but it means the plan's `ship confidently` outcome was only partially met. | Add a final demo deployment gate that validates the live CP and PP support surfaces after deploy, not just targeted local regression slices before merge. |

## Observed Defects

| ID | Surface | Defect | Evidence | Root cause | Impact | Best possible solution/fix |
|---|---|---|---|---|---|---|
| D1 | CP demo API | `https://cp.demo.waooaw.com/api/docs` returns `500 Internal Server Error` instead of a usable docs page or an intentional auth response. | Live response body: `Budget middleware requires JWT claims`; `/api/openapi.json` also returns `Internal Server Error`. | Budget middleware is executing on documentation routes and expects JWT claims that do not exist for public docs requests. | Customer Portal demo support and release verification are weaker because the CP API cannot be inspected or smoke-verified through its documentation surface. | Whitelist docs/schema routes from budget enforcement, or disable public docs intentionally and return a controlled `401/403/404` instead of `500`. |
| D2 | PP demo API | `https://pp.demo.waooaw.com/api/docs` returns `500 Internal Server Error` instead of a usable docs page or an intentional auth response. | Live response body: `Budget middleware requires JWT claims`; `/api/openapi.json` also returns `Internal Server Error`. | Same middleware configuration problem on the PP deployment path. | PP operators and release reviewers lose a key support/debugging surface for the operator portal demo. | Apply the same docs-route middleware exemption or controlled auth response pattern on PP. |
| D3 | Release closeout | PR 921 claims the DMA MVP is ready through `I3-S4`, but the live demo still has broken public support surfaces on both portals. | PR 921 summary says it completed the chain through `I3-S4`; plan `I3-S4` requires enough smoke validation and release-closeout to ship confidently; live docs/openapi surfaces fail on both portals. | Release-closeout focused on targeted regression coverage, but did not include a post-deploy demo verification of public operational surfaces. | The release is code-complete, but demo-complete confidence is overstated because externally visible deployment defects remained. | Add a mandatory post-deploy checklist for demo URLs covering portal load, docs/schema availability policy, and a small authenticated smoke walkthrough for CP and PP. |
| D4 | CP portal | First-login navigation between `Dashboard` and `My Agents` still throws a session-timeout error on the first attempt, even though this was claimed fixed earlier. | User-observed defect on live demo; no matching fixed-string was found in current CP source search, which suggests the visible message likely comes from auth/session handling rather than a stable UI copy path. | First-load auth refresh or route bootstrap still races with the first authenticated page transition. The second login likely works because session state or refresh token state is then hydrated correctly. | The first impression of the CP portal is still broken and undermines trust in the claimed fix. | Reproduce with authenticated browser tracing on demo, inspect CP auth refresh flow during the first route switch, and add an end-to-end regression specifically for first-login `Dashboard -> My Agents` navigation. |
| D5 | CP portal / demo data | The DMA stories and user journeys promised in the PLANT-DMA-1 plan are not visible in CP because the demo database has no DMA runtime data at all. | Cloud SQL demo schema contains the required tables: `campaigns`, `content_posts`, `marketing_draft_batches`, `marketing_draft_posts`, `platform_connections`, `skill_configs`, `flow_runs`, `component_runs`. But live counts are `0` for `hired_agents` with `agent_id='AGT-MKT-DMA-001'`, `0` campaigns, `0` marketing_draft_batches, `0` content_posts, and `0` YouTube platform connections. | This is not a missing DDL problem. The schema exists, but no Digital Marketing Agent hired instance or seeded runtime data exists in demo to drive the CP workflows. | Customers cannot see Theme Discovery, draft review, approval, or YouTube readiness journeys because nothing exists in demo to render them. The implementation may be present, but the demo cannot prove it. | Seed or create at least one demo DMA subscription and hired instance, plus a structured Theme Discovery brief, campaign row, draft batch, deliverable/content post, and YouTube platform connection reference so the CP journey has actual runtime state to display. |
| D6 | PP sign-in | PP sign-in shows `Google Sign-In is not configured for this environment (missing client ID)` even though demo should support Google sign-in. | User-observed live defect. In source, that message is shown only when `config.googleClientId` resolves empty. But the live `https://pp.demo.waooaw.com/pp-runtime-config.js` currently serves a non-empty `googleClientId`. | The likely issue is not a missing configured value in source control. It is more likely a runtime-config script load failure, stale bundle/runtime mismatch, or page-load sequencing issue where `pp-runtime-config.js` did not populate before the sign-in screen rendered in the user session. | PP login looks broken and creates the impression that Google OAuth was regressed, even if the backend/client ID may still be configured underneath. | Capture a live browser session with network logs for `pp-runtime-config.js`, confirm whether the script loads before app bootstrap on demo, and verify there is no CDN/cache skew between the main bundle and runtime config file. |
| D7 | PP portal / demo data | The DMA stories and user journeys promised in the PLANT-DMA-1 plan are not visible in PP because the demo database has no DMA runtime data at all. | Same Cloud SQL demo evidence as CP: required runtime tables exist, but counts are `0` for DMA hired agents, campaigns, draft batches, content posts, and YouTube platform connections. PP strings and routes are deployed, but there is no runtime state to inspect. | PP operator tooling was shipped, but the supporting demo runtime data was never created or preserved in demo. | Operators cannot inspect the customer brief, approval queue, publish blockers, or YouTube readiness for the Digital Marketing Agent because there is no DMA instance to inspect. | Seed a realistic DMA demo runtime in Cloud SQL, including approval-linked deliverables and at least one blocked/ready publish state so PP can demonstrate the plan's operator workflows truthfully. |
| D8 | Story design / planning process | DMA was written and accepted as a long multi-surface story chain without a hard requirement that the promised customer-visible portal journey must exist on demo with real data before sign-off. | Plan status says all DMA stories are `Completed`, but demo has no DMA hired instance, no campaign, no draft, no deliverable, and no YouTube connection to make the promised CP/PP journey real. | The stories optimized for code slices and test slices, not for sellable customer proof. The planning process did not force `demo data to create`, `exact walkthrough steps`, `demo account/persona`, or `proof of visible value` as acceptance criteria. | This creates fake completion: long stories look done on paper while the customer still gets nothing visible or sellable in the portal. | Any future sellable MVP story must be invalid unless it names the demo persona, demo runtime data to create, exact CP/PP/mobile walkthrough steps, and a deployed proof gate showing the customer-visible journey end to end. |

## Route Presence Verified In Demo

These PR 921 routes are deployed and reachable behind auth, based on `401` responses rather than `404`:

- CP: `/api/api/cp/campaigns/{campaign_id}/upload-eligibility`
- CP: `/api/api/cp/platform-credentials/youtube`
- CP: `/api/api/cp/campaigns/{campaign_id}/posts/{post_id}/publish`
- PP: `/api/api/pp/ops/hired-agents/{hired_instance_id}/skills`
- PP: `/api/api/pp/ops/hired-agents/{hired_instance_id}/platform-connections`
- PP: `/api/api/pp/approvals/review-queue`
- PP: `/api/api/pp/ops/hired-agents/{hired_agent_id}/scheduler-diagnostics`

## Remediation Status On Branch

This section reflects branch-local remediation work completed after the defect review. These items are code-complete and Docker-validated on branch, but they are not yet re-verified on deployed demo URLs.

| Defect | Branch status | Implementation status | Validation evidence |
|---|---|---|---|
| D1 | Fixed on branch | Plant Gateway auth, budget, and RBAC middleware now share the same public-path rules for `/docs`, `/openapi.json`, `/redoc`, and proxied docs paths. | Docker: focused gateway middleware pytest passed (`32 passed`). |
| D2 | Fixed on branch | Same shared public-path middleware fix covers PP through the shared Plant Gateway path. | Docker: focused gateway middleware pytest passed (`32 passed`). |
| D3 | Process fix done on branch | `docs/CONTEXT_AND_INDEX.md` now requires customer-visible proof, demo runtime data, walkthrough steps, and release gates for sellable portal work. | Manual doc review completed. |
| D4 | Mitigated on branch | CP frontend now forces refresh on protected-route 401s even without a stored session hint and no longer mislabels `User not found` as an expired session. | Docker: focused CP frontend Vitest passed (`14 passed`). Live demo re-verification still pending. |
| D5 | Fixed on branch | Added migration `032_seed_demo_dma_runtime` to seed DMA hired agents, campaigns, draft batches, content posts, deliverables, approvals, skill configs, and YouTube platform connections for demo/uat. | Docker: Alembic `upgrade head` succeeded against disposable Postgres. |
| D6 | Fixed on branch | PP runtime config and API endpoints are now resolved lazily so `pp-runtime-config.js` can hydrate after module import without leaving Google client ID empty. | Docker: focused PP frontend Vitest passed (`1 passed`). |
| D7 | Fixed on branch | Same DMA demo seed migration addresses the missing PP runtime journey by creating inspectable operator data. | Docker: Alembic `upgrade head` succeeded against disposable Postgres. |
| D8 | Process fix done on branch | Story-definition rules now explicitly require demo actor, runtime data, walkthrough path, visible success/blocked states, and proof artifact. | Manual doc review completed. |

## Docker Validation Summary

| Command | Result |
|---|---|
| `docker build --build-arg INSTALL_DEV_DEPS=true -t waooaw-gateway-test ./src/Plant/Gateway && docker run --rm waooaw-gateway-test python -m pytest middleware/tests/test_budget.py middleware/tests/test_rbac.py` | Passed (`32 passed`) |
| `docker build --target test -t waooaw-pp-frontend-test ./src/PP/FrontEnd && docker run --rm waooaw-pp-frontend-test npm run test -- --run src/config/oauth.config.test.ts` | Passed (`1 passed`) |
| `docker run --rm -v "$PWD/src/CP/FrontEnd":/app -w /app node:20-alpine sh -lc "npm test -- --run src/__tests__/auth.service.test.ts src/__tests__/gatewayApiClient.test.ts"` | Passed (`14 passed`) |
| Disposable Postgres + `Dockerfile.migrations` + `python -m alembic upgrade head` | Passed |

## Bottom Line

PR 921 did achieve the main DMA implementation and much of the intended portal behavior, and the deployed bundles show the new DMA customer and operator vocabulary. The main miss is release hardening on the live demo deployment: both CP and PP documentation/schema surfaces are broken by middleware, which means the demo is not fully closed out to the standard promised by `I3-S4`.

## Database Check - DDL vs Data

This was checked directly against demo Cloud SQL through the Auth Proxy.

| Check | Result | Conclusion |
|---|---|---|
| DMA-related tables exist | `campaigns`, `content_posts`, `marketing_draft_batches`, `marketing_draft_posts`, `platform_connections`, `skill_configs`, `flow_runs`, `component_runs` all exist | DDL is present for the DMA runtime surface |
| DMA hired-agent rows | `0` rows where `hired_agents.agent_id = 'AGT-MKT-DMA-001'` | No Digital Marketing Agent instance exists in demo |
| Campaign rows | `0` | No Theme Discovery or campaign runtime exists |
| Draft batch rows | `0` | No reviewable marketing draft workflow exists |
| Content post rows | `0` | No deliverables exist for approval/publish journeys |
| YouTube platform connections | `0` rows with `platform_key = 'youtube'` | No channel readiness state exists |

Conclusion: the main CP and PP journey absence is a missing demo-data problem, not a missing-schema problem.

## Process Defect To Prevent Next Time

The DMA failure was not only an implementation gap. It was a story-definition gap.

| Failure | What should have been required in the story | Why it matters |
|---|---|---|
| Story said customer gets a portal journey | Name the exact demo customer/operator accounts and hired instance ids | Without named actors, nobody proves the journey on demo |
| Story said CP/PP surfaces are delivered | Name the exact demo rows/state to create: hire, brief, draft, approval, connection, publish state | Without runtime data, the UI has nothing truthful to render |
| Story said release-closeout is done | Name the exact deployed URL walkthrough steps and pass/fail proof | Without a live walkthrough, completion is only local code confidence |
| Story said sellable MVP exists | Add a hard sign-off rule: if customer cannot see and operate it on demo, the story is not complete | This stops fake completion and forces value, not activity |