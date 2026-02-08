"""CP 2FA (TOTP) store + helpers.

REG-1.7: Support 2FA enrollment and challenge after OTP verification,
and enforce it on login flows.

Storage is file-backed (JSONL append-only) for lower env parity.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TwoFAState(BaseModel):
    user_id: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)

    secret_base32: str | None = None
    enabled: bool = False

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class TwoFAEvent(BaseModel):
    user_id: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)  # enroll | enable | disable
    secret_base32: str | None = None
    enabled: bool
    occurred_at: datetime = Field(default_factory=_utcnow)


def generate_base32_secret(byte_length: int = 20) -> str:
    raw = secrets.token_bytes(byte_length)
    return base64.b32encode(raw).decode("utf-8").rstrip("=")


def _base32_decode_unpadded(secret_base32: str) -> bytes:
    s = (secret_base32 or "").strip().upper()
    padding = "=" * (-len(s) % 8)
    return base64.b32decode(s + padding, casefold=True)


def _hotp(secret_base32: str, counter: int, digits: int = 6) -> str:
    key = _base32_decode_unpadded(secret_base32)
    msg = counter.to_bytes(8, "big")
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = int.from_bytes(digest[offset : offset + 4], "big") & 0x7FFFFFFF
    return str(code_int % (10**digits)).zfill(digits)


def totp(secret_base32: str, for_time: float | None = None, step_seconds: int = 30, digits: int = 6) -> str:
    t = time.time() if for_time is None else float(for_time)
    counter = int(t // step_seconds)
    return _hotp(secret_base32, counter=counter, digits=digits)


def verify_totp(secret_base32: str, code: str, window: int = 1, step_seconds: int = 30, digits: int = 6) -> bool:
    candidate = "".join(ch for ch in str(code or "") if ch.isdigit())
    if len(candidate) != digits:
        return False

    now = time.time()
    current_counter = int(now // step_seconds)
    for drift in range(-window, window + 1):
        if _hotp(secret_base32, counter=current_counter + drift, digits=digits) == candidate:
            return True
    return False


def build_otpauth_uri(email: str, secret_base32: str, issuer: str = "WAOOAW") -> str:
    label = f"{issuer}:{email}".replace(" ", "%20")
    issuer_q = issuer.replace(" ", "%20")
    return (
        f"otpauth://totp/{label}?secret={secret_base32}"
        f"&issuer={issuer_q}&algorithm=SHA1&digits=6&period=30"
    )


class FileTwoFAStore:
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def _read_state(self) -> dict[str, TwoFAState]:
        states: dict[str, TwoFAState] = {}
        for line in self._path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw:
                continue
            try:
                event = TwoFAEvent.model_validate_json(raw)
            except Exception:
                continue

            existing = states.get(event.user_id)
            if existing is None:
                existing = TwoFAState(user_id=event.user_id, email=event.email)

            if event.event_type == "enroll":
                existing.secret_base32 = event.secret_base32
                existing.enabled = False
                existing.updated_at = event.occurred_at
            elif event.event_type == "enable":
                existing.secret_base32 = event.secret_base32
                existing.enabled = True
                existing.updated_at = event.occurred_at
            elif event.event_type == "disable":
                existing.secret_base32 = None
                existing.enabled = False
                existing.updated_at = event.occurred_at

            states[event.user_id] = existing

        return states

    def get(self, user_id: str) -> TwoFAState | None:
        return self._read_state().get(user_id)

    def is_enabled(self, user_id: str) -> bool:
        state = self.get(user_id)
        return bool(state and state.enabled and state.secret_base32)

    def get_secret(self, user_id: str) -> str | None:
        state = self.get(user_id)
        if not state:
            return None
        return state.secret_base32

    def _append(self, event: TwoFAEvent) -> None:
        with self._path.open("a", encoding="utf-8") as f:
            f.write(event.model_dump_json())
            f.write("\n")

    def enroll(self, user_id: str, email: str) -> TwoFAState:
        secret = generate_base32_secret()
        event = TwoFAEvent(
            user_id=user_id,
            email=email,
            event_type="enroll",
            secret_base32=secret,
            enabled=False,
        )
        self._append(event)
        return TwoFAState(user_id=user_id, email=email, secret_base32=secret, enabled=False)

    def enable(self, user_id: str, email: str, secret_base32: str) -> TwoFAState:
        event = TwoFAEvent(
            user_id=user_id,
            email=email,
            event_type="enable",
            secret_base32=secret_base32,
            enabled=True,
        )
        self._append(event)
        return TwoFAState(user_id=user_id, email=email, secret_base32=secret_base32, enabled=True)

    def disable(self, user_id: str, email: str) -> TwoFAState:
        event = TwoFAEvent(
            user_id=user_id,
            email=email,
            event_type="disable",
            secret_base32=None,
            enabled=False,
        )
        self._append(event)
        return TwoFAState(user_id=user_id, email=email, secret_base32=None, enabled=False)


@lru_cache(maxsize=1)
def default_cp_2fa_store() -> FileTwoFAStore:
    path = os.getenv("CP_2FA_STORE_PATH", "/app/data/cp_2fa.jsonl")
    return FileTwoFAStore(path)


def get_cp_2fa_store() -> FileTwoFAStore:
    return default_cp_2fa_store()
