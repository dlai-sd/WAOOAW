"""Field-level PII encryption — E3-S1 (Iteration 7: Scale Prep).

Provides transparent AES-256-GCM encryption for PII SQLAlchemy columns.
The encryption key is loaded from the ENCRYPTION_KEY environment variable
(hex-encoded 32-byte key).  In production the key is injected via
GCP Secret Manager / Cloud Run secret volume mounts.

Usage in a model:
    from core.encryption import EncryptedString, email_search_hash

    class Customer(BaseEntity):
        email = Column(EncryptedString(255), nullable=False)
        email_hash = Column(String(64), nullable=False, index=True)
        phone = Column(EncryptedString(50), nullable=False)
        full_name = Column(EncryptedString(255), nullable=False)

The application layer must keep email_hash in sync with email:
    customer.email = "user@example.com"
    customer.email_hash = email_search_hash("user@example.com")

Performance: AES-256-GCM on a single field adds ≈ 0.5 ms (software AES).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from typing import Any, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

# ---------------------------------------------------------------------------
# Key management
# ---------------------------------------------------------------------------

_NONCE_SIZE = 12  # 96-bit nonce (GCM standard)


def _load_key() -> Optional[bytes]:
    """Load the 32-byte AES-256 encryption key from the environment.

    Returns None when the key is not configured (plain-text passthrough for
    local dev / tests that do not set ENCRYPTION_KEY).
    """
    raw = os.getenv("ENCRYPTION_KEY", "").strip()
    if not raw:
        return None
    try:
        key = bytes.fromhex(raw)
    except ValueError:
        # Try base64 fallback
        key = base64.b64decode(raw)
    if len(key) != 32:
        raise ValueError(
            f"ENCRYPTION_KEY must be 32 bytes (got {len(key)}). "
            "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return key


def _load_index_key() -> Optional[bytes]:
    """Load the 32-byte HMAC key used for searchable email_hash column.

    Defaults to ENCRYPTION_KEY if INDEX_KEY not set separately.
    """
    raw = os.getenv("INDEX_KEY", "").strip()
    if not raw:
        return _load_key()
    try:
        key = bytes.fromhex(raw)
    except ValueError:
        key = base64.b64decode(raw)
    if len(key) != 32:
        raise ValueError("INDEX_KEY must be exactly 32 bytes")
    return key


# ---------------------------------------------------------------------------
# Core encrypt/decrypt
# ---------------------------------------------------------------------------

def encrypt(plaintext: str, key: bytes) -> str:
    """Encrypt *plaintext* with AES-256-GCM.

    Returns a base64-encoded string: ``nonce || ciphertext || tag``.
    The nonce is randomly generated per call (96 bits = 12 bytes).
    """
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt(token: str, key: bytes) -> str:
    """Decrypt a token produced by :func:`encrypt`.

    Returns the original plaintext string.

    Raises:
        ValueError: If the token is malformed.
        cryptography.exceptions.InvalidTag: If MAC verification fails (tamper detected).
    """
    try:
        raw = base64.b64decode(token)
    except Exception as exc:
        raise ValueError("Encrypted field is not valid base64") from exc
    if len(raw) < _NONCE_SIZE + 16:  # nonce + min GCM tag
        raise ValueError("Encrypted field is too short to be valid")
    nonce = raw[:_NONCE_SIZE]
    ciphertext = raw[_NONCE_SIZE:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


# ---------------------------------------------------------------------------
# Searchable email index helper
# ---------------------------------------------------------------------------

def email_search_hash(email: str) -> str:
    """Return a constant-time HMAC-SHA256 digest of *email* for DB indexing.

    The digest is hex-encoded (64 characters).  When INDEX_KEY is not set,
    returns a SHA-256 hash of the lowercased email (acceptable for dev/test).
    """
    email_normalised = email.strip().lower()
    key = _load_index_key()
    if key:
        return hmac.HMAC(key, email_normalised.encode("utf-8"), hashlib.sha256).hexdigest()
    # Fallback for dev (no secret key)
    return hashlib.sha256(email_normalised.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# SQLAlchemy TypeDecorator
# ---------------------------------------------------------------------------

class EncryptedString(TypeDecorator):
    """SQLAlchemy column type that transparently encrypts on write and
    decrypts on read using AES-256-GCM.

    When ENCRYPTION_KEY is not set (local dev / unit tests), values are
    stored and returned as plain text — no behaviour change.

    Example::

        class Customer(Base):
            email = Column(EncryptedString(255), nullable=False)
    """

    impl = String
    cache_ok = True

    def __init__(self, length: int = 1024, *args: Any, **kwargs: Any):
        # Store enough room for base64(nonce + aes_tag + ciphertext_of_max_plaintext)
        # 255-char plaintext → ≈ 340 bytes cipher → 456 b64 chars; 1024 is safe.
        super().__init__(length, *args, **kwargs)

    def process_bind_param(self, value: Optional[str], dialect: Any) -> Optional[str]:
        """Called when writing to DB — encrypt the plaintext value."""
        if value is None:
            return None
        key = _load_key()
        if key is None:
            return value  # passthrough for dev
        return encrypt(str(value), key)

    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[str]:
        """Called when reading from DB — decrypt the stored ciphertext."""
        if value is None:
            return None
        key = _load_key()
        if key is None:
            return value  # passthrough for dev
        # Graceful degradation: if value is not valid ciphertext (e.g. legacy plain
        # row from before encryption was enabled), return as-is with a warning.
        try:
            return decrypt(str(value), key)
        except Exception:  # noqa: BLE001
            import logging
            logging.getLogger(__name__).warning(
                "EncryptedString: decryption failed — returning raw value "
                "(may be un-migrated plaintext row)"
            )
            return value
