"""Usage ledger (in-process).

Goal 4: provide a minimal metering primitive (tasks/day, spend/month) with a
stable interface. This is intentionally in-memory for now to avoid adding new
DB migrations while the test DB is pinned to Alembic revision 006.

Later phases can replace the implementation with Redis/Postgres without changing
call sites.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Protocol


class UsageLedger(Protocol):
    def increment_with_limit(
        self,
        *,
        key: str,
        limit: int,
        window: timedelta,
        amount: int = 1,
        now: datetime | None = None,
    ) -> "CounterConsumeResult":
        """Increment a counter under a fixed window."""

    def add_spend_with_limit(
        self,
        *,
        key: str,
        budget_usd: float,
        spend_usd: float,
        window: timedelta,
        now: datetime | None = None,
    ) -> "SpendConsumeResult":
        """Add spend under a fixed window."""


@dataclass(frozen=True)
class CounterConsumeResult:
    allowed: bool
    value: int
    resets_at: datetime


@dataclass(frozen=True)
class SpendConsumeResult:
    allowed: bool
    total_usd: float
    resets_at: datetime


@dataclass
class _WindowedValue:
    value: float
    resets_at: datetime


class InMemoryUsageLedger:
    def __init__(self) -> None:
        self._counters: Dict[str, _WindowedValue] = {}

    def _now(self, now: datetime | None) -> datetime:
        if now is None:
            return datetime.now(tz=timezone.utc)
        if now.tzinfo is None:
            return now.replace(tzinfo=timezone.utc)
        return now

    def _get_window(self, *, key: str, window: timedelta, now: datetime) -> _WindowedValue:
        current = self._counters.get(key)
        if current is None or now >= current.resets_at:
            current = _WindowedValue(value=0.0, resets_at=now + window)
            self._counters[key] = current
        return current

    def increment_with_limit(
        self,
        *,
        key: str,
        limit: int,
        window: timedelta,
        amount: int = 1,
        now: datetime | None = None,
    ) -> CounterConsumeResult:
        if limit < 0:
            raise ValueError("limit must be >= 0")
        if amount <= 0:
            raise ValueError("amount must be > 0")

        current_time = self._now(now)
        window_value = self._get_window(key=key, window=window, now=current_time)

        new_value = int(window_value.value) + amount
        if new_value > limit:
            return CounterConsumeResult(
                allowed=False,
                value=int(window_value.value),
                resets_at=window_value.resets_at,
            )

        window_value.value = float(new_value)
        return CounterConsumeResult(
            allowed=True,
            value=new_value,
            resets_at=window_value.resets_at,
        )

    def add_spend_with_limit(
        self,
        *,
        key: str,
        budget_usd: float,
        spend_usd: float,
        window: timedelta,
        now: datetime | None = None,
    ) -> SpendConsumeResult:
        if budget_usd < 0:
            raise ValueError("budget_usd must be >= 0")
        if spend_usd < 0:
            raise ValueError("spend_usd must be >= 0")

        current_time = self._now(now)
        window_value = self._get_window(key=key, window=window, now=current_time)

        new_total = float(window_value.value) + float(spend_usd)
        if new_total > float(budget_usd):
            return SpendConsumeResult(
                allowed=False,
                total_usd=float(window_value.value),
                resets_at=window_value.resets_at,
            )

        window_value.value = float(new_total)
        return SpendConsumeResult(
            allowed=True,
            total_usd=float(new_total),
            resets_at=window_value.resets_at,
        )


class FileUsageLedger:
    """File-backed JSON usage ledger.

    Provides persistence for counters/spend without DB migrations.
    State is stored as a single JSON object mapping key -> {value,resets_at}.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def _now(self, now: datetime | None) -> datetime:
        if now is None:
            return datetime.now(tz=timezone.utc)
        if now.tzinfo is None:
            return now.replace(tzinfo=timezone.utc)
        return now

    def _load(self) -> Dict[str, _WindowedValue]:
        raw = self._path.read_text(encoding="utf-8").strip()
        if not raw:
            return {}
        data = json.loads(raw)
        out: Dict[str, _WindowedValue] = {}
        for key, val in data.items():
            resets_at = datetime.fromisoformat(val["resets_at"])
            if resets_at.tzinfo is None:
                resets_at = resets_at.replace(tzinfo=timezone.utc)
            out[key] = _WindowedValue(value=float(val["value"]), resets_at=resets_at)
        return out

    def _save(self, state: Dict[str, _WindowedValue]) -> None:
        serialized = {
            key: {"value": float(val.value), "resets_at": val.resets_at.isoformat()}
            for key, val in state.items()
        }
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            _flock_exclusive(f)
            json.dump(serialized, f)
            f.flush()
            os.fsync(f.fileno())
            _flock_release(f)
        os.replace(tmp, self._path)

    def _get_window(
        self,
        *,
        state: Dict[str, _WindowedValue],
        key: str,
        window: timedelta,
        now: datetime,
    ) -> _WindowedValue:
        current = state.get(key)
        if current is None or now >= current.resets_at:
            current = _WindowedValue(value=0.0, resets_at=now + window)
            state[key] = current
        return current

    def increment_with_limit(
        self,
        *,
        key: str,
        limit: int,
        window: timedelta,
        amount: int = 1,
        now: datetime | None = None,
    ) -> CounterConsumeResult:
        if limit < 0:
            raise ValueError("limit must be >= 0")
        if amount <= 0:
            raise ValueError("amount must be > 0")

        current_time = self._now(now)
        state = self._load()
        window_value = self._get_window(state=state, key=key, window=window, now=current_time)

        new_value = int(window_value.value) + amount
        if new_value > limit:
            return CounterConsumeResult(
                allowed=False,
                value=int(window_value.value),
                resets_at=window_value.resets_at,
            )

        window_value.value = float(new_value)
        self._save(state)
        return CounterConsumeResult(
            allowed=True,
            value=new_value,
            resets_at=window_value.resets_at,
        )

    def add_spend_with_limit(
        self,
        *,
        key: str,
        budget_usd: float,
        spend_usd: float,
        window: timedelta,
        now: datetime | None = None,
    ) -> SpendConsumeResult:
        if budget_usd < 0:
            raise ValueError("budget_usd must be >= 0")
        if spend_usd < 0:
            raise ValueError("spend_usd must be >= 0")

        current_time = self._now(now)
        state = self._load()
        window_value = self._get_window(state=state, key=key, window=window, now=current_time)

        new_total = float(window_value.value) + float(spend_usd)
        if new_total > float(budget_usd):
            return SpendConsumeResult(
                allowed=False,
                total_usd=float(window_value.value),
                resets_at=window_value.resets_at,
            )

        window_value.value = float(new_total)
        self._save(state)
        return SpendConsumeResult(
            allowed=True,
            total_usd=float(new_total),
            resets_at=window_value.resets_at,
        )


def _flock_exclusive(f) -> None:  # type: ignore[no-untyped-def]
    try:
        import fcntl

        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    except Exception:
        return


def _flock_release(f) -> None:  # type: ignore[no-untyped-def]
    try:
        import fcntl

        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception:
        return
