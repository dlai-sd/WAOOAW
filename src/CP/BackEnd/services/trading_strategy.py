"""Trading strategy configuration storage (CP).

Story TR-CP-3.1: Customer configures interval/time window parameters for
future strategy automation. Execution remains approval-gated.

This stores non-secret config per customer_id (and agent_id) in a lightweight
JSONL file store.
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ActiveWindow(BaseModel):
    start: str = Field(..., min_length=1)
    end: str = Field(..., min_length=1)


class TradingStrategyConfigPublic(BaseModel):
    config_ref: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)

    interval_seconds: Optional[int] = Field(default=None, gt=0)
    active_window: Optional[ActiveWindow] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class _TradingStrategyConfigRecord(TradingStrategyConfigPublic):
    pass


class FileTradingStrategyConfigStore:
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def mint_config_ref(self) -> str:
        return f"STRAT-{secrets.token_urlsafe(12)}"

    def upsert(
        self,
        *,
        customer_id: str,
        agent_id: str,
        interval_seconds: Optional[int],
        active_window: Optional[ActiveWindow],
        metadata: Optional[Dict[str, Any]] = None,
        config_ref: Optional[str] = None,
    ) -> TradingStrategyConfigPublic:
        rows = self._load_records()
        now = _utcnow()

        if not config_ref:
            config_ref = self.mint_config_ref()

        record = _TradingStrategyConfigRecord(
            config_ref=config_ref,
            customer_id=customer_id,
            agent_id=agent_id,
            interval_seconds=interval_seconds,
            active_window=active_window,
            metadata=dict(metadata or {}),
            created_at=now,
            updated_at=now,
        )

        replaced = False
        for idx, existing in enumerate(rows):
            if existing.config_ref == record.config_ref:
                record.created_at = existing.created_at
                rows[idx] = record
                replaced = True
                break

        if not replaced:
            rows.append(record)

        self._write_records(rows)
        return TradingStrategyConfigPublic(**record.model_dump())

    def list(self, *, customer_id: str, agent_id: Optional[str] = None, limit: int = 100) -> List[TradingStrategyConfigPublic]:
        rows = [r for r in self._load_records() if r.customer_id == customer_id]
        if agent_id:
            rows = [r for r in rows if r.agent_id == agent_id]
        rows = rows[-max(1, int(limit)) :]
        return [TradingStrategyConfigPublic(**r.model_dump()) for r in rows]

    def _load_records(self) -> List[_TradingStrategyConfigRecord]:
        if not self._path.exists():
            return []
        rows: List[_TradingStrategyConfigRecord] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(_TradingStrategyConfigRecord.model_validate_json(line))
            except Exception:
                continue
        return rows

    def _write_records(self, rows: List[_TradingStrategyConfigRecord]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(row.model_dump_json())
                f.write("\n")


@lru_cache(maxsize=1)
def default_trading_strategy_config_store() -> FileTradingStrategyConfigStore:
    path = os.getenv("CP_TRADING_STRATEGY_STORE_PATH", "/app/data/cp_trading_strategy.jsonl")
    return FileTradingStrategyConfigStore(path)


def get_trading_strategy_config_store() -> FileTradingStrategyConfigStore:
    return default_trading_strategy_config_store()
