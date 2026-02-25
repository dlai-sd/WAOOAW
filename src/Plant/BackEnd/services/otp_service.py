"""Plant OTP service — AUTH-MOBILE-OTP-1.

In-memory OTP challenge store for the mobile registration/login flow.
Uses secure random 6-digit codes, SHA-256 hashed storage, per-destination
rate limiting, and per-challenge attempt capping.

Design choices:
- In-memory: avoids external dependencies (no Redis required for demo/uat).
  For production at scale, swap the store backend for Redis-backed equivalent.
- Codes are stored as SHA-256 hashes — not plaintext.
- TTL enforced at verification time (not deferred garbage collection).
- Thread-safe via threading.Lock (FastAPI workers share memory in a single
  asyncio-based process).
"""

from __future__ import annotations

import hashlib
import random
import string
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from pydantic import BaseModel


# ── Config ────────────────────────────────────────────────────────────────────

OTP_TTL_SECONDS: int = 300            # 5 minutes per challenge
OTP_MAX_ATTEMPTS: int = 5             # brute-force cap per challenge
OTP_RATE_WINDOW_SECONDS: int = 600    # 10-minute issuance window
OTP_RATE_MAX_PER_WINDOW: int = 3      # max challenges per destination per window


# ── Data model ────────────────────────────────────────────────────────────────

class OtpChallenge(BaseModel):
    """Stored state for one OTP challenge."""

    otp_id: str
    registration_id: str
    channel: Literal["email", "phone"]
    destination: str
    code_hash: str          # SHA-256 of the plain OTP code
    created_at: datetime
    expires_at: datetime
    attempts: int = 0
    verified: bool = False


# ── Store ─────────────────────────────────────────────────────────────────────

class OtpStore:
    """Thread-safe in-memory OTP challenge store."""

    def __init__(self) -> None:
        self._challenges: dict[str, OtpChallenge] = {}
        self._lock = threading.Lock()

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _generate_code(length: int = 6) -> str:
        return "".join(random.choices(string.digits, k=length))

    @staticmethod
    def _hash_code(code: str) -> str:
        return hashlib.sha256(code.encode()).hexdigest()

    # ── Public API ────────────────────────────────────────────────────────────

    def can_issue(self, *, destination: str) -> bool:
        """Return True if a new challenge may be issued for ``destination``.

        Limits issuance to ``OTP_RATE_MAX_PER_WINDOW`` challenges per
        destination within the last ``OTP_RATE_WINDOW_SECONDS``.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=OTP_RATE_WINDOW_SECONDS)
        with self._lock:
            count = sum(
                1
                for c in self._challenges.values()
                if c.destination == destination and c.created_at >= cutoff
            )
        return count < OTP_RATE_MAX_PER_WINDOW

    def create_challenge(
        self,
        *,
        registration_id: str,
        channel: Literal["email", "phone"],
        destination: str,
        ttl_seconds: int = OTP_TTL_SECONDS,
    ) -> tuple[OtpChallenge, str]:
        """Create and store a new OTP challenge.

        Returns ``(challenge, plain_code)`` — the plain code is returned once
        and never stored (only its hash is kept).
        """
        code = self._generate_code()
        now = datetime.now(timezone.utc)
        challenge = OtpChallenge(
            otp_id=str(uuid.uuid4()),
            registration_id=registration_id,
            channel=channel,
            destination=destination,
            code_hash=self._hash_code(code),
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        with self._lock:
            self._challenges[challenge.otp_id] = challenge
        return challenge, code

    def get_challenge(self, otp_id: str) -> OtpChallenge | None:
        with self._lock:
            return self._challenges.get(otp_id)

    def verify(self, *, otp_id: str, code: str) -> tuple[bool, str]:
        """Verify ``code`` against the stored challenge.

        Returns ``(True, "ok")`` on success, ``(False, reason)`` on failure.
        Marks the challenge as ``verified`` on success so it cannot be reused.
        """
        with self._lock:
            challenge = self._challenges.get(otp_id)
            if not challenge:
                return False, "OTP not found or already used"

            now = datetime.now(timezone.utc)
            if now > challenge.expires_at:
                return False, "OTP has expired. Please request a new one."

            if challenge.verified:
                return False, "OTP already used"

            if challenge.attempts >= OTP_MAX_ATTEMPTS:
                return False, "Too many invalid attempts. Please request a new OTP."

            if self._hash_code(code) != challenge.code_hash:
                challenge.attempts += 1
                return False, "Invalid OTP code"

            challenge.verified = True
            return True, "ok"


# ── Singleton ─────────────────────────────────────────────────────────────────

_store: Optional[OtpStore] = None
_store_lock = threading.Lock()


def get_otp_store() -> OtpStore:
    """Return the process-wide singleton OtpStore."""
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = OtpStore()
    return _store
