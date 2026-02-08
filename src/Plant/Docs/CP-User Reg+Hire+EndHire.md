# CP User Journeys — Registration + Hire Agent + End Hiring

**Scope**: Customer Portal (CP) user journeys for (1) user registration, (2) hiring an agent (with payment + trial + configuration wizard), and (3) ending an agent hire at next billing cycle.

**Design constraints**
- Keep registration fields to **10 max** at signup; collect additional business/profile details later.
- Stories must be independently pickable and specify work across **CP**, **Plant**, and **Gateway**.
- Security requirements: **OTP (email/phone)**, **2FA**, **CAPTCHA**, optional **Google auth** prefill.

## Environment URLs (confirmed)

| Environment | CP Frontend (customer portal) | CP API base (single-door) |
|---|---|---|
| Production | https://cp.waooaw.com | https://cp.waooaw.com/api |
| Demo / lower env | https://cp.demo.waooaw.com/ | https://cp.demo.waooaw.com/api |

**API_PROD_URL derivation**: treated as CP origin + `/api` so CP FE never calls Plant directly; CP backend/gateway can route internally to Plant/Gateway services.

## Single source-of-truth (payments gating)

To avoid mismatches between UI and API behavior, **the backend is the source-of-truth** for which payment flow is enabled.

| Environment | `PAYMENTS_MODE` (server) | Allowed flow |
|---|---|---|
| Production | `razorpay` | Razorpay only (no coupon UI, coupon rejected server-side) |
| Demo / UAT / Dev (codespaces) | `coupon` | Coupon only (`WAOOAW100`), Razorpay disabled |

**Contract**
- CP Backend exposes `GET /cp/payments/config` returning `{ mode: "razorpay" | "coupon" }`.
- CP Frontend uses this response to decide which UI to render.
- CP Backend must enforce the mode server-side (never trust frontend gating).

## Execution log (completed stories)

- ✅ 2026-02-07: Payments mode config endpoint + tests (CP backend: [src/CP/BackEnd/api/payments_config.py](src/CP/BackEnd/api/payments_config.py), [src/CP/BackEnd/tests/test_payments_config_routes.py](src/CP/BackEnd/tests/test_payments_config_routes.py); CP frontend: [src/CP/FrontEnd/src/services/paymentsConfig.service.ts](src/CP/FrontEnd/src/services/paymentsConfig.service.ts), [src/CP/FrontEnd/src/__tests__/paymentsConfig.service.test.ts](src/CP/FrontEnd/src/__tests__/paymentsConfig.service.test.ts)).
- ✅ 2026-02-07: CP frontend prefetches payment mode via provider for future Hire flow gating (context: [src/CP/FrontEnd/src/context/PaymentsConfigContext.tsx](src/CP/FrontEnd/src/context/PaymentsConfigContext.tsx), test: [src/CP/FrontEnd/src/__tests__/PaymentsConfigContext.test.tsx](src/CP/FrontEnd/src/__tests__/PaymentsConfigContext.test.tsx)).
- ✅ 2026-02-07: Coupon-only checkout skeleton (CP backend route: [src/CP/BackEnd/api/payments_coupon.py](src/CP/BackEnd/api/payments_coupon.py), tests: [src/CP/BackEnd/tests/test_payments_coupon_routes.py](src/CP/BackEnd/tests/test_payments_coupon_routes.py); CP frontend service: [src/CP/FrontEnd/src/services/couponCheckout.service.ts](src/CP/FrontEnd/src/services/couponCheckout.service.ts), test: [src/CP/FrontEnd/src/__tests__/couponCheckout.service.test.ts](src/CP/FrontEnd/src/__tests__/couponCheckout.service.test.ts)).
- ✅ 2026-02-07: BookingModal uses payments mode config and triggers coupon checkout in `coupon` mode (UI: [src/CP/FrontEnd/src/components/BookingModal.tsx](src/CP/FrontEnd/src/components/BookingModal.tsx), test: [src/CP/FrontEnd/src/test/BookingModal.test.tsx](src/CP/FrontEnd/src/test/BookingModal.test.tsx)).
- ✅ 2026-02-07: REG-1.1 registration UI (10 fields max) in AuthModal with cancel + consent gating (UI: [src/CP/FrontEnd/src/components/auth/AuthModal.tsx](src/CP/FrontEnd/src/components/auth/AuthModal.tsx), test: [src/CP/FrontEnd/src/test/AuthModalRegistration.test.tsx](src/CP/FrontEnd/src/test/AuthModalRegistration.test.tsx)).
- ✅ 2026-02-07: REG-1.2 CAPTCHA required for registration (Cloudflare Turnstile; env: `VITE_TURNSTILE_SITE_KEY`) (widget: [src/CP/FrontEnd/src/components/auth/CaptchaWidget.tsx](src/CP/FrontEnd/src/components/auth/CaptchaWidget.tsx), UI+tests: [src/CP/FrontEnd/src/components/auth/AuthModal.tsx](src/CP/FrontEnd/src/components/auth/AuthModal.tsx), [src/CP/FrontEnd/src/test/AuthModalRegistration.test.tsx](src/CP/FrontEnd/src/test/AuthModalRegistration.test.tsx); Vitest stubs `window.turnstile` to avoid loading external scripts).
- ✅ 2026-02-07: REG-1.3 registration API + validation (route: [src/CP/BackEnd/api/cp_registration.py](src/CP/BackEnd/api/cp_registration.py), store: [src/CP/BackEnd/services/cp_registrations.py](src/CP/BackEnd/services/cp_registrations.py), tests: [src/CP/BackEnd/tests/test_cp_registration_routes.py](src/CP/BackEnd/tests/test_cp_registration_routes.py)).
- ✅ 2026-02-08: REG-1.4 OTP issuance + verify (rate-limited + audit-log JSONL; non-prod returns OTP code for demo/testing) (routes: [src/CP/BackEnd/api/cp_otp.py](src/CP/BackEnd/api/cp_otp.py), store: [src/CP/BackEnd/services/cp_otp.py](src/CP/BackEnd/services/cp_otp.py), tests: [src/CP/BackEnd/tests/test_cp_otp_routes.py](src/CP/BackEnd/tests/test_cp_otp_routes.py); CP frontend wiring: [src/CP/FrontEnd/src/services/otp.service.ts](src/CP/FrontEnd/src/services/otp.service.ts), [src/CP/FrontEnd/src/components/auth/AuthModal.tsx](src/CP/FrontEnd/src/components/auth/AuthModal.tsx), [src/CP/FrontEnd/src/test/AuthModalRegistration.test.tsx](src/CP/FrontEnd/src/test/AuthModalRegistration.test.tsx)).
- ✅ 2026-02-08: REG-1.5 Plant customer account entity + persistence (Customer model/schema/service/API + migration) (Plant: [src/Plant/BackEnd/models/customer.py](src/Plant/BackEnd/models/customer.py), [src/Plant/BackEnd/schemas/customer.py](src/Plant/BackEnd/schemas/customer.py), [src/Plant/BackEnd/services/customer_service.py](src/Plant/BackEnd/services/customer_service.py), [src/Plant/BackEnd/api/v1/customers.py](src/Plant/BackEnd/api/v1/customers.py), [src/Plant/BackEnd/database/migrations/versions/008_customer_entity.py](src/Plant/BackEnd/database/migrations/versions/008_customer_entity.py), test: [src/Plant/BackEnd/tests/unit/test_customer_schemas.py](src/Plant/BackEnd/tests/unit/test_customer_schemas.py)).
- ✅ 2026-02-08: REG-1.6 Gateway auth passthrough + anti-abuse header for customer registration calls (Plant Gateway requires `X-CP-Registration-Key` for `/api/v1/customers`; CP syncs customer to Plant on OTP verify) (Gateway: [src/Plant/Gateway/middleware/auth.py](src/Plant/Gateway/middleware/auth.py); CP: [src/CP/BackEnd/api/cp_otp.py](src/CP/BackEnd/api/cp_otp.py), test: [src/CP/BackEnd/tests/test_cp_otp_routes.py](src/CP/BackEnd/tests/test_cp_otp_routes.py)).
- ✅ 2026-02-08: REG-1.7 2FA enrollment + challenge (TOTP) (CP: endpoints under `/api/auth/2fa/*` + Google login enforcement when enabled) (service: [src/CP/BackEnd/services/cp_2fa.py](src/CP/BackEnd/services/cp_2fa.py), routes: [src/CP/BackEnd/api/auth/routes.py](src/CP/BackEnd/api/auth/routes.py), test: [src/CP/BackEnd/tests/test_2fa_totp.py](src/CP/BackEnd/tests/test_2fa_totp.py)).
- ✅ 2026-02-08: REG-1.8 Google auth prefill for registration (decode Google credential and prefill name/email; user can edit before submit) (button: [src/CP/FrontEnd/src/components/auth/GoogleLoginButton.tsx](src/CP/FrontEnd/src/components/auth/GoogleLoginButton.tsx), UI: [src/CP/FrontEnd/src/components/auth/AuthModal.tsx](src/CP/FrontEnd/src/components/auth/AuthModal.tsx), test: [src/CP/FrontEnd/src/test/AuthModalRegistration.test.tsx](src/CP/FrontEnd/src/test/AuthModalRegistration.test.tsx)).
- ✅ 2026-02-08: REG-1.9 Plant security logging + throttles (throttle by IP+email on customer upsert; append-only security audit store) (Plant: [src/Plant/BackEnd/api/v1/customers.py](src/Plant/BackEnd/api/v1/customers.py), [src/Plant/BackEnd/services/security_throttle.py](src/Plant/BackEnd/services/security_throttle.py), [src/Plant/BackEnd/services/security_audit.py](src/Plant/BackEnd/services/security_audit.py), test: [src/Plant/BackEnd/tests/unit/test_security_throttle_customers.py](src/Plant/BackEnd/tests/unit/test_security_throttle_customers.py)).
- ✅ 2026-02-08: AUTH-1.1 Login UI + session restore (Google OAuth + OTP login support; restores session after refresh) (CP backend OTP login start: [src/CP/BackEnd/api/cp_otp.py](src/CP/BackEnd/api/cp_otp.py), test: [src/CP/BackEnd/tests/test_cp_otp_login_routes.py](src/CP/BackEnd/tests/test_cp_otp_login_routes.py); CP frontend: [src/CP/FrontEnd/src/components/auth/AuthModal.tsx](src/CP/FrontEnd/src/components/auth/AuthModal.tsx), [src/CP/FrontEnd/src/App.tsx](src/CP/FrontEnd/src/App.tsx), [src/CP/FrontEnd/src/services/otp.service.ts](src/CP/FrontEnd/src/services/otp.service.ts), [src/CP/FrontEnd/src/services/auth.service.ts](src/CP/FrontEnd/src/services/auth.service.ts), test: [src/CP/FrontEnd/src/test/App.test.tsx](src/CP/FrontEnd/src/test/App.test.tsx)).
- ✅ 2026-02-08: AUTH-1.2 Token issuance + logout refresh revocation (refresh tokens are rejected after logout via CP-local JSONL revocation store) (CP: [src/CP/BackEnd/api/auth/routes.py](src/CP/BackEnd/api/auth/routes.py), [src/CP/BackEnd/api/auth/dependencies.py](src/CP/BackEnd/api/auth/dependencies.py), [src/CP/BackEnd/services/cp_refresh_revocations.py](src/CP/BackEnd/services/cp_refresh_revocations.py), test: [src/CP/BackEnd/tests/test_google_oauth_integration.py](src/CP/BackEnd/tests/test_google_oauth_integration.py)).
- ✅ 2026-02-08: AUTH-1.3 Plant customer auth source-of-truth (enforce unique phone; 409 conflict + audit for duplicate phone; token validation endpoint with auth audit events) (Plant: [src/Plant/BackEnd/database/migrations/versions/009_customer_unique_phone.py](src/Plant/BackEnd/database/migrations/versions/009_customer_unique_phone.py), [src/Plant/BackEnd/models/customer.py](src/Plant/BackEnd/models/customer.py), [src/Plant/BackEnd/services/customer_service.py](src/Plant/BackEnd/services/customer_service.py), [src/Plant/BackEnd/api/v1/customers.py](src/Plant/BackEnd/api/v1/customers.py), [src/Plant/BackEnd/api/v1/auth.py](src/Plant/BackEnd/api/v1/auth.py), tests: [src/Plant/BackEnd/tests/unit/test_customers_duplicate_phone.py](src/Plant/BackEnd/tests/unit/test_customers_duplicate_phone.py), [src/Plant/BackEnd/tests/unit/test_auth_validate.py](src/Plant/BackEnd/tests/unit/test_auth_validate.py)).
- ✅ 2026-02-08: AUTH-1.4 Gateway auth middleware + customer context (rate-limit `/api/v1/auth/*`; when `customer_id` missing, validate with Plant `/api/v1/auth/validate` and inject normalized `customer_id`/email into `request.state`) (Gateway: [src/Plant/Gateway/middleware/auth.py](src/Plant/Gateway/middleware/auth.py), tests: [src/Plant/Gateway/middleware/tests/test_auth.py](src/Plant/Gateway/middleware/tests/test_auth.py)).
- ✅ 2026-02-08: HIRE-1.1 Hire entry points from landing + portal (landing CTAs route to `/discover`; unauthenticated users are redirected into AuthModal and returned to intended hire path; portal “+ Hire New Agent” and “Hire Another Agent” route to `/discover`) (CP frontend: [src/CP/FrontEnd/src/App.tsx](src/CP/FrontEnd/src/App.tsx), [src/CP/FrontEnd/src/components/Header.tsx](src/CP/FrontEnd/src/components/Header.tsx), [src/CP/FrontEnd/src/sections/HeroSection.tsx](src/CP/FrontEnd/src/sections/HeroSection.tsx), [src/CP/FrontEnd/src/sections/CTASection.tsx](src/CP/FrontEnd/src/sections/CTASection.tsx), [src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx](src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx), [src/CP/FrontEnd/src/pages/authenticated/Dashboard.tsx](src/CP/FrontEnd/src/pages/authenticated/Dashboard.tsx); tests: [src/CP/FrontEnd/src/test/App.test.tsx](src/CP/FrontEnd/src/test/App.test.tsx), [src/CP/FrontEnd/src/test/MyAgents.test.tsx](src/CP/FrontEnd/src/test/MyAgents.test.tsx), [src/CP/FrontEnd/src/test/Dashboard.test.tsx](src/CP/FrontEnd/src/test/Dashboard.test.tsx)).

## Product-owner readiness review (gaps bridged)

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| Missing shared definitions (trial start, configured, subscription states) | Conflicting implementations across CP/Plant/Gateway | Add a single “Definitions & States” section and require all stories to reference it |
| Auth flow unspecified beyond registration (login/session/logout) | Users can register but not reliably return/resume journey | Add `AUTH-1` epic for login + session management |
| Payment edge cases not described (webhook retries, idempotency, retry UX) | Double-charges, orphan subscriptions, inconsistent UI | Add idempotency + reconciliation + retry stories under `HIRE-2` |
| No transactional notifications defined | Users lack trust/clarity; support burden increases | Add `NOTIF-1` epic for OTP/receipt/trial/cancel notifications |
| GST/invoicing intent unclear | Compliance risk and billing confusion | Add `BILL-1` epic to separate “collect GST” vs “issue GST invoice” |
| Retention rules after cancel not stated | Disputes about access/deliverables post-cancel | Add explicit retention policy stories under `END-1` |

---

## Definitions & States (source-of-truth for all stories)

### Key entities
- **Customer**: a human user + a business profile.
- **Subscription**: the paid relationship for a specific agent (or agent instance) with a billing cycle.
- **Hired agent instance**: a customer-scoped instance of an agent with configuration and lifecycle state.

### Subscription status (minimum)
- `pending_payment` → `active` → (`cancel_at_period_end`) → `ended`
- `payment_failed` (recoverable; customer can retry)

### Trial status (minimum)
- `not_started` (paid but not configured)
- `active` (trial clock running)
- `ended_converted` / `ended_not_converted`

### Trial start rule (explicit)
Trial starts only when ALL are true:
1) payment is confirmed (`active` subscription)
2) hired agent instance is **configured**
3) customer completed **goal setting** step for that agent

### Configuration completeness
An agent instance is `configured=true` only if all required agent-specific fields validate and secrets are stored.

---

## Goal 1 — User Registration

### Proposed registration fields (10 max)
The intent is “just enough” to create an account + anchor the business for billing, compliance, and later onboarding.

| Field | Why it matters | Source / notes |
|---|---|---|
| Full name | Account owner identity | Google auth can prefill |
| Business name | Billing + account grouping | Manual |
| Business industry | Agent recommendations + analytics | Use controlled enum |
| Business address (city/state/country) | Tax + invoices + compliance | Keep as single string initially |
| Email | Login + OTP | Google auth can prefill |
| Phone number | OTP + recovery | E.164 formatting |
| Website (optional) | Helps agent personalization | Optional |
| GST number (optional) | India invoicing/compliance | Validate format; optional |
| Preferred contact method (email/phone) | OTP delivery + comms | Default email |
| Consent (TOS/Privacy checkbox) | Legal compliance | Required |

**Deferred fields (post-signup profile)**: company size, role/title, marketing channels, trading risk profile, time zone, billing address split, etc.

### Epic REG-1: Secure registration + identity verification
**Outcome**: Customer can register, verify via OTP, and sign in securely.

#### Stories (independently pickable)

| Story ID | Component | Summary | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| REG-1.1 | CP Frontend | Registration UI (10 fields) with cancel/exit | Shows 10 fields max; cancel returns to landing; client-side validation; TOS consent required | None |
| REG-1.2 | CP Frontend | CAPTCHA on registration | CAPTCHA required to submit registration; failure blocks submit; accessible fallback | CAPTCHA provider selection/config |
| REG-1.3 | CP Backend | Registration API + validation | POST `/cp/auth/register` validates fields, normalizes email/phone; returns `registration_id` | DB/model layer in Plant or CP store decision |
| REG-1.4 | CP Backend | OTP issuance + verify (email/phone) | POST `/cp/auth/otp/start` sends OTP; POST `/cp/auth/otp/verify` verifies; rate limited; audit logged | Email/SMS provider integration |
| REG-1.5 | Plant | Customer account entity + persistence | Plant stores customer identity + business profile; supports lookup by email; idempotent create | Plant DB + schema changes (if not present) |
| REG-1.6 | Gateway | Auth passthrough + policy | Gateway routes CP registration calls to Plant; enforces auth/anti-abuse headers | Gateway routing |
| REG-1.7 | CP Backend | 2FA enrollment and challenge | Support 2FA (TOTP or SMS/email second factor) after OTP verification; enforce on login | Provider + secret storage |
| REG-1.8 | CP Frontend | Google auth prefill | If user uses Google OAuth, prefill name/email; user can edit before submit | OAuth client config |
| REG-1.9 | Plant | Security logging + throttles | Record OTP attempts, lockouts; configurable rate limits | Central logging |

### Epic AUTH-1: Login, session management, and logout (post-registration)
**Outcome**: Returning customers can sign in and resume hire/config/trial flows.

| Story ID | Component | Summary | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| AUTH-1.1 | CP Frontend | Login UI + session restore | Supports Google OAuth; supports OTP login if enabled; restores session after refresh | OAuth + OTP |
| AUTH-1.2 | CP Backend | Token issuance + logout | Issues access/refresh tokens; logout revokes refresh token; consistent 401/403 handling | Plant identity decision |
| AUTH-1.3 | Plant | Customer auth source-of-truth | Enforces unique email/phone; supports token validation; audit log for auth events | Plant DB |
| AUTH-1.4 | Gateway | Auth middleware + customer context | Validates tokens; injects `customer_id`; enforces rate limits for auth endpoints | Gateway auth |

### Notes on “Cancel registration”
- Treat cancel as **safe exit**: it should invalidate any in-progress `registration_id` and OTP session.
- Cancellation must not leave an account in “half-created” state; use a **pending** status until OTP verified.

---

## Goal 2 — Hiring an Agent (select → pay → trial → configure wizard)

### Epic HIRE-1: Agent selection + hire initiation
**Outcome**: Customer selects an agent and starts hiring flow from landing or after login.

| Story ID | Component | Summary | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| HIRE-1.1 | CP Frontend | Hire entry points from landing + portal | “Hire” available from landing and post-login; if not registered, redirect into registration and return to hire | REG-1.x |
| HIRE-1.2 | CP Frontend | Agent selection + duration selection UI | Customer selects agent + hire duration (e.g., monthly/quarterly) | Agent catalog endpoint |
| HIRE-1.3 | Plant | Agent catalog + pricing metadata | Plant exposes agent list incl. `trial_days`, allowed durations, price | Existing agent entities |
| HIRE-1.4 | Gateway | Catalog endpoint proxy | Gateway routes catalog calls; caches safely if needed | Gateway routing |

### Epic HIRE-2: Payment gateway + receipt + subscription creation
**Outcome**: Customer pays and a subscription is created; trial rules are established.

**Environment gating (must-have)**
- **Production**: Razorpay enabled.
- **Demo/lower env**: Razorpay disabled; hiring uses a **100% discount coupon** mechanism to simulate a “paid” subscription without contacting Razorpay.
- **UI rule**: Coupon entry is shown **only in demo/lower env**; production shows **no coupon UI** and rejects any coupon attempts.

**Single-door config endpoint (first story to execute)**
- `GET /api/cp/payments/config` returns `{ mode: "razorpay" | "coupon", coupon_code?, coupon_unlimited? }`.
- Mode is driven by `PAYMENTS_MODE` and guarded so production can never run in coupon mode.

| Story ID | Component | Summary | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| HIRE-2.1 | Plant | Payment intent + order creation | Create `order_id`, amount, currency, agent/duration; returns client payment data | Payment provider decision |
| HIRE-2.2 | Gateway | Payment endpoints routing | Gateway exposes `/payments/*` for CP; forwards to Plant securely | Gateway auth |
| HIRE-2.3 | CP Frontend | Payment UI + confirmation | Checkout UI; handles success/failure; shows receipt page with `order_id` | HIRE-2.1 |
| HIRE-2.4 | Plant | Webhook processing + receipt issuance | Payment webhook verifies signature; marks paid; issues receipt | Provider webhooks |
| HIRE-2.5 | Plant | Subscription + billing cycle state machine | After paid, create subscription with next billing date; store `trial_days` | Billing schema |
| HIRE-2.6 | Plant | Trial start rules | Trial does **not** start on payment; starts when config+goals complete; store `trial_start_at` when activated | HIRE-3.x |
| HIRE-2.7 | Plant | Payment idempotency + reconciliation | Payment-init accepts idempotency key; webhook retries are safe; reconcile “paid but no subscription” | Provider webhooks |
| HIRE-2.8 | CP Frontend | Payment failure + retry UX | If payment fails, user can retry without duplicate subscription/order; clear error state | HIRE-2.7 |
| HIRE-2.9 | Plant | Receipt/invoice artifacts API | Provide receipt always; invoice behind flag; CP can download by `order_id` | BILL-1 |

#### Razorpay specifics (production)
- Checkout creates a Razorpay order on the server side; CP only receives non-secret order details required by Razorpay Checkout.
- Webhook endpoint must verify signatures using the Razorpay webhook secret; webhook retries must be idempotent.

#### Coupon specifics (demo/lower env)
- Coupon code **WAOOAW100** produces a “paid via coupon” order with total ₹0 and creates the subscription exactly like a paid order.
- Coupon is **unlimited use** (no per-user/per-day limits), but must be **environment-limited** to **demo**, **uat**, and **dev/codespaces** so it cannot be used in production.

### Epic HIRE-3: Post-payment configuration wizard (agent-specific)
**Outcome**: After payment, customer completes agent configuration wizard; trial starts only after completion.

#### Wizard common steps (all agents)
- Step 1: Agent nickname (customer-defined)
- Step 2: Color theme selection (limited palette)
- Step 3: Agent-specific configuration
- Step 4: Confirm + “Activate trial”

| Story ID | Component | Summary | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| HIRE-3.1 | CP Frontend | Wizard shell + progress + resume | Wizard persists progress; can resume after logout; shows required vs optional fields | Storage approach |
| HIRE-3.2 | CP Backend | Config draft + finalize APIs | Save draft config; finalize config triggers Plant activation event | Plant config endpoints |
| HIRE-3.3 | Plant | Store hired agent instance + config | Create “hired instance” tied to customer; store config; mark `configured=true` | Subscription exists |
| HIRE-3.4 | Plant | Activation triggers + trial start | When config finalized, set `trial_start_at=now`; emit event to agent runtime | Event system |
| HIRE-3.5 | Gateway | Config endpoint routing + auth | Gateway forwards config; enforces customer ownership | Authz rules |

### Epic TRIAL-1: Trial lifecycle visibility and conversion
**Outcome**: Customer sees trial activation status and countdown, and understands conversion behavior.

| Story ID | Component | Summary | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| TRIAL-1.1 | Plant | Trial status API | Returns trial state and timestamps; consistent with “Definitions & States” | Definitions & States |
| TRIAL-1.2 | CP Frontend | Trial banner + countdown | Shows “Trial will start after setup” vs countdown when active | TRIAL-1.1 |
| TRIAL-1.3 | Plant | Trial end handling | At trial end, apply the chosen conversion rule (open question #6) | Payment provider |

#### Agent-specific configuration stories

**Share Trading**
| Story ID | Component | Summary | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| HIRE-3.ST1 | CP Frontend | Trading config step UI | Collect exchange name (eDelta India), coin(s), interval, API key/secret; validates required fields | None |
| HIRE-3.ST2 | CP Backend | Encrypted secret storage | Store exchange secrets encrypted at rest; never return secrets in API responses | Key management |
| HIRE-3.ST3 | Plant | Trading config validation | Plant validates supported exchanges/intervals/coins; rejects invalid combos | Trading domain rules |

**Digital Marketing**
| Story ID | Component | Summary | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| HIRE-3.DM1 | CP Frontend | Marketing platform selection UI | Select platforms (e.g., LinkedIn/X/Instagram); enter required credentials/keys per platform | Platform list |
| HIRE-3.DM2 | CP Backend | Encrypted credential storage | Store platform tokens/keys encrypted; rotate/update allowed | Key management |
| HIRE-3.DM3 | Plant | Marketing config validation | Plant validates platform requirements; marks config complete only when required credentials exist | Marketing rules |

---

## Goal 3 — End Agent Hiring (cancel next billing cycle)

### Epic END-1: Cancel subscription effective next cycle
**Outcome**: Customer can end hiring; billing stops next cycle; agent remains active until cycle boundary.

| Story ID | Component | Summary | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| END-1.1 | CP Frontend | “End Hire” UI + confirmation | Customer sees current plan, next billing date, and effect of cancel; requires confirmation | Subscription status API |
| END-1.2 | CP Backend | Cancel request endpoint | POST `/cp/subscriptions/{id}/cancel` sets `cancel_at_period_end=true` | Plant supports cancel state |
| END-1.3 | Plant | Subscription cancel-at-period-end logic | Updates subscription; prevents future charges; keeps service active until `period_end` | Billing state machine |
| END-1.4 | Plant | Deactivation at period boundary | At `period_end`, deactivates hired agent instance; emits deactivation event | Scheduler/cron |
| END-1.5 | Gateway | Cancel routing + authz | Ensure only subscription owner can cancel; audit log | Authz rules |
| END-1.6 | CP Frontend | Post-cancel UX | Shows “Scheduled to end on <date>”; allows undo until cutoff (optional) | Decide on undo |

| END-1.7 | Plant | Retention policy + enforcement | Define and enforce what remains accessible after end (deliverables/history/export) | Policy decision |
| END-1.8 | CP Frontend | Retention messaging | Show retention rules on cancel confirmation and after cancel | END-1.7 |

---

## Cross-cutting epic: Transactional notifications

### Epic NOTIF-1: Email/SMS notifications
**Outcome**: Users receive confirmations and status changes that match CP UI.

| Story ID | Component | Summary | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| NOTIF-1.1 | Plant | Notification event schema | Emit events for OTP sent/verified, payment success/fail, trial activated, cancel scheduled/effective | Event system |
| NOTIF-1.2 | Plant | Email provider integration | Sends transactional emails; templates versioned; env configurable | Provider decision |
| NOTIF-1.3 | Plant | SMS provider integration (optional) | If enabled, send OTP and critical alerts; feature flagged by env | OTP scope decision |
| NOTIF-1.4 | CP Frontend | Resend OTP UX + cooldown | “Resend OTP” available with cooldown; clear messaging | REG-1.4 |

---

## Cross-cutting epic: Billing, GST, and invoices

### Epic BILL-1: Billing artifacts and GST handling
**Outcome**: Billing is understandable and compliant for demo/production targets.

| Story ID | Component | Summary | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| BILL-1.1 | Plant | Separate “collect GST” vs “issue GST invoice” | GST field can ship without enabling GST invoice formatting | GST requirement |
| BILL-1.2 | Plant | Invoice metadata (optional) | When enabled, invoices include GSTIN and tax breakdown | Compliance |
| BILL-1.3 | CP Frontend | Billing history UX | Shows receipts/invoices list with download links and next billing date | HIRE-2.9 |

---

## Cross-cutting architecture decisions (must be made early)

| Decision | Options | Impact | Best possible solution/fix |
|---|---|---|---|
| Where customer identity lives | Plant DB vs CP local store | Affects auth, billing, audit | Put source-of-truth in Plant; CP is UI + thin API layer |
| OTP provider | Email only vs SMS+Email | Delivery + cost + reliability | Start with email OTP, add SMS behind feature flag |
| 2FA method | TOTP vs SMS | Security strength | Prefer TOTP; allow fallback SMS/email for MVP |
| CAPTCHA provider | reCAPTCHA/hCaptcha/etc | Bot mitigation | Choose one provider and wrap behind interface |
| Payments | Razorpay/Stripe/etc | Billing + webhooks | Use provider with strong webhook tooling; implement signature verification |
| Payment env gating | Razorpay in prod; coupon in non-prod | Prevent accidental live charges in demo | Feature-flag Razorpay by environment; enforce “coupon-only” checkout in lower env |
| Secret storage | KMS vs app-level encryption | Compliance | Use KMS where available; otherwise Fernet + rotation plan |

---

## Delivery plan (phased, independently shippable)

### Phase 1 — Registration foundation
- REG-1.1, REG-1.3, REG-1.4, REG-1.8 (minimal but secure)

### Phase 1b — Returning user usability
- AUTH-1.1 → AUTH-1.4

### Phase 2 — Hire + payment
- HIRE-1.1 → HIRE-2.5 (end-to-end paid subscription created)

### Phase 2b — Payment reliability + notifications
- HIRE-2.7, HIRE-2.8, NOTIF-1.1, NOTIF-1.2

### Phase 3 — Configuration wizard + trial start rule
- HIRE-3.1 → HIRE-3.4 plus agent-specific steps (ST/DM)

### Phase 3b — Trial visibility
- TRIAL-1.1, TRIAL-1.2

### Phase 4 — End hire
- END-1.1 → END-1.4

### Phase 4b — Retention clarity
- END-1.7, END-1.8

---

## Open questions (need answers to finalize stories)
1) Payment provider preference (Razorpay vs Stripe vs other)?
2) OTP scope: email-only MVP acceptable, or must support SMS day-1?
3) 2FA: TOTP acceptable as primary, or must be SMS?
4) Do we need GST invoicing day-1 for demo, or can GST be collected but invoices simplified?
5) Should “undo cancel” be supported (END-1.6), or keep it out for MVP?

6) Trial end rule: auto-convert to paid (continue billing) vs require explicit confirmation to continue?
7) Do we need proration for upgrades/downgrades mid-cycle (out of scope for MVP unless required)?
