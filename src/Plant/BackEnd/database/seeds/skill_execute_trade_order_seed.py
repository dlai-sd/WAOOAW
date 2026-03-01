"""Seed: execute-trade-order skill with goal_schema.

PLANT-SKILLS-1 E5-S2

Run: python -m database.seeds.skill_execute_trade_order_seed

Idempotent — upserts by external_id = "execute-trade-order".
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from core.database import _connector

EXTERNAL_ID = "execute-trade-order"

EXECUTE_TRADE_ORDER_GOAL_SCHEMA = {
    "fields": [
        {
            "key": "exchange",
            "type": "string",
            "required": True,
            "label": "Exchange name",
            "placeholder": "e.g. delta_exchange",
            "help": "Must match a connected PlatformConnection platform_key",
        },
        {
            "key": "instrument",
            "type": "string",
            "required": True,
            "label": "Instrument / Symbol",
            "placeholder": "e.g. BTC-USDT, NIFTY",
        },
        {
            "key": "leverage",
            "type": "integer",
            "required": False,
            "label": "Leverage (if supported by exchange)",
            "min": 1,
            "max": 100,
            "default": 1,
        },
        {
            "key": "interval",
            "type": "select",
            "required": True,
            "label": "Candle interval",
            "options": ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"],
            "default": "5m",
        },
        {
            "key": "trade_amount_usdt",
            "type": "decimal",
            "required": True,
            "label": "Trade amount (USDT)",
            "min": 10,
            "max_plan_gate": "max_trade_amount_usdt",
            "help": "Amount per trade. Maximum set by your subscription plan.",
        },
        {
            "key": "direction",
            "type": "select",
            "required": True,
            "label": "Trade direction",
            "options": ["buy", "sell", "both"],
            "default": "both",
        },
        {
            "key": "entry_condition",
            "type": "textarea",
            "required": True,
            "label": "Entry condition",
            "placeholder": "e.g. RSI < 30 AND price crosses above 200 EMA",
        },
        {
            "key": "stop_loss_pct",
            "type": "decimal",
            "required": True,
            "label": "Stop loss (%)",
            "min": 0.1,
            "max": 50,
            "default": 2.5,
        },
        {
            "key": "profit_target_pct",
            "type": "decimal",
            "required": True,
            "label": "Profit target (%)",
            "min": 0.1,
            "max": 100,
            "default": 5.0,
        },
        {
            "key": "max_stop_losses",
            "type": "integer",
            "required": True,
            "label": "Stop trading after N stop-losses",
            "min": 1,
            "max": 10,
            "default": 2,
            "help": "Agent halts the session after this many consecutive stop-losses",
        },
        {
            "key": "max_profit_exits",
            "type": "integer",
            "required": True,
            "label": "Stop trading after N profit exits",
            "min": 1,
            "max": 10,
            "default": 2,
        },
        {
            "key": "run_window",
            "type": "select",
            "required": True,
            "label": "Trading window",
            "options": ["24x7", "market_open_close", "custom"],
            "default": "24x7",
            "help": (
                "24x7 for crypto; market_open_close = first/last 1hr for equity; "
                "custom for specific window"
            ),
        },
        {
            "key": "run_window_custom",
            "type": "string",
            "required": False,
            "label": "Custom window (IST, HH:MM-HH:MM)",
            "placeholder": "e.g. 09:15-10:15,14:30-15:30",
            "show_if": {"key": "run_window", "value": "custom"},
        },
    ],
    "platform_connections_required": True,
    "platform_connection_keys": ["exchange"],
    "approval_workflow": None,
    "halt_logic": {
        "stop_after_stop_losses": "max_stop_losses",
        "stop_after_profit_exits": "max_profit_exits",
    },
}


async def seed_execute_trade_order():
    """Upsert execute-trade-order skill with goal_schema."""
    from models.skill import Skill  # local import — avoids top-level SQLAlchemy init race

    print(f"Seeding skill: {EXTERNAL_ID} ...")
    session = await _connector.get_session()
    async with session:
        # Check if already exists by external_id
        result = await session.execute(
            select(Skill).where(Skill.external_id == EXTERNAL_ID)
        )
        existing = result.scalars().first()

        if existing:
            existing.goal_schema = EXECUTE_TRADE_ORDER_GOAL_SCHEMA
            await session.commit()
            print(f"  ↺  Updated goal_schema for existing skill: {EXTERNAL_ID} (id={existing.id})")
        else:
            skill = Skill(
                id=uuid.uuid4(),
                external_id=EXTERNAL_ID,
                entity_type="Skill",
                name="Execute Trade Order",
                description=(
                    "Executes trades on a crypto/equity exchange on behalf of the customer "
                    "with configurable entry conditions, stop-loss, profit targets, "
                    "leverage, and trading window. Halts automatically after configured "
                    "consecutive stop-losses or profit exits."
                ),
                category="domain_expertise",
                goal_schema=EXECUTE_TRADE_ORDER_GOAL_SCHEMA,
                governance_agent_id="genesis",
            )
            session.add(skill)
            await session.commit()
            print(f"  ✓  Created skill: {EXTERNAL_ID} (id={skill.id})")

    print("✓ execute-trade-order seed complete")


if __name__ == "__main__":
    asyncio.run(seed_execute_trade_order())
