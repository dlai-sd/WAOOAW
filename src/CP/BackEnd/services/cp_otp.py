"""OTP challenges (CP).

REG-1.4 introduces OTP issuance + verification for CP registration.

This is a minimal, CP-local implementation:
- File-backed JSONL event store for auditability.
- Simple rate limiting per destination.
- In non-production environments, the OTP code may be returned for demo/testing.

A real provider integration (email/SMS) should replace the demo code path.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


Channel = Literal["email", "phone"]


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _mint_code() -> str:
    fixed = os.getenv("CP_OTP_FIXED_CODE")
    if fixed:
        return fixed
    return f"{secrets.randbelow(1_000_000):06d}"


class CPOtpEvent(BaseModel):
    otp_id: str = Field(..., min_length=1)
    registration_id: str = Field(..., min_length=1)

    channel: Channel
    destination: str = Field(..., min_length=1)

    code_hash: str = Field(..., min_length=1)

    created_at: datetime = Field(default_factory=_utcnow)
    expires_at: datetime

    verified_at: datetime | None = None
    attempts: int = 0


@dataclass(frozen=True)
class RateLimitConfig:
    max_per_window: int = 3
    window_seconds: int = 600


class FileCPOtpStore:
    def __init__(self, path: str | Path, *, rate_limit: RateLimitConfig | None = None):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)
        self._rate_limit = rate_limit or RateLimitConfig()

    def mint_otp_id(self) -> str:
        return f"OTP-{secrets.token_urlsafe(12)}"

    def can_issue(self, *, destination: str, now: datetime | None = None) -> bool:
        now = now or _utcnow()
        cutoff = now - timedelta(seconds=self._rate_limit.window_seconds)

        count = 0
        for event in self._iter_events():
            if event.destination != destination:
                continue
            if event.created_at >= cutoff:
                count += 1
        return count < self._rate_limit.max_per_window

    def create_challenge(
        self,
        *,
        registration_id: str,
        channel: Channel,
        destination: str,
        ttl_seconds: int = 300,
    ) -> tuple[CPOtpEvent, str]:
        otp_id = self.mint_otp_id()
        code = _mint_code()
        now = _utcnow()
        event = CPOtpEvent(
            otp_id=otp_id,
            registration_id=registration_id,
            channel=channel,
            destination=destination,
            code_hash=_hash_code(code),
            created_at=now,
            expires_at=now + timedelta(seconds=int(ttl_seconds)),
            verified_at=None,
            attempts=0,
        )
        self._append(event)
        return event, code

    def get_state(self, otp_id: str) -> CPOtpEvent | None:
        state: CPOtpEvent | None = None
        for event in self._iter_events():
            if event.otp_id == otp_id:
                state = event
        return state

    def record_attempt(self, otp_id: str, attempts: int) -> None:
        state = self.get_state(otp_id)
        if not state:
            return
        self._append(state.model_copy(update={"attempts": attempts}))

    def mark_verified(self, otp_id: str) -> None:
        state = self.get_state(otp_id)
        if not state:
            return
        self._append(state.model_copy(update={"verified_at": _utcnow()}))

    def verify(self, *, otp_id: str, code: str, max_attempts: int = 5) -> tuple[bool, str]:
        state = self.get_state(otp_id)
        if not state:
            return False, "OTP not found"
        if state.verified_at is not None:
            return False, "OTP already used"
        if _utcnow() >= state.expires_at:
            return False, "OTP expired"
        if state.attempts >= max_attempts:
            return False, "Too many attempts"

        expected = state.code_hash
        if _hash_code(code.strip()) != expected:
            self.record_attempt(otp_id, state.attempts + 1)
            return False, "Invalid OTP"

        self.mark_verified(otp_id)
        return True, "OK"

    def _append(self, event: CPOtpEvent) -> None:
        with self._path.open("a", encoding="utf-8") as f:
            f.write(event.model_dump_json())
            f.write("\n")

    def _iter_events(self):
        if not self._path.exists():
            return
        for line in self._path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw:
                continue
            try:
                yield CPOtpEvent.model_validate_json(raw)
            except Exception:
                continue


@lru_cache(maxsize=1)
def default_cp_otp_store() -> FileCPOtpStore:
    path = os.getenv("CP_OTP_STORE_PATH", "/app/data/cp_otp.jsonl")
    return FileCPOtpStore(path)


def get_cp_otp_store() -> FileCPOtpStore:
    return default_cp_otp_store()
