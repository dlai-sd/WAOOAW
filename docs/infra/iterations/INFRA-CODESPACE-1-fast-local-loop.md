# INFRA-CODESPACE-1 — Fast Local Loop in GitHub Codespaces

> **Objective guardrail — read first**
> This plan exists to create a Docker-first local iteration loop inside GitHub Codespaces so WAOOAW engineers can rebuild, restart, and verify Plant, CP, PP, and routing quickly against demo-grade cloud dependencies without waiting for PR merge and Cloud Run deployment cycles.
> Every story in this plan must preserve that objective: reduce iteration latency, keep runtime behavior close to demo, and avoid drift into production deploy redesign, unrelated UX work, or backend business-feature expansion.

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `INFRA-CODESPACE-1` |
| Feature area | `Infrastructure — GitHub Codespaces fast local iteration loop` |
| Created | `2026-04-02` |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `User request in chat — Codespaces fast local loop using Docker against demo assets` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | `1` |
| Total epics | `3` |
| Total stories | `6` |

---

## Objective

1. Run WAOOAW local application surfaces in GitHub Codespaces through Docker images and Docker Compose.
2. Point the local stack at demo-grade dependencies where safe and practical: Cloud SQL, managed Redis, Google OAuth, and runtime secrets pulled from GCP.
3. Give developers one repeatable local command surface to build, restart, clean stale images, and reopen the stack on Codespaces URLs.
4. Keep the work focused on the local iteration loop; no production deploy redesign, no unrelated product features, no environment-specific hacks baked into images.

> **Agent instruction**
> Before executing any epic or story, re-read this Objective section and verify the change still reduces local iteration time without drifting into production-only deployment work, unrelated feature development, or committed secret/config hacks that would break image promotion.

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for autonomous GitHub-hosted agents and small-context models.
Every structural choice below is optimized to keep the agent on one narrow, testable path.

| Constraint | How this plan handles it |
|---|---|
| Limited context window | Every story card is self-contained and names exact edit files |
| No reliable shell access in GitHub-hosted runs | Story cards prefer file edits and narrow validation; iteration rules allow deferred Docker execution when shell tools are unavailable |
| Infra work can drift easily | Objective section and every epic title are outcome-based, not implementation-first |
| Secrets/config work can become unsafe | Every config story explicitly keeps values in Secret Manager, generated local env files, or runtime env only |

> **Agent:** Execute exactly one story at a time. Read only the files listed in that story card before editing. Do not invent additional infra scope.

---

## PM Review Checklist

- [x] Expert personas filled for the iteration task block
- [x] Epic titles name developer outcomes, not technical chores
- [x] Every story has an exact branch label
- [x] Relevant runtime/config code patterns are embedded inline
- [x] Every story card has max 3 files in “Files to read first”
- [x] No CP BackEnd story introduces business logic
- [x] Every config-changing story keeps secrets/runtime values out of images and committed env files
- [x] Every story has `BLOCKED UNTIL`
- [x] Iteration has time estimate and come-back datetime
- [x] Iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules
- [x] Iteration count minimized to one
- [x] Related backend/frontend/runtime work kept in the same iteration
- [x] No placeholders remain

---

## Vision Intake

- **Area**: `infra`, with cross-service local runtime wiring for Plant, CP, PP, and routing inside GitHub Codespaces.
- **Outcome**: A developer can rebuild or restart the local Docker stack in Codespaces, have it run against demo-aligned cloud dependencies, and open the live Codespaces URLs from a laptop for fast iteration.
- **Out of scope**: Production Cloud Run deployment redesign, unrelated product UX changes, and backend business-feature work that does not directly improve the local iteration loop.
- **Lane**: `Lane B` — new local orchestration surfaces and configuration wiring are required.
- **Urgency**: Single iteration only; one merge should materially reduce the current PR-approval plus deployment wait loop.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Demo-aligned Docker runtime, one-command stack control, and Codespaces public URL stability for Plant + CP + PP | 3 | 6 | 5h 30m | 2026-04-02 23:30 UTC |

**Estimate basis:** env bootstrap = 45 min | compose/runtime overlay = 60 min | orchestration script = 60 min | cleanup/doctor = 45 min | CP local proxy wiring = 60 min | focused validation = 60 min | 20% buffer already included.

---

## How to Launch Each Iteration

### Iteration 1

**Steps to launch:**
1. Open this repository on GitHub
2. Open the **Agents** tab
3. Start a new agent task
4. If the UI exposes repository agents, select **platform-engineer**; otherwise use the default coding agent
5. Copy the block below and paste it into the task
6. Start the run
7. Go away. Come back at: **2026-04-02 23:30 UTC**

**Iteration 1 agent task** (paste verbatim — do not modify):

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Docker / container engineer + Senior GitHub Codespaces / GCP runtime engineer + Senior frontend platform engineer (Nginx/runtime config)
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/infra/iterations/INFRA-CODESPACE-1-fast-local-loop.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3. Do not invent Iteration 2.
TIME BUDGET: 5h 30m. If you reach 6h 30m without finishing, follow STUCK PROTOCOL immediately.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; make the code changes, record exactly what could not be validated, and keep the PR flow moving.

FAIL-FAST VALIDATION GATE (complete before reading story cards or editing files):
1. Verify the plan file is readable and the Iteration 1 section exists.
2. Verify this execution surface allows repository writes on the current task branch.
3. Verify this execution surface allows opening or updating a PR to `main`, or at minimum posting that PR controls are unavailable.
4. If any validation gate fails: post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read the "Agent Execution Rules" section in this plan file.
2. Read the "Iteration 1" section in this plan file.
3. Read nothing else before starting.
4. Work on the GitHub task branch created for this run. Do not assume terminal checkout or manual branch creation.
5. Execute Epics in this order: E1 → E2 → E3.
6. Add or update the tests listed in each story before moving on.
7. If shell/docker validation is unavailable, state exactly: "Validation deferred: GitHub Agents tab on this run did not expose shell/docker execution."
8. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all other instructions.

### Rule -2 — Fail-fast validation gate

Before reading story cards in detail or making any code changes, validate all of the following:

- The plan file is readable and the assigned iteration section exists.
- The GitHub execution surface lets you save repository changes on the current task branch.
- The GitHub execution surface lets you open or update a PR to `main`, or you can explicitly report that PR controls are unavailable.

If any check fails, post `Blocked at validation gate: [exact reason]` and HALT immediately.

### Rule -1 — Objective anti-drift check

Before starting each epic, re-read the Objective section at the top of this plan and verify the next story still improves the local Codespaces iteration loop.
If a tempting change does not directly reduce local iteration time, improve demo-aligned runtime fidelity, or stabilize Codespaces URLs, do not do it.

### Rule 0 — Use the GitHub task branch and open the iteration PR early

- Keep the whole iteration on the single task branch created for this run.
- Open a draft PR to `main` as soon as PR controls are available and keep updating that same PR.
- Use the Tracking Table in this plan as the source of truth for story status updates.

### Rule 1 — Scope lock

Implement exactly the acceptance criteria in the story card.
Do not add production deploy steps, Terraform drift cleanup, or unrelated feature work.

### Rule 2 — Runtime config safety

Any environment-specific value must live in one of these places only:
- GCP Secret Manager
- Cloud Run runtime env/secret references
- uncommitted generated local env files such as `.codespace/demo.env`

Never bake secrets or environment-specific URLs into Dockerfiles, committed `.env` files, source code constants, or Terraform defaults.

### Rule 3 — Codespaces public URL realism

When a story touches frontend runtime config or routing, assume the user will open the app from a laptop over `https://${CODESPACE_NAME}-{PORT}.app.github.dev/`.
Localhost-only assumptions are bugs in this iteration.

### Rule 4 — Validation discipline

Prefer the narrowest possible validation:
- `bash -n` for shell scripts
- `docker compose ... config` for compose overlays
- focused frontend tests for codespace URL logic
- targeted smoke checks for health endpoints

### Rule 5 — STUCK PROTOCOL

If you hit the same blocker 3 times, stop immediately and report:
1. exact blocker
2. files already changed
3. validation already attempted
4. the smallest remaining manual decision

### Rule 6 — CHECKPOINT RULE

After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(infra-codespace-1): [epic-id] — [epic title]" && git push
```
Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

---

## Iteration 1

### Outcome

After this iteration, a WAOOAW engineer can bring up a Codespaces-local Docker stack that points at demo-aligned cloud dependencies, rebuild or restart that stack from one script, and open stable public Codespaces URLs for CP, PP, and the supporting APIs from a laptop.

### Dependency Map

| Order | Epic | Why first |
|---|---|---|
| 1 | E1 | The stack needs a generated demo env profile and compose overlay before orchestration can be reliable |
| 2 | E2 | One-command build/restart/clean depends on the env profile and compose overlay |
| 3 | E3 | Public URL and CP local proxy stability depend on the final compose/orchestration shape |

### Tracking Table

| Epic | Story | Status | Scope summary |
|---|---|---|---|
| E1 | E1-S1 | Not Started | Generate a demo-aligned Codespaces env file from GCP secrets and the Cloud SQL proxy |
| E1 | E1-S2 | Not Started | Add a Codespaces compose overlay and forward the ports needed for CP, PP, Plant, and tools |
| E2 | E2-S1 | Not Started | Add one orchestration script for up, build, restart, down, logs, status, and URL output |
| E2 | E2-S2 | Not Started | Add doctor and safe cleanup flows so stale images and broken proxy state stop slowing local loops |
| E3 | E3-S1 | Not Started | Give CP the same local nginx proxy behavior PP already has so Codespaces public URLs work cleanly |
| E3 | E3-S2 | Not Started | Add focused validation for the Codespaces URL/runtime-config and orchestration surfaces |

---

## Epic E1 — Developer starts a demo-aligned Codespaces stack without hand-editing env vars

### Story E1-S1 — Generate a demo env file from Secret Manager and the Cloud SQL proxy

| Field | Value |
|---|---|
| Story ID | `E1-S1` |
| Branch | `feat/infra-codespace-1-demo-env` |
| Estimate | 45 min |
| BLOCKED UNTIL | none |

**Context**

Codespaces already has `.devcontainer/gcp-auth.sh`, which authenticates to GCP, starts the Cloud SQL Auth Proxy on `127.0.0.1:15432`, and reads the demo Plant database URL secret. What is still missing is a Docker-consumable, uncommitted env file that normalizes those secrets for containers, including managed Redis URLs and the OAuth/runtime secrets the local stack actually needs.

**Files to read first (max 3)**

| File | Lines | Why |
|---|---|---|
| `.devcontainer/gcp-auth.sh` | 1-180 | Reuse the Cloud SQL proxy and secret-reading conventions already used in Codespaces |
| `cloud/terraform/stacks/plant/main.tf` | 120-220 | Confirm demo secret naming for Plant backend and Plant gateway Redis |
| `cloud/terraform/stacks/cp/main.tf` | 90-150 | Confirm demo secret naming for CP backend Redis and runtime secret injection patterns |

**Files to create / modify**

| File | Action | Precise instruction |
|---|---|---|
| `scripts/codespace-demo-env.sh` | create | Create a bash script that assumes `.devcontainer/gcp-auth.sh` has already run, reads the demo secrets it needs from Secret Manager, normalizes the Plant DB URL to `host.docker.internal:15432`, and writes `.codespace/demo.env` for Docker Compose consumption. |
| `.gitignore` | modify | Ignore `.codespace/*.env` and any generated runtime env artifacts created by the Codespaces local loop. |

**Required secret set**

The generated `.codespace/demo.env` must include these runtime values at minimum:
- `PLANT_DATABASE_URL`
- `PLANT_BACKEND_REDIS_URL`
- `PLANT_GATEWAY_REDIS_URL`
- `CP_BACKEND_REDIS_URL`
- `PP_BACKEND_REDIS_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `JWT_SECRET`
- `CP_REGISTRATION_KEY`
- `TURNSTILE_SECRET_KEY`
- `TURNSTILE_SITE_KEY`
- `WAOOAW_CLOUDSQL_ENV`

**Code patterns to copy exactly**

```bash
set -euo pipefail

TARGET_ENV="${WAOOAW_CLOUDSQL_ENV:-demo}"
ENV_FILE="/workspaces/WAOOAW/.codespace/demo.env"
mkdir -p "$(dirname "$ENV_FILE")"
chmod 700 "$(dirname "$ENV_FILE")"
```

```bash
# Runtime values only — never commit this file and never bake these into images.
# Same image must stay promotable from demo -> uat -> prod.
cat > "$ENV_FILE" <<EOF
PLANT_DATABASE_URL=${NORMALIZED_DATABASE_URL}
EOF
chmod 600 "$ENV_FILE"
```

**Acceptance criteria**

1. Running `bash scripts/codespace-demo-env.sh` after `.devcontainer/gcp-auth.sh` creates `.codespace/demo.env` without manual edits.
2. The generated Plant DB URL points containers to `host.docker.internal:15432`, not raw localhost or a committed Cloud SQL host.
3. Managed Redis URLs for Plant backend, Plant gateway, CP backend, and PP backend are written from Secret Manager values, not local `redis://redis:6379/*` defaults.
4. OAuth/runtime secrets required for CP and PP local login flows are written to the generated env file.
5. `.codespace/demo.env` is git-ignored and written with restrictive file permissions.

**Tests / validation**

| Test ID | Command | Assert |
|---|---|---|
| `E1-S1-T1` | `bash -n scripts/codespace-demo-env.sh` | Script syntax is valid |
| `E1-S1-T2` | `WAOOAW_CLOUDSQL_ENV=demo bash scripts/codespace-demo-env.sh --dry-run` | Dry-run prints the env file path and secret names without writing secrets to stdout |

**Commit message**

`feat(infra-codespace-1): add codespace demo env bootstrap`

---

### Story E1-S2 — Add a Codespaces compose overlay and expose the right public ports

| Field | Value |
|---|---|
| Story ID | `E1-S2` |
| Branch | `feat/infra-codespace-1-compose-overlay` |
| Estimate | 60 min |
| BLOCKED UNTIL | `E1-S1` complete |

**Context**

`docker-compose.local.yml` is currently local-regression first: it defaults to local Postgres, local Redis, and partial port exposure. For a real Codespaces iteration loop, the stack needs an overlay that consumes `.codespace/demo.env`, points app containers at demo-aligned dependencies, and exposes the CP, PP, backend, gateway, and admin ports the laptop browser will actually need.

**Files to read first (max 3)**

| File | Lines | Why |
|---|---|---|
| `docker-compose.local.yml` | 1-520 | Base service names, existing local ports, and current dependency graph |
| `.devcontainer/devcontainer.json` | 1-80 | Current forwarded ports and Codespaces startup hooks |
| `start-local-no-docker.sh` | 1-40 | Existing local entrypoint that should remain a simple wrapper, not a second orchestration system |

**Files to create / modify**

| File | Action | Precise instruction |
|---|---|---|
| `docker-compose.codespace.yml` | create | Create a Docker Compose overlay for Codespaces that consumes `.codespace/demo.env`, points services at host-proxied Cloud SQL and managed Redis URLs, and keeps the same service names as `docker-compose.local.yml`. |
| `.devcontainer/devcontainer.json` | modify | Forward the ports needed for the local Codespaces loop: `3001`, `3002`, `8000`, `8001`, `8015`, `8020`, `8081`, `5555`, and `15432`. |
| `start-local-no-docker.sh` | modify | Keep it as a tiny wrapper, but redirect users to the new orchestration script once that script exists instead of telling them to run bare `docker compose -f docker-compose.local.yml up --build`. |

**Code patterns to copy exactly**

```yaml
services:
  plant-backend:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

```yaml
services:
  cp-backend:
    env_file:
      - .codespace/demo.env
```

```json
"forwardPorts": [3001, 3002, 8000, 8001, 8015, 8020, 8081, 5555, 15432]
```

**Acceptance criteria**

1. `docker compose --env-file .codespace/demo.env -f docker-compose.local.yml -f docker-compose.codespace.yml config` renders successfully.
2. The overlay uses generated runtime values from `.codespace/demo.env` instead of hardcoded localhost or committed secret values.
3. Codespaces forwards CP frontend, PP frontend, CP backend, PP backend, Plant gateway, Plant backend, Adminer, Flower, and Cloud SQL proxy ports.
4. The base local compose file remains usable for pure local regression; Codespaces-specific behavior lives in the overlay rather than breaking the default local path.

**Tests / validation**

| Test ID | Command | Assert |
|---|---|---|
| `E1-S2-T1` | `docker compose --env-file .codespace/demo.env -f docker-compose.local.yml -f docker-compose.codespace.yml config >/tmp/codespace-compose.out` | Compose overlay resolves without schema or env errors |
| `E1-S2-T2` | `jq '.forwardPorts' .devcontainer/devcontainer.json` | Required ports are present |

**Commit message**

`feat(infra-codespace-1): add codespace compose overlay`

---

## Epic E2 — Developer can rebuild, restart, and clean the local stack from one command

### Story E2-S1 — Create one orchestration script for build, up, restart, down, logs, status, and URLs

| Field | Value |
|---|---|
| Story ID | `E2-S1` |
| Branch | `feat/infra-codespace-1-stack-script` |
| Estimate | 60 min |
| BLOCKED UNTIL | `E1-S1` and `E1-S2` complete |

**Context**

Right now the repo has scattered local entrypoints: `start-local-no-docker.sh`, various README snippets, and one-off scripts such as `cloud/test/portal-v2.sh`. That is too fragmented for fast iteration. The local loop needs one consistent orchestration surface that feels like a small local version of the WAOOAW Deploy workflow: build what changed, restart what changed, and show the URLs you can open from the laptop.

**Files to read first (max 3)**

| File | Lines | Why |
|---|---|---|
| `start-local-no-docker.sh` | 1-40 | Existing user-facing local command |
| `docker-compose.local.yml` | 1-520 | Service names and health targets |
| `docker-compose.codespace.yml` | 1-240 | Codespaces overlay that this script must use |

**Files to create / modify**

| File | Action | Precise instruction |
|---|---|---|
| `scripts/codespace-stack.sh` | create | Create a bash orchestration script with subcommands `bootstrap-env`, `build`, `up`, `restart`, `down`, `logs`, `status`, and `urls`. It must use `docker-compose.local.yml` plus `docker-compose.codespace.yml` and default to `.codespace/demo.env`. |
| `start-local-no-docker.sh` | modify | Make this script delegate to `scripts/codespace-stack.sh up` for the Codespaces-first path rather than duplicating compose logic. |

**Supported command surface**

The script must support:
- `bash scripts/codespace-stack.sh bootstrap-env`
- `bash scripts/codespace-stack.sh up all`
- `bash scripts/codespace-stack.sh build cp`
- `bash scripts/codespace-stack.sh restart plant`
- `bash scripts/codespace-stack.sh down`
- `bash scripts/codespace-stack.sh logs cp`
- `bash scripts/codespace-stack.sh status`
- `bash scripts/codespace-stack.sh urls`

**Code patterns to copy exactly**

```bash
COMPOSE_FILES=(-f docker-compose.local.yml -f docker-compose.codespace.yml)
ENV_FILE=".codespace/demo.env"
DC=(docker compose --env-file "$ENV_FILE" "${COMPOSE_FILES[@]}")
```

```bash
case "${1:-}" in
  up|build|restart|down|logs|status|urls|bootstrap-env) ;;
  *) echo "Usage: $0 {bootstrap-env|build|up|restart|down|logs|status|urls} [all|plant|cp|pp]"; exit 1 ;;
esac
```

```bash
# Codespaces URL pattern
if [[ -n "${CODESPACE_NAME:-}" ]]; then
  echo "CP Frontend: https://${CODESPACE_NAME}-3002.app.github.dev/"
fi
```

**Acceptance criteria**

1. A developer can start the whole stack with one command and no raw compose flags.
2. The script accepts targeted scopes at minimum: `all`, `plant`, `cp`, and `pp`.
3. `urls` prints the exact public Codespaces URLs for CP frontend, PP frontend, CP backend, PP backend, Plant gateway, and Plant backend when `CODESPACE_NAME` is present.
4. The script exits fast with clear error text when `.codespace/demo.env` is missing.

**Tests / validation**

| Test ID | Command | Assert |
|---|---|---|
| `E2-S1-T1` | `bash -n scripts/codespace-stack.sh` | Script syntax is valid |
| `E2-S1-T2` | `CODESPACE_NAME=test-space bash scripts/codespace-stack.sh urls` | All expected `app.github.dev` URLs are printed |

**Commit message**

`feat(infra-codespace-1): add codespace stack orchestrator`

---

### Story E2-S2 — Add doctor and safe cleanup so stale images stop slowing the loop

| Field | Value |
|---|---|
| Story ID | `E2-S2` |
| Branch | `feat/infra-codespace-1-stack-doctor-clean` |
| Estimate | 45 min |
| BLOCKED UNTIL | `E2-S1` complete |

**Context**

Codespaces loses speed when Docker layers, stopped containers, and stale builder cache pile up. At the same time, destructive cleanup is dangerous in a shared dev container. The orchestration script needs two explicit safety valves: a `doctor` command that explains what is broken, and a `clean` command that removes only WAOOAW-local build artifacts instead of carpet-bombing the entire Docker daemon.

**Files to read first (max 3)**

| File | Lines | Why |
|---|---|---|
| `scripts/codespace-stack.sh` | 1-260 | Extend the single orchestration surface instead of creating a second one |
| `.devcontainer/gcp-auth.sh` | 1-180 | Reuse the proxy success signals and failure language |
| `docker-compose.local.yml` | 1-520 | Identify the WAOOAW-local container and image names that are safe to clean |

**Files to create / modify**

| File | Action | Precise instruction |
|---|---|---|
| `scripts/codespace-stack.sh` | modify | Add `doctor` and `clean` subcommands. `doctor` must validate Docker, compose files, `.codespace/demo.env`, Cloud SQL proxy state, and health endpoints. `clean` must remove only WAOOAW-local containers/images/build cache and never use `docker system prune -a`. |

**Code patterns to copy exactly**

```bash
if ! pgrep -fa cloud-sql-proxy >/dev/null 2>&1; then
  echo "Cloud SQL proxy not running. Run: bash .devcontainer/gcp-auth.sh"
  exit 1
fi
```

```bash
# Safe cleanup only — do not wipe the whole daemon.
docker compose --env-file "$ENV_FILE" "${COMPOSE_FILES[@]}" down --remove-orphans || true
docker image prune -f >/dev/null 2>&1 || true
docker builder prune -f --filter 'until=24h' >/dev/null 2>&1 || true
```

**Acceptance criteria**

1. `doctor` reports missing env file, missing proxy, missing Docker, and unhealthy services with specific next actions.
2. `clean` removes WAOOAW-local stopped containers, dangling images, and stale builder cache without using `docker system prune -a`.
3. The script still preserves non-WAOOAW Docker resources in the Codespace.
4. `doctor` includes at least CP frontend, PP frontend, CP backend, PP backend, Plant gateway, and Plant backend health checks when those services are up.

**Tests / validation**

| Test ID | Command | Assert |
|---|---|---|
| `E2-S2-T1` | `bash -n scripts/codespace-stack.sh` | Script remains syntactically valid after adding new subcommands |
| `E2-S2-T2` | `bash scripts/codespace-stack.sh doctor` | Failures print actionable messages instead of raw stack traces |

**Commit message**

`feat(infra-codespace-1): add doctor and safe cleanup`

---

## Epic E3 — Developer can use Codespaces public URLs from a laptop without API or OAuth drift

### Story E3-S1 — Give CP the same local nginx proxy behavior PP already has

| Field | Value |
|---|---|
| Story ID | `E3-S1` |
| Branch | `feat/infra-codespace-1-cp-local-proxy` |
| Estimate | 60 min |
| BLOCKED UNTIL | `E1-S2` and `E2-S1` complete |

**Context**

PP already has a local nginx mode that proxies `/api` to `pp-backend`, which is why same-origin Codespaces URLs can work there. CP does not: `src/CP/FrontEnd/nginx.conf` is Cloud Run only and leaves `/api` disabled. That breaks the browser-side Codespaces assumption in `src/CP/FrontEnd/src/config/oauth.config.ts`, which already expects same-origin `/api` in Codespaces.

**Files to read first (max 3)**

| File | Lines | Why |
|---|---|---|
| `src/CP/FrontEnd/Dockerfile` | 1-220 | CP frontend image currently has no local/cloudrun nginx mode split |
| `src/CP/FrontEnd/nginx.conf` | 1-200 | Current CP frontend runtime config disables `/api` proxying |
| `src/CP/FrontEnd/src/config/oauth.config.ts` | 1-140 | Codespaces runtime already expects `currentUrl + /api`; make the container honor that contract |

**Files to create / modify**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/nginx.local.conf` | create | Create a local nginx config mirroring PP’s local behavior: SPA fallback, static asset caching, OAuth-safe headers, and `/api` reverse proxy to `cp-backend:8020`. |
| `src/CP/FrontEnd/Dockerfile` | modify | Add `ARG NGINX_MODE=cloudrun` and switch between `nginx.conf` and `nginx.local.conf` at build time, matching the PP frontend pattern. |
| `docker-compose.codespace.yml` | modify | Set CP frontend build arg `NGINX_MODE=local` for the Codespaces overlay. |

**Code patterns to copy exactly**

```nginx
location /api {
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://cp-backend:8020;
}
```

```dockerfile
ARG NGINX_MODE=cloudrun
COPY nginx.conf /etc/nginx/nginx.cloudrun.conf
COPY nginx.local.conf /etc/nginx/nginx.local.conf
RUN if [ "$NGINX_MODE" = "local" ]; then cp /etc/nginx/nginx.local.conf /etc/nginx/nginx.conf; else cp /etc/nginx/nginx.cloudrun.conf /etc/nginx/nginx.conf; fi
```

**Acceptance criteria**

1. The CP frontend image supports both `cloudrun` and `local` nginx modes without duplicating the whole Dockerfile.
2. In Codespaces/local mode, CP browser requests to `/api/*` proxy to `cp-backend:8020` from the same public frontend origin.
3. The existing Codespaces behavior in `oauth.config.ts` becomes valid rather than aspirational.
4. OAuth popup-safe headers remain present in the CP local nginx config.

**Tests / validation**

| Test ID | Command | Assert |
|---|---|---|
| `E3-S1-T1` | `docker compose --env-file .codespace/demo.env -f docker-compose.local.yml -f docker-compose.codespace.yml build cp-frontend` | CP frontend builds in local nginx mode |
| `E3-S1-T2` | `docker compose --env-file .codespace/demo.env -f docker-compose.local.yml -f docker-compose.codespace.yml config | grep -n "NGINX_MODE=local"` | Codespaces overlay selects local nginx mode |

**Commit message**

`feat(infra-codespace-1): add cp local nginx proxy mode`

---

### Story E3-S2 — Add focused validation for Codespaces URL and orchestration behavior

| Field | Value |
|---|---|
| Story ID | `E3-S2` |
| Branch | `feat/infra-codespace-1-validation` |
| Estimate | 60 min |
| BLOCKED UNTIL | `E2-S2` and `E3-S1` complete |

**Context**

Without focused validation, the next small config edit will break Codespaces URLs again and no one will know until they open the app from a laptop. This iteration needs lightweight, automatable checks for the new shell surface and the Codespaces runtime-config assumptions in CP and PP frontends.

**Files to read first (max 3)**

| File | Lines | Why |
|---|---|---|
| `src/CP/FrontEnd/src/config/oauth.config.ts` | 1-140 | Validate CP Codespaces API base behavior |
| `src/PP/FrontEnd/src/config/oauth.config.ts` | 1-120 | Validate PP Codespaces API base behavior |
| `scripts/codespace-stack.sh` | 1-320 | Validate the public URL and command surface contract |

**Files to create / modify**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/__tests__/oauth.config.codespace.test.ts` | create | Add a focused test that stubs a `github.dev` hostname and asserts CP uses the current origin plus `/api`. |
| `src/PP/FrontEnd/src/__tests__/oauth.config.codespace.test.ts` | create | Add the equivalent focused test for PP. |
| `scripts/test-codespace-stack.sh` | create | Add a tiny shell validation script that checks `bash -n scripts/codespace-stack.sh` and asserts `urls` prints the expected `app.github.dev` links when `CODESPACE_NAME` is set. |

**Code patterns to copy exactly**

```typescript
Object.defineProperty(window, 'location', {
  value: new URL('https://demo-space-3002.app.github.dev/'),
  writable: true,
})
```

```typescript
expect(config.apiBaseUrl).toBe('https://demo-space-3002.app.github.dev/api')
```

```bash
set -euo pipefail
bash -n scripts/codespace-stack.sh
CODESPACE_NAME=test-space bash scripts/codespace-stack.sh urls | grep 'app.github.dev'
```

**Acceptance criteria**

1. CP frontend has an automated test proving Codespaces hosts resolve to `current origin + /api`.
2. PP frontend has the same regression guard.
3. The orchestration script has a small executable validation surface that checks syntax and URL output.
4. The final iteration can state exactly which narrow validations passed, even if full Docker runtime smoke is deferred on GitHub-hosted execution.

**Tests / validation**

| Test ID | Command | Assert |
|---|---|---|
| `E3-S2-T1` | `cd src/CP/FrontEnd && npm test -- --run src/__tests__/oauth.config.codespace.test.ts` | CP Codespaces runtime-config test passes |
| `E3-S2-T2` | `cd src/PP/FrontEnd && npm test -- --run src/__tests__/oauth.config.codespace.test.ts` | PP Codespaces runtime-config test passes |
| `E3-S2-T3` | `bash scripts/test-codespace-stack.sh` | Stack helper validation passes |

**Commit message**

`test(infra-codespace-1): add codespace loop validation`

---

## Out of Scope

| Area | Why it is out of scope in INFRA-CODESPACE-1 |
|---|---|
| Cloud Run deploy workflow redesign | This plan is about local Codespaces speed, not production deployment topology |
| Terraform import/reconcile of new infra | No new GCP resource creation is required for the local loop itself |
| CP or PP product UX redesign | The goal is fast local runtime iteration, not user-facing feature changes |
| Mobile app runtime loop | Mobile has a separate Codespaces path and is not part of this single-iteration scope |
| Broad backend business logic work | CP, PP, Plant runtime behavior should only change when needed to make the local loop usable from Codespaces |
