# CP Registration Tasks — Register 1

**Date**: 2026-02-17
**Scope**: CP registration reliability + auth modal polish

## Story REG-UI-1: Stabilize Google sign-in button in auth modals
**Status**: done

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| Google OAuth button mounts after script load and reflows the layout | Visible layout shift in Sign In/Sign Up modals | Reserve button space and align width/height to avoid late reflow while keeping Google button logic intact |

**Acceptance criteria**
- Google sign-in button renders with a fixed footprint (no layout shift).
- Visual alignment matches CP modal styling and spacing.
- No auth logic change.

## Story REG-BE-1: Surface Plant persistence failures during OTP verify
**Status**: done

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| Plant upsert is best-effort in non-prod, so failed persistence is silent | Customer appears registered but is not saved in Plant; no error feedback | Make Plant persistence strict by default (configurable override) and return an error when it fails |

**Acceptance criteria**
- OTP verify returns a clear error when Plant persistence fails or is misconfigured.
- Behavior is configurable via env override for best-effort mode.
- Tests cover strict vs best-effort behavior.
