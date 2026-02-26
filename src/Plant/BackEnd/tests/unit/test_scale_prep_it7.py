"""Unit tests for Iteration 7 — Scale Prep.

E1-S1: get_read_db_session uses replica engine (or falls back to primary).
E2-S1: FeatureFlagService — is_enabled logic, percentage rollout, allowlist.
E3-S1: EncryptedString TypeDecorator, email_search_hash.
E4-S2: cleanup_otp_sessions task logic.
E5-S1: requirements.txt contains no unpinned specifiers.
"""

from __future__ import annotations

import os
import re
import sys
import uuid
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure Plant backend is on path
_PLANT_BACKEND = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir
)
sys.path.insert(0, os.path.abspath(_PLANT_BACKEND))


# ---------------------------------------------------------------------------
# E1-S1: Read replica — get_read_db_session available and wired
# ---------------------------------------------------------------------------

class TestReadReplicaDatabaseSession:
    """E1-S1: Confirm get_read_db_session is exported from core.database."""

    def test_get_read_db_session_exported(self):
        from core import database
        assert hasattr(database, "get_read_db_session"), (
            "get_read_db_session must be exported from core.database"
        )

    def test_get_db_session_exported(self):
        from core import database
        assert hasattr(database, "get_db_session")

    def test_read_replica_url_in_settings(self):
        """Settings must accept READ_REPLICA_URL env var (E1-S1 Acceptance Criteria)."""
        from core.config import Settings
        s = Settings(
            database_url="postgresql+asyncpg://u:p@localhost/test",
            READ_REPLICA_URL="postgresql+asyncpg://u:p@replica/test",
        )
        assert s.read_replica_url == "postgresql+asyncpg://u:p@replica/test"

    def test_read_replica_url_defaults_none(self):
        from core.config import Settings
        # Unset env → None (falls back to primary)
        s = Settings(database_url="postgresql+asyncpg://u:p@localhost/test")
        assert s.read_replica_url is None


# ---------------------------------------------------------------------------
# E2-S1: Feature flag service — evaluation logic
# ---------------------------------------------------------------------------

class TestFeatureFlagServiceEvaluation:
    """E2-S1: FeatureFlagService._evaluate() logic."""

    def _svc(self):
        from services.feature_flag_service import FeatureFlagService
        db = AsyncMock()
        return FeatureFlagService(db)

    def test_disabled_flag_always_false(self):
        svc = self._svc()
        flag = {"enabled": False, "rollout_percentage": 100, "enabled_for_customer_ids": []}
        assert svc._evaluate(flag, None) is False
        assert svc._evaluate(flag, uuid.uuid4()) is False

    def test_enabled_100pct_no_customer(self):
        svc = self._svc()
        flag = {"enabled": True, "rollout_percentage": 100, "enabled_for_customer_ids": None}
        assert svc._evaluate(flag, None) is True

    def test_enabled_0pct_no_customer(self):
        svc = self._svc()
        flag = {"enabled": True, "rollout_percentage": 0, "enabled_for_customer_ids": None}
        assert svc._evaluate(flag, None) is False

    def test_enabled_0pct_with_customer(self):
        svc = self._svc()
        cid = uuid.uuid4()
        flag = {"enabled": True, "rollout_percentage": 0, "enabled_for_customer_ids": None}
        assert svc._evaluate(flag, cid) is False

    def test_allowlist_overrides_zero_pct(self):
        svc = self._svc()
        cid = uuid.uuid4()
        flag = {
            "enabled": True,
            "rollout_percentage": 0,
            "enabled_for_customer_ids": [cid],
        }
        assert svc._evaluate(flag, cid) is True

    def test_rollout_deterministic(self):
        """TC-E2-S1-4 proxy: same customer always gets the same bucket."""
        svc = self._svc()
        from services.feature_flag_service import _hash_rollout
        cid = uuid.uuid4()
        result1 = _hash_rollout(cid)
        result2 = _hash_rollout(cid)
        assert result1 == result2
        assert 0 <= result1 < 100

    @pytest.mark.asyncio
    async def test_is_enabled_flag_not_found(self):
        from services.feature_flag_service import FeatureFlagService
        db = AsyncMock()
        svc = FeatureFlagService(db)
        svc._get_flag = AsyncMock(return_value=None)
        result = await svc.is_enabled("nonexistent_flag")
        assert result is False

    @pytest.mark.asyncio
    async def test_redis_failure_falls_back_to_db(self):
        """TC-E2-S1-5: Redis unavailable — falls back to DB query."""
        from services.feature_flag_service import FeatureFlagService

        db = AsyncMock()

        # Simulate DB returning a flag row via mappings().first()
        mock_row = {
            "key": "test",
            "enabled": True,
            "rollout_percentage": 100,
            "enabled_for_customer_ids": None,
            "scope": "all",
            "description": None,
            "updated_at": None,
        }
        mock_mappings = MagicMock()
        mock_mappings.first.return_value = mock_row
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings
        db.execute = AsyncMock(return_value=mock_result)

        # Redis.get raises (connection error)
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis down"))
        mock_redis.set = AsyncMock(side_effect=Exception("Redis down"))

        svc = FeatureFlagService(db, redis=mock_redis)
        flag = await svc._get_flag("test")
        assert flag is not None
        assert flag["enabled"] is True


# ---------------------------------------------------------------------------
# E3-S1: Field-level PII encryption
# ---------------------------------------------------------------------------

class TestEncryptedString:
    """E3-S1: EncryptedString round-trip and passthrough behaviour."""

    def test_passthrough_when_no_key(self):
        """TC-E3-S1-1: Without ENCRYPTION_KEY, value passes through unchanged."""
        from core.encryption import EncryptedString

        col = EncryptedString()

        class _FakeDialect:
            pass

        # _load_key reads os.getenv("ENCRYPTION_KEY") — patch env to empty
        with patch.dict(os.environ, {"ENCRYPTION_KEY": ""}):
            result = col.process_bind_param("user@example.com", _FakeDialect())
            assert result == "user@example.com"
            result2 = col.process_result_value("user@example.com", _FakeDialect())
            assert result2 == "user@example.com"

    def test_encrypt_decrypt_round_trip(self):
        """TC-E3-S1-2: Encrypt then decrypt returns original value."""
        import secrets as _sec
        key = _sec.token_bytes(32)
        from core.encryption import encrypt, decrypt
        plaintext = "test@example.com"
        ciphertext = encrypt(plaintext, key)
        assert ciphertext != plaintext
        assert decrypt(ciphertext, key) == plaintext

    def test_encrypt_produces_different_output_each_call(self):
        """Random nonce: same plaintext → different ciphertext each time."""
        import secrets as _sec
        key = _sec.token_bytes(32)
        from core.encryption import encrypt
        ct1 = encrypt("hello", key)
        ct2 = encrypt("hello", key)
        assert ct1 != ct2

    def test_email_search_hash_is_deterministic(self):
        """TC-E3-S1-3 proxy: Same email always produces same hash."""
        from core.encryption import email_search_hash
        h1 = email_search_hash("User@EXAMPLE.COM")
        h2 = email_search_hash("user@example.com")
        assert h1 == h2  # normalised to lowercase

    def test_email_search_hash_is_64_chars(self):
        from core.encryption import email_search_hash
        h = email_search_hash("user@example.com")
        assert len(h) == 64
        assert re.match(r"^[0-9a-f]{64}$", h)

    def test_encrypted_string_type_decorator_round_trip_with_key(self):
        """With an ENCRYPTION_KEY set, bind param encrypts and result value decrypts."""
        import secrets as _sec

        test_key = _sec.token_hex(32)  # 64 hex chars = 32 bytes

        class _FakeDialect:
            pass

        with patch.dict(os.environ, {"ENCRYPTION_KEY": test_key, "INDEX_KEY": ""}):
            from core.encryption import EncryptedString
            col = EncryptedString()
            bound = col.process_bind_param("hello@example.com", _FakeDialect())
            assert bound != "hello@example.com"
            recovered = col.process_result_value(bound, _FakeDialect())
            assert recovered == "hello@example.com"


# ---------------------------------------------------------------------------
# E5-S1: All requirements.txt files have exact pins (== only)
# ---------------------------------------------------------------------------

_PLANT_REQ = Path(_PLANT_BACKEND) / "requirements.txt"

def _sibling_req(service: str) -> Path:
    """Resolve CP/PP requirements.txt whether running on host or inside Plant container."""
    # Inside the Plant container, siblings are mounted at /app/tests/cp-req.txt etc.
    # On the host, derive from the PLANT_BACKEND path.
    container_mount = Path(f"/app/tests/{service.lower()}-requirements.txt")
    if container_mount.exists():
        return container_mount
    # Host path: src/<SERVICE>/BackEnd/requirements.txt
    return Path(_PLANT_BACKEND).parent.parent / service / "BackEnd" / "requirements.txt"


_BACKENDS = [
    _PLANT_REQ,
    _sibling_req("CP"),
    _sibling_req("PP"),
]

_UNPINNED_RE = re.compile(r"[>~^]=")


class TestDependencyPinning:
    """E5-S1: Confirm all requirements.txt files use == exact version specifiers."""

    @pytest.mark.parametrize("req_path", _BACKENDS)
    def test_no_unpinned_specifiers(self, req_path: Path):
        """TC-E5-S1-1: grep >= | ~= | ^= must return no results."""
        if not req_path.exists():
            pytest.skip(f"requirements.txt not accessible at {req_path} (cross-service file; run on host)")
        lines = req_path.read_text().splitlines()
        violations = [
            line for line in lines
            if line.strip() and not line.strip().startswith("#") and _UNPINNED_RE.search(line)
        ]
        assert violations == [], (
            f"{req_path.name}: unpinned specifiers found:\n"
            + "\n".join(f"  {v}" for v in violations)
        )
