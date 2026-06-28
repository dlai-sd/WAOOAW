"""Unit tests for Share Trader AgentSpec and ConstraintPolicy caps (ST-MVP-1 S4)."""
from __future__ import annotations


class TestConstraintPolicyCaps:
    """ST-MVP-1 S4 T1 — ConstraintPolicy hard-caps for Share Trader."""

    def test_default_max_leverage(self):
        from agent_mold.spec import ConstraintPolicy
        policy = ConstraintPolicy()
        assert policy.max_leverage == 10

    def test_default_max_capital_pct_per_trade(self):
        from agent_mold.spec import ConstraintPolicy
        policy = ConstraintPolicy()
        assert policy.max_capital_pct_per_trade == 20.0

    def test_share_trader_spec_max_leverage(self):
        from agent_mold.reference_agents import _trading_spec
        spec = _trading_spec("AGT-TRD-TEST")
        assert spec.constraint_policy.max_leverage == 10

    def test_share_trader_spec_max_capital_pct(self):
        from agent_mold.reference_agents import _trading_spec
        spec = _trading_spec("AGT-TRD-TEST")
        assert spec.constraint_policy.max_capital_pct_per_trade == 20.0


class TestExecuteTradeOrderGoalSchemaFields:
    """ST-MVP-1 S4 T2 — Seed adds all 4 new fields to goal_schema."""

    def test_seed_schema_contains_capital_pct(self):
        from database.seeds.skill_execute_trade_order_seed import EXECUTE_TRADE_ORDER_GOAL_SCHEMA
        keys = [f["key"] for f in EXECUTE_TRADE_ORDER_GOAL_SCHEMA["fields"]]
        assert "capital_pct" in keys

    def test_seed_schema_contains_autonomous_mode(self):
        from database.seeds.skill_execute_trade_order_seed import EXECUTE_TRADE_ORDER_GOAL_SCHEMA
        keys = [f["key"] for f in EXECUTE_TRADE_ORDER_GOAL_SCHEMA["fields"]]
        assert "autonomous_mode" in keys

    def test_seed_schema_contains_autonomous_consent_at(self):
        from database.seeds.skill_execute_trade_order_seed import EXECUTE_TRADE_ORDER_GOAL_SCHEMA
        keys = [f["key"] for f in EXECUTE_TRADE_ORDER_GOAL_SCHEMA["fields"]]
        assert "autonomous_consent_at" in keys

    def test_seed_schema_contains_risk_disclosure_accepted(self):
        from database.seeds.skill_execute_trade_order_seed import EXECUTE_TRADE_ORDER_GOAL_SCHEMA
        keys = [f["key"] for f in EXECUTE_TRADE_ORDER_GOAL_SCHEMA["fields"]]
        assert "risk_disclosure_accepted" in keys

    def test_capital_pct_limits(self):
        from database.seeds.skill_execute_trade_order_seed import EXECUTE_TRADE_ORDER_GOAL_SCHEMA
        field = next(f for f in EXECUTE_TRADE_ORDER_GOAL_SCHEMA["fields"] if f["key"] == "capital_pct")
        assert field["min"] == 1
        assert field["max"] == 20
        assert field["default"] == 5

    def test_autonomous_mode_default_false(self):
        from database.seeds.skill_execute_trade_order_seed import EXECUTE_TRADE_ORDER_GOAL_SCHEMA
        field = next(f for f in EXECUTE_TRADE_ORDER_GOAL_SCHEMA["fields"] if f["key"] == "autonomous_mode")
        assert field["default"] is False
        assert field["type"] == "boolean"
