# Iteration 1 — Auth Foundation

**When:** Before login screen ships  
**Branch naming:** `feat/auth-foundation-it1`  
**Testing:** `docker compose -f docker-compose.local.yml` — no virtual env, no local Python  
**Status:** � Complete — merged [PR #768](https://github.com/dlai-sd/WAOOAW/pull/768)

---

## Tracking Table

| # | Epic | Story | Status | PR |
|---|------|-------|--------|----|
| E1-S1 | JWT Refresh | Implement refresh token issuance on login | 🟢 Done | [#768](https://github.com/dlai-sd/WAOOAW/pull/768) |
| E1-S2 | JWT Refresh | Store refresh token in httpOnly cookie | 🟢 Done | [#768](https://github.com/dlai-sd/WAOOAW/pull/768) |
| E1-S3 | JWT Refresh | Silent refresh endpoint | 🟢 Done | [#768](https://github.com/dlai-sd/WAOOAW/pull/768) |
| E1-S4 | JWT Refresh | Frontend silent refresh logic | 🟢 Done | [#768](https://github.com/dlai-sd/WAOOAW/pull/768) |
| E2-S1 | Token Revocation | Redis revocation list on logout | 🟢 Done | [#768](https://github.com/dlai-sd/WAOOAW/pull/768) |
| E2-S2 | Token Revocation | Check revocation on every authenticated request | 🟢 Done | [#768](https://github.com/dlai-sd/WAOOAW/pull/768) |
| E2-S3 | Token Revocation | Revoke all tokens on password reset | 🟢 Done | [#768](https://github.com/dlai-sd/WAOOAW/pull/768) |

**Story Status Key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done

---

## Epic 1 — JWT Refresh Token Strategy

**Goal:** Users are never unexpectedly logged out. Access tokens expire after 15 minutes but are silently refreshed using a secure httpOnly cookie holding the refresh token. This must be implemented before the login screen ships.

**Context:**  
Currently, if a JWT expires the user gets a 401 and must log in again. This is poor UX and a security gap (long-lived access tokens are the common workaround — worse). The correct pattern: short-lived access token (15 min) + long-lived refresh token (7 days) stored in httpOnly cookie (not localStorage — prevents XSS token theft).

---

### E1-S1 — Implement refresh token issuance on login

**Story:**  
As the Plant backend, when a user successfully logs in, I issue both an access token and a refresh token so the frontend can silently renew access without re-login.

**Acceptance Criteria:**
- Login endpoint returns `access_token` (JWT, 15 min expiry) in the JSON response body
- Login endpoint also sets a `refresh_token` cookie (httpOnly, Secure, SameSite=Strict, 7 days expiry)
- Refresh token is a signed JWT containing: `sub` (user_id), `jti` (unique token ID), `exp` (7 days)
- `jti` is stored in Redis with TTL of 7 days — this is the revocation record
- Refresh token is NOT returned in the JSON body — only via cookie

**Technical Implementation Notes:**
- File to modify: `src/Plant/BackEnd/api/v1/auth.py` — login endpoint
- Add `generate_refresh_token(user_id)` to `src/Plant/BackEnd/core/security.py`
- Redis key pattern: `refresh_token:{jti}` = `user_id`, TTL = 604800 seconds (7 days)
- Use `httpx` Redis client already in docker-compose — connection via `REDIS_URL` env var
- Cookie settings: `httponly=True`, `secure=True`, `samesite="strict"`, `max_age=604800`
- Set cookie via `response.set_cookie(...)` in FastAPI — requires `Response` parameter injection

**Test Cases:**
```
TC-E1-S1-1: POST /api/v1/auth/login with valid credentials
  → HTTP 200
  → Body contains access_token (JWT, decodable, exp = now + 15 min)
  → Response headers contain Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict
  → refresh_token cookie NOT in body

TC-E1-S1-2: POST /api/v1/auth/login with invalid credentials
  → HTTP 401
  → No Set-Cookie header

TC-E1-S1-3: Decode refresh_token JWT from cookie
  → Contains sub = user_id
  → Contains jti (UUID)
  → exp = now + 7 days

TC-E1-S1-4: Check Redis after successful login
  → Key refresh_token:{jti} exists
  → TTL is approximately 604800 seconds
```

**Status:** 🟢 Done — PR #768

---

### E1-S2 — Store refresh token in httpOnly cookie

**Story:**  
As the frontend, I never have access to the refresh token value in JavaScript — it lives only in a httpOnly cookie managed by the browser — so XSS attacks cannot steal it.

**Acceptance Criteria:**
- Cookie is set with `HttpOnly` flag — not readable by `document.cookie`
- Cookie is set with `Secure` flag — only sent over HTTPS
- Cookie is set with `SameSite=Strict` — not sent on cross-site requests
- Cookie path is `/api/v1/auth` — scoped, not sent on every request
- Frontend JS code never reads, stores, or logs the refresh token

**Technical Implementation Notes:**
- This is enforced by the backend cookie settings in E1-S1 — no separate code needed on backend
- Frontend: audit `src/CP/FrontEnd/src/` for any code that reads `document.cookie` for tokens — must not exist
- Frontend: access token stored in memory (React state/context) only — not localStorage, not sessionStorage
- On page refresh: access token is lost from memory → triggers silent refresh automatically (E1-S4)

**Test Cases:**
```
TC-E1-S2-1: After login, attempt to read refresh_token via document.cookie in browser console
  → Returns empty string (HttpOnly cookie not accessible to JS)

TC-E1-S2-2: Inspect Set-Cookie header on login response
  → Flags present: HttpOnly, Secure, SameSite=Strict
  → Path=/api/v1/auth

TC-E1-S2-3: Send a request from a different origin
  → SameSite=Strict prevents cookie from being sent cross-site
```

**Status:** 🟢 Done — PR #768

---

### E1-S3 — Silent refresh endpoint

**Story:**  
As the Plant backend, I expose a `/auth/refresh` endpoint that accepts the refresh token cookie and returns a new access token, so the frontend can renew silently without user interaction.

**Acceptance Criteria:**
- `POST /api/v1/auth/refresh` — no body required, reads refresh token from httpOnly cookie
- Validates refresh token JWT: signature, expiry, `jti` exists in Redis (not revoked)
- Returns new `access_token` (15 min) in JSON body
- Optionally rotates the refresh token (issues new cookie, invalidates old `jti` in Redis) — rotation is the more secure pattern
- Returns HTTP 401 if refresh token is missing, expired, or revoked

**Technical Implementation Notes:**
- File: `src/Plant/BackEnd/api/v1/auth.py` — add `POST /refresh` route
- Read cookie: `request.cookies.get("refresh_token")`
- Validate: decode JWT, check `jti` in Redis (`EXISTS refresh_token:{jti}`)
- Rotation: delete old `refresh_token:{jti}` from Redis, generate new refresh token, set new cookie
- This endpoint must be in the public path list (`_is_public_path()` in `auth.py`) — it carries its own auth via cookie

**Test Cases:**
```
TC-E1-S3-1: POST /api/v1/auth/refresh with valid refresh_token cookie
  → HTTP 200
  → Body contains new access_token (JWT, exp = now + 15 min)
  → New Set-Cookie with rotated refresh_token

TC-E1-S3-2: POST /api/v1/auth/refresh with no cookie
  → HTTP 401
  → Error code: REFRESH_TOKEN_MISSING

TC-E1-S3-3: POST /api/v1/auth/refresh with expired refresh_token cookie
  → HTTP 401
  → Error code: REFRESH_TOKEN_EXPIRED

TC-E1-S3-4: POST /api/v1/auth/refresh with manually revoked jti (deleted from Redis)
  → HTTP 401
  → Error code: REFRESH_TOKEN_REVOKED

TC-E1-S3-5: Confirm old jti deleted from Redis after refresh (token rotation)
  → Redis key refresh_token:{old_jti} does not exist
  → Redis key refresh_token:{new_jti} exists
```

**Status:** 🟢 Done — PR #768

---

### E1-S4 — Frontend silent refresh logic

**Story:**  
As a logged-in user, my session is transparently renewed before my access token expires, so I never see an unexpected logout or 401 error during normal use.

**Acceptance Criteria:**
- Frontend holds access token in memory (React context) only — not localStorage
- On every authenticated API call, if a 401 is received, frontend automatically calls `POST /auth/refresh` once
- If refresh succeeds: retry the original request with the new access token
- If refresh fails (401 from refresh endpoint): clear auth state, redirect to login
- On app load / page refresh: immediately call `POST /auth/refresh` to restore session
- No access token stored in localStorage or sessionStorage anywhere in the codebase

**Technical Implementation Notes:**
- File: `src/CP/FrontEnd/src/services/api.service.ts` (or equivalent axios/fetch interceptor)
- Implement as an HTTP interceptor: on 401 response → call refresh → retry once → if still 401 → logout
- Flag to prevent infinite refresh loops: if already refreshing, queue requests and replay after
- On app startup (`App.tsx` or auth context provider): call refresh endpoint, set access token in context if successful
- Search entire `src/CP/FrontEnd/src/` for `localStorage.setItem` — must not set any token there

**Test Cases:**
```
TC-E1-S4-1: Make an authenticated request with an expired access token
  → Frontend automatically calls POST /auth/refresh
  → Original request is retried with new token
  → User sees no error, no redirect

TC-E1-S4-2: Make an authenticated request when refresh token is also expired
  → POST /auth/refresh returns 401
  → User is redirected to login screen
  → Auth state is cleared

TC-E1-S4-3: Refresh page while logged in
  → App calls POST /auth/refresh on load
  → Access token restored from refresh token cookie
  → User lands on their dashboard, not login screen

TC-E1-S4-4: Grep localStorage in frontend code
  → No token stored in localStorage or sessionStorage
```

**Status:** 🟢 Done — PR #768

---

## Epic 2 — Token Revocation

**Goal:** Any issued JWT can be invalidated immediately — on logout, password reset, or account compromise. Without this, a stolen token is valid for its full lifetime with no way to stop it.

**Context:**  
Redis is already in docker-compose and available. The revocation list uses Redis because it needs to be checked on every single authenticated request — must be sub-millisecond. Each refresh token `jti` is stored in Redis with TTL matching token expiry. Revocation = delete the key.

---

### E2-S1 — Redis revocation list on logout

**Story:**  
As a user who clicks logout, my refresh token is immediately invalidated on the server so nobody can use it to get new access tokens, even if they have the cookie value.

**Acceptance Criteria:**
- `POST /api/v1/auth/logout` — reads refresh token from cookie, deletes its `jti` from Redis
- Clears the refresh token cookie (set expired cookie with same name/path/domain)
- Returns HTTP 200
- After logout, calling `POST /auth/refresh` with the old cookie returns 401 (revoked)

**Technical Implementation Notes:**
- File: `src/Plant/BackEnd/api/v1/auth.py` — add `POST /logout` route
- Read cookie, decode JWT (without full validation — just extract `jti`), delete `refresh_token:{jti}` from Redis
- Clear cookie: `response.delete_cookie("refresh_token", path="/api/v1/auth")`
- Must be in public path list — user might have an expired access token when they logout
- Frontend: on logout, call this endpoint, then clear access token from memory and redirect to login

**Test Cases:**
```
TC-E2-S1-1: POST /api/v1/auth/logout with valid refresh_token cookie
  → HTTP 200
  → Redis key refresh_token:{jti} deleted
  → Set-Cookie header clears the refresh_token cookie (max-age=0 or expired date)

TC-E2-S1-2: POST /api/v1/auth/refresh after logout with old cookie
  → HTTP 401
  → Error code: REFRESH_TOKEN_REVOKED

TC-E2-S1-3: POST /api/v1/auth/logout with no cookie
  → HTTP 200 (idempotent — logout is always successful even if already logged out)
```

**Status:** 🟢 Done — PR #768

---

### E2-S2 — Check revocation on every authenticated request

**Story:**  
As the Plant Gateway, on every request with a JWT access token, I verify the token has not been revoked, so a compromised access token can be blocked within seconds.

**Acceptance Criteria:**
- Auth middleware checks a Redis revocation key for the access token's `jti` on every authenticated request
- Access token revocation key pattern: `revoked_access:{jti}`
- If key exists: return HTTP 401, error code `TOKEN_REVOKED`
- Performance: Redis check is < 2ms — must not meaningfully add latency
- This check only applies to access tokens — refresh token revocation is checked in the refresh endpoint

**Technical Implementation Notes:**
- File: `src/Plant/Gateway/middleware/auth.py` — in the JWT validation section
- After decoding JWT, extract `jti` — check `EXISTS revoked_access:{jti}` in Redis
- Redis connection must be async (`aioredis`) — do not use synchronous Redis in async middleware
- Revoked access token TTL in Redis = remaining time on the token (so keys auto-expire and don't accumulate)
- To revoke an access token: `SET revoked_access:{jti} 1 EX {remaining_ttl}`

**Test Cases:**
```
TC-E2-S2-1: Send request with valid, non-revoked JWT
  → HTTP 200 (passes through)
  → Redis check happens but key does not exist

TC-E2-S2-2: Manually add revoked_access:{jti} to Redis, then send request with that JWT
  → HTTP 401
  → Error code: TOKEN_REVOKED

TC-E2-S2-3: Performance — 1000 authenticated requests in sequence
  → p95 latency increase from Redis check < 2ms

TC-E2-S2-4: Token expires naturally (not revoked)
  → HTTP 401
  → Error code: TOKEN_EXPIRED (not TOKEN_REVOKED — distinguish the two)
```

**Status:** 🟢 Done — PR #768

---

### E2-S3 — Revoke all tokens on password reset

**Story:**  
As a user who resets their password, all my existing sessions across all devices are immediately invalidated so that anyone who had my old credentials or tokens can no longer access my account.

**Acceptance Criteria:**
- Password reset flow invalidates ALL refresh tokens for the user (not just current session)
- Approach: store a `token_version` per user in DB, increment on password reset — tokens with old version are rejected
- Alternatively: store all active `jti` values per user in Redis set — delete entire set on password reset
- Recommended: `user_token_version` column on `customers` table — simpler, no Redis set management
- JWT includes `token_version` claim — auth middleware rejects if claim < current DB version

**Technical Implementation Notes:**
- Add `token_version integer DEFAULT 1` to `customers` table (migration)
- On JWT generation: include `token_version` claim
- On password reset: `UPDATE customers SET token_version = token_version + 1 WHERE id = ?`
- In auth middleware: after JWT decode, fetch customer's current `token_version`, compare with JWT claim — reject if stale
- Cache `token_version` per user in Redis (TTL 5 min) to avoid DB hit on every request

**Test Cases:**
```
TC-E2-S3-1: Log in on two devices (two valid JWTs)
  → Both can make authenticated requests

TC-E2-S3-2: Reset password on device 1
  → Device 1 gets new token with new token_version
  → Device 2's old token is rejected with HTTP 401
  → Error code: TOKEN_VERSION_MISMATCH

TC-E2-S3-3: token_version incremented in DB after password reset
  → SELECT token_version FROM customers WHERE id = ? → incremented

TC-E2-S3-4: New login after password reset
  → New JWT contains updated token_version
  → Authenticated requests succeed
```

**Status:** 🟢 Done — PR #768

---

## Epic Completion — Docker Integration Test

Run after all stories in this iteration are complete.

```bash
# Start all services
docker compose -f docker-compose.local.yml up -d

# Run full backend test suite
docker compose -f docker-compose.local.yml run --rm --no-deps plant-backend pytest tests/ -x -q

# Run CP backend tests
docker compose -f docker-compose.local.yml run --rm --no-deps cp-backend pytest tests/ -x -q

# TypeScript check on CP frontend
docker compose -f docker-compose.local.yml run --rm --no-deps cp-frontend npx tsc --noEmit

# Verify Redis is being used
docker compose -f docker-compose.local.yml exec redis redis-cli KEYS "refresh_token:*"
```

All tests must pass. Zero TypeScript errors. Redis keys must be visible after a test login.
