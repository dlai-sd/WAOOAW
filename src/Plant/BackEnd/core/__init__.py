"""
Plant Backend - Core Configuration Layer
Centralized configuration, database, security, and exception handling
"""

from core.config import settings
from core.database import engine, SessionLocal, Base
from core.exceptions import (
    ConstitutionalAlignmentError,
    HashChainBrokenError,
    AmendmentSignatureError,
    EntityNotFoundError,
    ValidationError,
    DuplicateEntityError,
)
from core.security import verify_password, get_password_hash
from core.logging import get_logger

__all__ = [
    "settings",
    "engine",
    "SessionLocal",
    "Base",
    "ConstitutionalAlignmentError",
    "HashChainBrokenError",
    "AmendmentSignatureError",
    "EntityNotFoundError",
    "ValidationError",
    "DuplicateEntityError",
    "verify_password",
    "get_password_hash",
    "get_logger",
]
