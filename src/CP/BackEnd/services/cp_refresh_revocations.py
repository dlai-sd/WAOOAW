"""Refresh token revocations (CP).

AUTH-1.2 requires logout to revoke refresh tokens.

Minimal CP-local implementation:
- File-backed JSONL event store.
- Per-user revocation timestamp: on logout we record a `revoked_at` time.
- Any refresh token with `iat` <= `revoked_at` is treated as revoked.

In production, consider Redis and per-token `jti` revocation.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

from models.user import TokenData


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CPRefreshRevocationEvent(BaseModel):
    user_id: str = Field(..., min_length=1)
    revoked_at: datetime = Field(default_factory=_utcnow)


class FileCPRefreshRevocationStore:
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def revoke_user(self, user_id: str, *, revoked_at: datetime | None = None) -> None:
        event = CPRefreshRevocationEvent(user_id=user_id, revoked_at=revoked_at or _utcnow())
        with self._path.open("a", encoding="utf-8") as f:
            f.write(event.model_dump_json())
            f.write("\n")

    def revoked_at_for_user(self, user_id: str) -> datetime | None:
        last: datetime | None = None
        for event in self._iter_events():
            if event.user_id == user_id:
                last = event.revoked_at
        return last

    def is_refresh_token_revoked(self, token_data: TokenData) -> bool:
        if token_data.token_type != "refresh":
            return False

        token_iat = token_data.iat
        if token_iat is None:
            return False

        revoked_at = self.revoked_at_for_user(token_data.user_id)
        if revoked_at is None:
            return False

        issued_at = datetime.fromtimestamp(int(token_iat), tz=timezone.utc)
        return issued_at <= revoked_at

    def _iter_events(self):
        if not self._path.exists():
            return
        for line in self._path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw:
                continue
            try:
                yield CPRefreshRevocationEvent.model_validate_json(raw)
            except Exception:
                continue


@lru_cache(maxsize=1)
def default_cp_refresh_revocation_store() -> FileCPRefreshRevocationStore:
    explicit_path = os.getenv("CP_REFRESH_REVOKE_STORE_PATH")
    if explicit_path:
        return FileCPRefreshRevocationStore(explicit_path)

    # Default to a relative path so unit tests and non-container environments
    # don't require an `/app` filesystem layout.
    default_path = Path("data") / "cp_refresh_revocations.jsonl"
    return FileCPRefreshRevocationStore(default_path)


def get_cp_refresh_revocation_store() -> FileCPRefreshRevocationStore:
    return default_cp_refresh_revocation_store()
