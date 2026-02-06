---
playbook_id: TRADING.DELTA.FUTURES.MANUAL.V1
name: Delta Exchange India futures (manual enter/exit)
version: 1.0.0
category: trading
description: Deterministic manual trade planning with strict risk checks; execution is approval-gated.
output_contract: trading_delta_futures_manual_v1
required_inputs:
  - exchange_account_id
  - coin
  - units
  - side
  - action
steps:
  - Validate intent fields (coin/units/side/action)
  - Apply risk limits (max units per order, max notional if available)
  - Produce an order intent payload (market or limit)
  - If explicitly authorized (intent_action + approval_id), execute via Delta client
quality_checks:
  - Never execute without explicit approval
  - Never accept raw API keys in request payload
  - Units must be > 0 and within configured limits
  - Side/action must be one of the allowed enums
---

# Skill: Delta futures manual trading

This playbook defines a minimal, certifiable contract for manual trade intents.

The MVP produces a draft order intent; later stories add approved execution + audit.
