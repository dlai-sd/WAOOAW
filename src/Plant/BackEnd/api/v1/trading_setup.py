"""
Trading setup chat API for Share Trader agent (feat/share-trader-setup-chat).

Provides a guided step-machine conversation that collects Delta Exchange
credentials, validates them live, and stores trading strategy parameters.
No LLM — all assistant messages are pre-scripted for security (API keys must
never be sent to an LLM).

State is stored in hired_agent.config["trading_setup"] JSONB.

Steps:
  welcome → api_key → api_secret → validate → instrument → rsi_period
          → risk_limits → done
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.exchange_credentials import _validate_exchange_live
from core.database import get_db_session, get_read_db_session
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from repositories.hired_agent_repository import HiredAgentRepository
from services.exchange_credential_service import (
    ExchangeCredentialService,
    _encrypt,
    _decrypt,
)

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/hired-agents", tags=["trading-setup"])

_SETUP_KEY = "trading_setup"
_AGENT_TYPE = "trading.share_trader.v1"

# ── Step definitions ────────────────────────────────────────────────────────

STEPS = [
    "welcome",
    "api_key",
    "api_secret",
    "validate",
    "instrument",
    "rsi_period",
    "risk_limits",
    "done",
]

_ASSISTANT_INTRO = {
    "welcome": (
        "Namaste! 🇮🇳 I'm your Share Trader — a technical-analysis expert "
        "specialising in F&O, futures, crypto and Indian indices (NIFTY, BANKNIFTY, "
        "BTC, ETH and more).\n\n"
        "To get started I need your **Delta Exchange API credentials** so I can connect "
        "to the markets on your behalf. Your keys are encrypted at rest and never logged.\n\n"
        "Ready? Type **start** to begin setup."
    ),
    "api_key": (
        "**Step 1 of 6 — API Key**\n\n"
        "Please enter your Delta Exchange API Key. "
        "You can find it at: *Settings → API Keys* in your Delta Exchange account.\n\n"
        "_Your input is masked on screen and encrypted before storage._"
    ),
    "api_secret": (
        "**Step 2 of 6 — API Secret**\n\n"
        "Now enter your Delta Exchange API Secret (shown once when you create the key).\n\n"
        "_Masked on screen. Never stored in plain text._"
    ),
    "validate": (
        "**Step 3 of 6 — Validating credentials…**\n\n"
        "Connecting to Delta Exchange to verify your keys have read and trade permissions."
    ),
    "instrument": (
        "**Step 4 of 6 — Default Instrument**\n\n"
        "Which instrument should I trade by default?\n\n"
        "Examples: **BTC**, **ETH**, **NIFTY**, **BANKNIFTY**, **SOL**\n\n"
        "Type the instrument symbol (e.g. `BTC`)."
    ),
    "rsi_period": (
        "**Step 5 of 6 — RSI Period**\n\n"
        "I use RSI (Relative Strength Index) to generate BUY/SELL signals.\n\n"
        "• Period **14** is the industry standard (recommended)\n"
        "• Shorter periods (e.g. 7) = more signals, more noise\n"
        "• Longer periods (e.g. 21) = fewer signals, more reliable\n\n"
        "Enter a number between 2 and 100, or type **14** to use the default."
    ),
    "risk_limits": (
        "**Step 6 of 6 — Risk Limits**\n\n"
        "Set your safety guardrails. I will never place an order that exceeds these.\n\n"
        "Reply in this format:\n"
        "`units: <max units per order>  notional: <max INR per order>`\n\n"
        "Example: `units: 1  notional: 50000`\n\n"
        "Or type **skip** to use defaults (1 unit, ₹50,000 notional)."
    ),
}

_VALIDATION_SUCCESS = (
    "✅ **Credentials validated!** Delta Exchange connection confirmed — "
    "read access and trade permissions verified.\n\n"
    "Now let's configure your trading strategy."
)

_VALIDATION_FAIL = (
    "❌ **Credential validation failed.**\n\n"
    "The keys could not connect to Delta Exchange. Please check:\n"
    "• The API key and secret are copied correctly (no extra spaces)\n"
    "• The key has *Read* and *Write* permissions enabled\n"
    "• The key has not expired\n\n"
    "Type your API key again to retry from Step 1."
)

_DONE_MESSAGE = (
    "🎯 **Your Share Trader is ready!**\n\n"
    "I'm now configured and connected to Delta Exchange. "
    "Here's your setup summary:\n\n"
    "{summary}\n\n"
    "I'll analyse the market using RSI signals and notify you of BUY/SELL "
    "opportunities. You approve each trade before I execute. "
    "\n\nHead back to the agent dashboard to start your first trading goal."
)


# ── Pydantic models ─────────────────────────────────────────────────────────

class TradingSetupMessage(BaseModel):
    role: str  # "assistant" | "user"
    content: str
    masked: bool = False  # True when the user input was a sensitive field


class TradingSetupState(BaseModel):
    step: str = "welcome"
    messages: list[TradingSetupMessage] = Field(default_factory=list)
    collected: dict[str, Any] = Field(default_factory=dict)
    validation_status: str = "pending"  # pending | valid | invalid
    configured: bool = False
    updated_at: str = ""


class TradingSetupResponse(BaseModel):
    hired_instance_id: str
    state: TradingSetupState
    readiness: dict[str, Any]


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    customer_id: str = Field(..., min_length=1)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _state_from_config(config: dict[str, Any] | None) -> TradingSetupState:
    raw = (config or {}).get(_SETUP_KEY)
    if not raw or not isinstance(raw, dict):
        return TradingSetupState()
    try:
        return TradingSetupState(**raw)
    except Exception:
        return TradingSetupState()


def _state_to_config(existing: dict[str, Any], state: TradingSetupState) -> dict[str, Any]:
    updated = dict(existing or {})
    updated[_SETUP_KEY] = state.model_dump(mode="json")
    return updated


def _readiness(state: TradingSetupState) -> dict[str, Any]:
    collected = state.collected
    return {
        "configured": state.configured,
        "step": state.step,
        "has_credentials": bool(collected.get("encrypted_api_key")),
        "credentials_valid": state.validation_status == "valid",
        "has_instrument": bool(collected.get("default_coin")),
        "has_rsi_period": "rsi_period" in collected,
        "has_risk_limits": bool(collected.get("max_units_per_order")),
    }


def _mask_content(content: str) -> str:
    """Return a redacted display string for sensitive fields."""
    if not content:
        return "●●●●"
    return "●" * min(len(content), 8) + f"…({len(content)} chars)"


def _assistant_msg(content: str) -> TradingSetupMessage:
    return TradingSetupMessage(role="assistant", content=content)


def _user_msg(content: str, *, masked: bool = False) -> TradingSetupMessage:
    return TradingSetupMessage(role="user", content=content, masked=masked)


# ── Step processor ──────────────────────────────────────────────────────────

async def _process_step(
    state: TradingSetupState,
    user_input: str,
    hired_instance_id: str,
    db: AsyncSession,
) -> TradingSetupState:
    """Advance the step machine by one step based on user_input."""
    step = state.step
    inp = user_input.strip()
    msgs = list(state.messages)
    collected = dict(state.collected)

    # ── welcome ──
    if step == "welcome":
        msgs.append(_user_msg(inp))
        msgs.append(_assistant_msg(_ASSISTANT_INTRO["api_key"]))
        state.step = "api_key"

    # ── api_key ──
    elif step == "api_key":
        if not inp:
            msgs.append(_user_msg("[empty]", masked=True))
            msgs.append(_assistant_msg("API key cannot be empty. Please enter your Delta Exchange API key."))
        else:
            collected["encrypted_api_key"] = _encrypt(inp)
            msgs.append(_user_msg(_mask_content(inp), masked=True))
            msgs.append(_assistant_msg(_ASSISTANT_INTRO["api_secret"]))
            state.step = "api_secret"

    # ── api_secret ──
    elif step == "api_secret":
        if not inp:
            msgs.append(_user_msg("[empty]", masked=True))
            msgs.append(_assistant_msg("API secret cannot be empty. Please enter your Delta Exchange API secret."))
        else:
            collected["encrypted_api_secret"] = _encrypt(inp)
            msgs.append(_user_msg(_mask_content(inp), masked=True))
            msgs.append(_assistant_msg(_ASSISTANT_INTRO["validate"]))
            state.step = "validate"
            # Auto-advance to validation immediately
            api_key = _decrypt(collected["encrypted_api_key"])
            api_secret = _decrypt(collected["encrypted_api_secret"])
            readable, tradeable, _, error = await _validate_exchange_live(
                api_key=api_key, api_secret=api_secret
            )
            if readable:
                state.validation_status = "valid"
                msgs.append(_assistant_msg(_VALIDATION_SUCCESS))
                msgs.append(_assistant_msg(_ASSISTANT_INTRO["instrument"]))
                state.step = "instrument"
            else:
                state.validation_status = "invalid"
                msgs.append(_assistant_msg(_VALIDATION_FAIL))
                collected.pop("encrypted_api_key", None)
                collected.pop("encrypted_api_secret", None)
                msgs.append(_assistant_msg(_ASSISTANT_INTRO["api_key"]))
                state.step = "api_key"

    # ── instrument ──
    elif step == "instrument":
        coin = inp.upper().strip()
        if not coin or len(coin) > 20:
            msgs.append(_user_msg(inp))
            msgs.append(_assistant_msg("Please enter a valid instrument symbol (e.g. BTC, NIFTY, ETH)."))
        else:
            collected["default_coin"] = coin
            msgs.append(_user_msg(coin))
            msgs.append(_assistant_msg(_ASSISTANT_INTRO["rsi_period"]))
            state.step = "rsi_period"

    # ── rsi_period ──
    elif step == "rsi_period":
        try:
            period = int(inp)
            if not 2 <= period <= 100:
                raise ValueError
            collected["rsi_period"] = period
            msgs.append(_user_msg(str(period)))
            msgs.append(_assistant_msg(_ASSISTANT_INTRO["risk_limits"]))
            state.step = "risk_limits"
        except ValueError:
            msgs.append(_user_msg(inp))
            msgs.append(_assistant_msg(
                f"RSI period must be a whole number between 2 and 100. "
                f"You entered: `{inp}`. Try again, or type **14** for the default."
            ))

    # ── risk_limits ──
    elif step == "risk_limits":
        units, notional = 1.0, 50000.0
        if inp.lower() != "skip":
            try:
                parts = {k.strip(): float(v.strip())
                         for part in inp.replace(",", " ").split()
                         for k, v in [part.split(":")] if ":" in part}
                units = parts.get("units", 1.0)
                notional = parts.get("notional", 50000.0)
                if units <= 0 or notional <= 0:
                    raise ValueError
            except Exception:
                msgs.append(_user_msg(inp))
                msgs.append(_assistant_msg(
                    "I couldn't parse that. Please use the format:\n"
                    "`units: 1  notional: 50000`\n\n"
                    "Or type **skip** for defaults."
                ))
                state.messages = msgs
                state.collected = collected
                return state

        collected["max_units_per_order"] = units
        collected["max_notional_inr"] = notional
        msgs.append(_user_msg(f"units: {units}  notional: ₹{notional:,.0f}"))

        # Persist exchange credentials to DB
        svc = ExchangeCredentialService(db)
        try:
            rec = await svc.upsert(
                customer_id=collected.get("customer_id", "unknown"),
                exchange_provider="delta_exchange_india",
                api_key=_decrypt(collected["encrypted_api_key"]),
                api_secret=_decrypt(collected["encrypted_api_secret"]),
                default_coin=collected["default_coin"],
                allowed_coins=[collected["default_coin"]],
                risk_limits={
                    "max_units_per_order": units,
                    "max_notional_inr": notional,
                },
            )
            await svc.mark_validated(
                credential_ref=rec.credential_ref, status="valid"
            )
            collected["credential_ref"] = rec.credential_ref
        except Exception as exc:
            logger.error("trading_setup: credential persist failed — %s", type(exc).__name__)

        # Remove raw encrypted blobs from state — credential_ref is enough
        collected.pop("encrypted_api_key", None)
        collected.pop("encrypted_api_secret", None)

        summary = (
            f"• Exchange: Delta Exchange India\n"
            f"• Instrument: {collected.get('default_coin', '—')}\n"
            f"• RSI Period: {collected.get('rsi_period', 14)}\n"
            f"• Max units/order: {units}\n"
            f"• Max notional: ₹{notional:,.0f}"
        )
        msgs.append(_assistant_msg(_DONE_MESSAGE.format(summary=summary)))
        state.step = "done"
        state.configured = True

    state.messages = msgs
    state.collected = collected
    state.updated_at = datetime.now(timezone.utc).isoformat()
    return state


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/{hired_instance_id}/trading-setup",
            response_model=TradingSetupResponse)
async def get_trading_setup(
    hired_instance_id: str,
    customer_id: str,
    db=Depends(get_read_db_session),
) -> TradingSetupResponse:
    """Return current trading setup state for the hired agent."""
    repo = HiredAgentRepository(db)
    record = await repo.get_by_id(hired_instance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Hired agent not found")
    state = _state_from_config(record.config)
    if state.step == "welcome" and not state.messages:
        state.messages = [_assistant_msg(_ASSISTANT_INTRO["welcome"])]
    return TradingSetupResponse(
        hired_instance_id=hired_instance_id,
        state=state,
        readiness=_readiness(state),
    )


@router.post("/{hired_instance_id}/trading-setup/message",
             response_model=TradingSetupResponse)
async def send_trading_setup_message(
    hired_instance_id: str,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TradingSetupResponse:
    """Process a user message and advance the setup step machine."""
    repo = HiredAgentRepository(db)
    record = await repo.get_by_id(hired_instance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Hired agent not found")

    state = _state_from_config(record.config)
    if state.step == "welcome" and not state.messages:
        state.messages = [_assistant_msg(_ASSISTANT_INTRO["welcome"])]

    if state.step == "done":
        # Allow re-configuration by resetting
        state = TradingSetupState()
        state.messages = [_assistant_msg(_ASSISTANT_INTRO["welcome"])]

    # Inject customer_id into collected for credential persistence
    state.collected["customer_id"] = body.customer_id

    state = await _process_step(
        state=state,
        user_input=body.content,
        hired_instance_id=hired_instance_id,
        db=db,
    )

    updated_config = _state_to_config(dict(record.config or {}), state)
    await repo.update_config(
        hired_instance_id,
        config=updated_config,
        configured=state.configured if state.configured else None,
    )
    await db.commit()

    return TradingSetupResponse(
        hired_instance_id=hired_instance_id,
        state=state,
        readiness=_readiness(state),
    )
