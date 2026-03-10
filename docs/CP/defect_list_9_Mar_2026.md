# Defect List — 9 March 2026
## Session: CP Portal Live Testing — Open Defects Only

**Source:** Static code analysis pruned by live verification on demo after PR #912 deployment and CP repair waves 1 and 2
**Environment:** https://cp.demo.waooaw.com
**Auth pattern used for live checks:** demo customer demo@waooaw.com (id = ce8cf044-b378-4d3d-b11d-4817074b08f6) with Docker-minted JWTs and live Cloud Run routes

### Status after CP repair waves 1 and 2

The following defects were fixed in this wave and are removed from the active ledger:

- DEF-CP-001: Plant now exposes hired-agent trial budget
- DEF-CP-002: Plant now exposes hired-agent pause and resume
- DEF-CP-007: performance stats router no longer mounts under double /v1
- DEF-CP-008: platform connections router no longer mounts under double /v1
- DEF-CP-009: deliverables list now honors the optional status filter
- DEF-CP-010: refresh restore now normalizes the in-memory user to the canonical JWT subject

These fixes were validated with targeted Docker tests in the Plant and CP backends.

---

## Live Validation Snapshot

| Check | Result |
|---|---|
| Plant Gateway OpenAPI | Runtime route surface for earlier PR #912 families remains present on demo |
| CP BackEnd OpenAPI | Runtime route surface for earlier PR #912 families remains present on demo |
| CP repair waves 1 and 2 | Fixed in code and validated in Docker tests; demo redeploy validation still pending |
| CP refresh restoration | Fixed in code; demo redeploy validation still pending |

---

## Current Open Defects

No currently open CP defects remain in this ledger. This tracker is code-complete and awaiting only post-deploy runtime revalidation.

---

## Summary

- 0 valid CP defects remain open in this ledger.
- All previously active CP defects were fixed in code and validated with targeted Docker tests.
- Demo redeploy validation is still required to convert this from code-complete to runtime-verified.
- The remaining work after CP is the separate PP and mobile defect tracker.
- PP and mobile continue to have a separate defect tracker at docs/PP/iterations/PP-MOBILE-DEFECTS-1-systematic-audit-and-fix.md.
