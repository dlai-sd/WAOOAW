"""Authentication Models"""

from enum import Enum
from pydantic import BaseModel
from typing import Optional


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(BaseModel):
    """User model"""
    email: str
    name: str
    picture: Optional[str] = None
    role: UserRole


class TokenData(BaseModel):
    """Token data model"""
    email: str
    name: str
    role: UserRole
