"""Registration records (CP).

REG-1.3 introduces a CP-local registration API that validates and normalizes
registration input, then mints a `registration_id` for later OTP verification.

Storage is file-backed (JSONL) to match other CP-local stores used in lower env.
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CPRegistrationRecord(BaseModel):
    registration_id: str = Field(..., min_length=1)

    full_name: str = Field(..., min_length=1)
    business_name: str = Field(..., min_length=1)
    business_industry: str = Field(..., min_length=1)
    business_address: str = Field(..., min_length=1)

    email: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)

    website: str | None = None
    gst_number: str | None = None

    preferred_contact_method: str = Field(..., min_length=1)
    consent: bool

    created_at: datetime = Field(default_factory=_utcnow)


class FileCPRegistrationStore:
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def mint_registration_id(self) -> str:
        return f"REG-{secrets.token_urlsafe(12)}"

    def append(self, record: CPRegistrationRecord) -> CPRegistrationRecord:
        with self._path.open("a", encoding="utf-8") as f:
            f.write(record.model_dump_json())
            f.write("\n")
        return record

    def get_by_id(self, registration_id: str) -> CPRegistrationRecord | None:
        if not self._path.exists():
            return None

        found: CPRegistrationRecord | None = None
        for line in self._path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw:
                continue
            try:
                record = CPRegistrationRecord.model_validate_json(raw)
            except Exception:
                continue
            if record.registration_id == registration_id:
                found = record
        return found

    def get_by_email(self, email: str) -> CPRegistrationRecord | None:
        value = (email or "").strip().lower()
        if not value or not self._path.exists():
            return None

        found: CPRegistrationRecord | None = None
        for line in self._path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw:
                continue
            try:
                record = CPRegistrationRecord.model_validate_json(raw)
            except Exception:
                continue
            if record.email.strip().lower() == value:
                found = record
        return found

    def get_by_phone(self, phone: str) -> CPRegistrationRecord | None:
        value = (phone or "").strip()
        if not value or not self._path.exists():
            return None

        found: CPRegistrationRecord | None = None
        for line in self._path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw:
                continue
            try:
                record = CPRegistrationRecord.model_validate_json(raw)
            except Exception:
                continue
            if record.phone.strip() == value:
                found = record
        return found


@lru_cache(maxsize=1)
def default_cp_registration_store() -> FileCPRegistrationStore:
    path = os.getenv("CP_REGISTRATIONS_STORE_PATH", "/app/data/cp_registrations.jsonl")
    return FileCPRegistrationStore(path)


def get_cp_registration_store() -> FileCPRegistrationStore:
    return default_cp_registration_store()
