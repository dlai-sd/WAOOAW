# Defect List — 9 March 2026
## Session: CP Portal Live Testing — Open Defects Only

**Source:** Static code analysis pruned by live verification on demo after PR #912 deployment and CP repair wave 1
**Environment:** https://cp.demo.waooaw.com
**Auth pattern used for live checks:** demo customer demo@waooaw.com (id = ce8cf044-b378-4d3d-b11d-4817074b08f6) with Docker-minted JWTs and live Cloud Run routes

### Status after CP repair wave 1

The following defects were fixed in this wave and are removed from the active ledger:

- DEF-CP-001: Plant now exposes hired-agent trial budget
- DEF-CP-002: Plant now exposes hired-agent pause and resume
- DEF-CP-007: performance stats router no longer mounts under double /v1
- DEF-CP-008: platform connections router no longer mounts under double /v1
- DEF-CP-009: deliverables list now honors the optional status filter

These fixes were validated with targeted Docker tests in the Plant backend.

---

## Live Validation Snapshot

| Check | Result |
|---|---|
| Plant Gateway OpenAPI | Runtime route surface for earlier PR #912 families remains present on demo |
| CP BackEnd OpenAPI | Runtime route surface for earlier PR #912 families remains present on demo |
| CP repair wave 1 | Fixed in code and validated in Docker tests; demo redeploy validation still pending |
| CP refresh restoration | Still returns a non-canonical in-memory UUID from GET /api/auth/me after refresh restore |

---

## Current Open Defects

### DEF-CP-010 · LIVE BUG — CP refresh-restore returns auth/me.id as an in-memory UUID instead of the canonical Plant customer UUID

| | |
|---|---|
| **Files** | src/CP/BackEnd/api/auth/routes.py, src/CP/BackEnd/api/auth/user_store.py |
| **Live evidence** | On demo, POST /api/auth/refresh returned 200 and issued a new access token, but GET /api/auth/me on that token returned id = 206fa836-82d9-4422-8eed-d885b994d006 while Plant GET /api/v1/auth/validate returned the canonical customer id ce8cf044-b378-4d3d-b11d-4817074b08f6. |
| **Root cause** | The refresh cold-start restore path recreates a minimal in-memory User with a random UUID, aliases the canonical token subject to that object, and later routes read current_user.id from the random in-memory user rather than the canonical JWT subject. |
| **Impact** | Any CP proxy route that injects current_user.id into upstream requests can operate against the wrong customer identity after refresh-based restore. This is a live correctness issue and can distort runtime validation. |
| **Best fix** | Normalize the restored user so current_user.id equals the canonical token subject, or ensure CP proxy routes use the JWT subject rather than the random restored in-memory UUID. |

---

## Summary

- 1 valid CP defect remains open in this ledger.
- The route and data defects from CP repair wave 1 were fixed in code and validated with targeted Docker tests.
- Demo redeploy validation is still required before removing the remaining runtime caution line from the live snapshot.
- The remaining blocker is the CP auth/session identity restore path.
- PP and mobile continue to have a separate defect tracker at docs/PP/iterations/PP-MOBILE-DEFECTS-1-systematic-audit-and-fix.md.
