# MOB-API-REDUNDANCY-AUDIT — Mobile vs CP API Endpoint Comparison

> **Purpose**: Identify where the mobile app calls separate Plant API endpoints
> instead of reusing the same endpoints the CP frontend uses. These redundancies
> must be consolidated before adding new features.

---

## Audit Metadata

| Field | Value |
|---|---|
| Audit ID | MOB-API-REDUNDANCY-AUDIT |
| Date | 2026-04-14 |
| Scope | `src/mobile/src/services/`, `src/mobile/src/hooks/`, `src/CP/FrontEnd/src/`, `src/CP/BackEnd/api/`, `src/Plant/BackEnd/api/` |
| Status | **Partially closed** — Wave 1+2 CP→Gateway migration complete (2026-04-xx); remaining items in §6 |

---

## 1. Critical Redundancies (mobile calls a different Plant route for the same resource)

| Feature | CP Frontend Endpoint | Mobile Endpoint | Root Cause | Impact | Recommended Fix |
|---|---|---|---|---|---|
| **Payments — Create Order** | `/cp/payments/razorpay/order` (CP Backend) | `/v1/payments/create-order` (Plant) | Mobile bypasses CP proxy, calls Plant directly | Two separate payment flows; risk of divergent business logic | Consolidate to single endpoint; mobile should reuse CP route |
| **Payments — Verify** | `/cp/payments/razorpay/confirm` (CP Backend) | `/v1/payments/verify` (Plant) | Same as above | Payment verification logic split across two services | Consolidate to single endpoint |
| **Skills — List** | `/v1/genesis/skills` (gateway) | `/v1/skills` (apiClient) | Different URL prefix for same resource | Two Plant routes serving identical data | Standardize to `/v1/skills`, update CP frontend |
| **Skills — Get** | `/v1/genesis/skills/{id}` (gateway) | `/v1/skills/{id}` (apiClient) | Same as above | Same as above | Same as above |
| **Job Roles — List** | `/v1/genesis/job-roles` (gateway) | `/v1/job-roles` (apiClient) | Same as above | Same as above | Standardize to `/v1/job-roles`, update CP frontend |
| **Job Roles — Get** | `/v1/genesis/job-roles/{id}` (gateway) | `/v1/job-roles/{id}` (apiClient) | Same as above | Same as above | Same as above |
| **Auth — Google Verify** | `/cp/auth/google/verify` (CP Backend) | `/auth/google/verify` (Plant) | Mobile authenticates directly against Plant | Auth logic potentially duplicated | Evaluate which is canonical; consolidate |

---

## 2. Properly Shared Endpoints (no redundancy — keep as-is)

| Feature | Shared Endpoint | Protocol |
|---|---|---|
| List Agents | `/v1/agents` | Both via Plant |
| Get Agent | `/v1/agents/{id}` | Both via Plant |
| Agent Types | `/v1/agent-types` | Both via Plant |
| Trial Status | `/v1/trial-status` | Both via Plant |
| My Agents Summary | `/api/v1/hired-agents/by-customer/{customerId}` | Mobile → Plant Gateway ✅ migrated |
| Platform Connections (list/create/delete) | `/api/v1/hired-agents/{id}/platform-connections` | Mobile → Plant Gateway ✅ migrated |
| YouTube OAuth Start | `/api/v1/customer-platform-connections/youtube/connect/start` | Mobile → Plant Gateway ✅ migrated |
| Content Recommendations | `/api/v1/hired-agents/{id}/content-recommendations` | Mobile → Plant Gateway ✅ migrated |
| Invoices (list / HTML) | `/api/v1/invoices`, `/api/v1/invoices/{id}/html` | Mobile → Plant Gateway ✅ migrated |
| Receipts (list / HTML) | `/api/v1/receipts`, `/api/v1/receipts/{id}/html` | Mobile → Plant Gateway ✅ migrated |

---

## 3. Mobile-Only Plant Endpoints (no CP equivalent)

| Endpoint | Notes |
|---|---|
| `POST /v1/payments/refund` | Refund flow only on mobile |
| `GET  /v1/payments/{id}/status` | Payment status check only on mobile |
| `POST /api/v1/customers/fcm-token` | Push notification registration — mobile-only, expected |

---

## 4. CP Features Missing from Mobile (feature gaps, not redundancy)

| Feature Area | CP Endpoint(s) | Notes |
|---|---|---|
| Goal management | `/cp/hired-agents/{id}/goals` (GET/PUT/DELETE) | Mobile cannot list, create, or delete goals |
| Deliverable review | `/api/v1/hired-agents/{id}/deliverables`, `POST /api/v1/deliverables/{id}/review` | ✅ Implemented in Wave 2 — approve/reject via Plant Gateway |
| Brand voice | `/cp/brand-voice` (GET/PATCH) | Mobile cannot view or update brand voice |
| Digital marketing activation | `/api/v1/hired-agents/{id}/digital-marketing-activation`, `/generate-theme-plan` | ✅ Implemented in Wave 1 — DMA flows via Plant Gateway |
| Profile | `/cp/profile` (GET/PATCH) | Mobile cannot view or edit profile |
| Platform credentials | `/cp/platform-credentials` (GET/POST) | Mobile cannot manage provider credentials |
| Subscriptions | `/cp/subscriptions/`, `.../cancel` | Mobile cannot list or cancel subscriptions |
| Hiring wizard | `/cp/hire/wizard/draft`, `/finalize`, `/by-subscription` | Mobile has different hiring approach |
| YouTube finalize | `/cp/youtube-connections/connect/finalize` | Mobile missing OAuth finalize step |
| YouTube list | `/cp/youtube-connections` (GET) | Mobile missing connection listing |
| Payment config | `/cp/payments/config` (GET) | Mobile missing Razorpay config |
| Coupon checkout | `/cp/payments/coupon/checkout` (POST) | Mobile missing coupon support |
| Trading | `/cp/trading-strategy`, `/cp/trading/draft-plan`, `/cp/trading/approve-execute` | Mobile missing entire trading feature set |

---

## 5. Architecture Observation

The mobile app now uses a single API client:

- **`apiClient`** → Plant Gateway (`/api/v1/...` and `/auth/...`)
- ~~**`cpApiClient`** → CP Backend~~ — **removed in Wave 1+2 migration (2026-04-xx)**

CP Frontend still routes through the gateway which proxies to CP Backend or Plant.
Mobile is now fully Plant Gateway-native; `cpApiClient` has zero production references remaining.

---

## 6. Remediation Priority

| Priority | Action | Effort |
|---|---|---|
| **P0** | Consolidate payment endpoints — single create-order + verify path | 1 sprint |
| **P1** | Standardize skills/job-roles URL prefix (drop `/genesis/`) | 1 story |
| **P1** | Consolidate Google Auth verify to single canonical endpoint | 1 story |
| **P2** | Add mobile-only endpoints (refund, status) to CP if needed | 2 stories |
| **P3** | Close mobile feature gaps (goals, brand voice, etc.) | Multi-sprint |

---

## 7. CP → Plant Gateway Migration Log (Wave 1 + 2, 2026-04-xx)

All `cpApiClient` calls have been removed from production mobile code. Every route now calls Plant Gateway directly via `apiClient`.

| Route | Before (CP Backend) | After (Plant Gateway) |
|---|---|---|
| My agents list | `GET /cp/my-agents/summary` | `GET /api/v1/hired-agents/by-customer/{customerId}` |
| By-subscription | `GET /cp/hired-agents/by-subscription/{id}` | `GET /api/v1/hired-agents/by-subscription/{id}` |
| Deliverables / approval queue | `/cp/hired-agents/{id}/approval-queue` | `GET /api/v1/hired-agents/{id}/deliverables?status=pending_review` |
| Approve / Reject | `/cp/.../approve\|reject` | `POST /api/v1/deliverables/{id}/review` with `{decision}` |
| Skills, pause, resume | `/cp/hired-agents/{id}/...` | `/api/v1/hired-agents/{id}/...` |
| Goal config PATCH | `/goal-config` body `{goal_config}` | `/customer-config` body `{customer_fields}` |
| DMA activation | `/cp/digital-marketing-activation/{id}` | `/api/v1/hired-agents/{id}/digital-marketing-activation` |
| Marketing drafts | `/cp/marketing/...` | `/api/v1/marketing/...` |
| Platform connections / YouTube OAuth | `/cp/hired-agents/{id}/platform-connections`, `/cp/youtube-connections/connect/start` | `/api/v1/hired-agents/{id}/platform-connections`, `/api/v1/customer-platform-connections/youtube/connect/start` |
| Invoices / Receipts | `/cp/invoices`, `/cp/receipts` | `/api/v1/invoices`, `/api/v1/receipts` (Gateway auto-injects `customer_id` from JWT) |
| Content recommendations | `/cp/content-recommendations/{id}` | `/api/v1/hired-agents/{id}/content-recommendations` |

### Bugs discovered and fixed during audit

| Bug | Old behaviour | Fix |
|---|---|---|
| `fetchDeliverable` single GET | CP route `/cp/approval-queue/{deliverableId}` never existed in CP or Plant — would 404 | Replaced with Plant list `GET /api/v1/hired-agents/{id}/deliverables` + client-side `.find(d => d.id === deliverableId)` |
| `rejectDraftPost` | CP wrote rejection to `FileCPApprovalStore` (local file) — invisible to Plant DB | Now calls Plant directly: `POST /api/v1/marketing/draft-posts/{postId}/reject` |
