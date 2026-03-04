
---

## [2026-03-04 16:30 UTC] Diagnosed and fixed Razorpay 502 (receipt too long)

**Branch**: `fix/razorpay-receipt-length-plant`
**PR**: #854 — https://github.com/dlai-sd/WAOOAW/pull/854
**Status**: Completed — all 12 CI checks green

### What was done
User reported "Plant Razorpay order create failed (502)" even after PR #852 was deployed. Root cause traced via Cloud Run logs + direct Razorpay API test: `internal_order_id = f"ORDER-{uuid4()}"` = 42 chars; Razorpay's `receipt` field enforces a 40-char max → Razorpay returns 400 → Plant raises HTTPException(502). The curl debug test passed because it used `"test-receipt-001"` (16 chars). Fixed by generating receipt separately as `f"ORD-{uuid4().hex}"` = 36 chars. Also added structured error logging for future Razorpay failures.

### Outcome
- All 6 Plant Razorpay unit tests pass
- All 12 CI checks on PR #854 green

### Key files changed
| File | Change |
|------|--------|
| `src/Plant/BackEnd/api/v1/payments_simple.py` | Receipt uses `f"ORD-{uuid4().hex}"` (36 chars); error logging added |
| `src/Plant/BackEnd/tests/unit/test_payments_razorpay_api.py` | Receipt assertion updated to `startswith("ORD-")` + `len <= 40` |

### Next step
Merge PR #854 and deploy to demo. After deploy, user should test "Pay Now" flow — Razorpay popup with UPI/card options should appear.

### Recovery hint
This was the ONLY reason Razorpay checkout never worked — it was always 42 chars. After merge+deploy the full Razorpay UI (UPI, cards, netbanking) should appear correctly since the `amount` + `prefill` fixes from PR #852 are already in.
