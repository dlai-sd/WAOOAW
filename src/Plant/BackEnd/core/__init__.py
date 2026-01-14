"""
Plant Backend - Core Configuration Layer
Centralized configuration, database, security, and exception handling
"""

from core.config import settings
from core.database import Base, get_connector
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
    "get_connector",
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
