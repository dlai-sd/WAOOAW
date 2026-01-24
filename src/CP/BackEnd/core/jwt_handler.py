"""core.jwt_handler

JWT token handling utilities.

This module is used both by the FastAPI auth layer and unit tests.
It intentionally provides small convenience helpers (``create_tokens`` and
``verify_token``) in addition to the ``JWTHandler`` class.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError

from core.config import settings
from models.user import TokenData


class JWTHandler:
    """Handle JWT token creation and validation"""

    @staticmethod
    def create_access_token(user_id: str, email: str, tenant_id: Optional[str] = None) -> str:
        """
        Create a new access token

        Args:
            user_id: User's unique identifier
            email: User's email address
            tenant_id: Tenant's unique identifier

        Returns:
            Encoded JWT access token
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta

        payload: Dict[str, Any] = {
            "user_id": user_id,
            "email": email,
            "token_type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        if tenant_id:
            payload["tenant_id"] = tenant_id

        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_refresh_token(user_id: str, email: str, tenant_id: Optional[str] = None) -> str:
        """
        Create a new refresh token

        Args:
            user_id: User's unique identifier
            email: User's email address
            tenant_id: Tenant's unique identifier

        Returns:
            Encoded JWT refresh token
        """
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.utcnow() + expires_delta

        payload: Dict[str, Any] = {
            "user_id": user_id,
            "email": email,
            "token_type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        if tenant_id:
            payload["tenant_id"] = tenant_id

        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def decode_token(token: str) -> TokenData:
        """
        Decode and validate a JWT token

        Args:
            token: JWT token string

        Returns:
            TokenData with user information

        Raises:
            HTTPException: If token is invalid or expired
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )

            user_id = payload.get("user_id")
            email = payload.get("email")
            token_type = payload.get("token_type")

            if user_id is None or email is None:
                raise credentials_exception

            return TokenData(user_id=user_id, email=email, token_type=token_type or "access")

        except InvalidTokenError:
            raise credentials_exception

    @staticmethod
    def create_token_pair(user_id: str, email: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create both access and refresh tokens

        Args:
            user_id: User's unique identifier
            email: User's email address
            tenant_id: Tenant's unique identifier

        Returns:
            Dictionary with access_token, refresh_token, and metadata
        """
        access_token = JWTHandler.create_access_token(user_id, email, tenant_id)
        refresh_token = JWTHandler.create_refresh_token(user_id, email, tenant_id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_seconds,
        }


def create_tokens(user_id: str, email: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """Convenience wrapper used across the CP backend and tests."""

    return JWTHandler.create_token_pair(user_id=user_id, email=email, tenant_id=tenant_id)


def create_access_token(user_id: str, email: str, tenant_id: Optional[str] = None) -> str:
    """Backwards-compatible wrapper around ``JWTHandler.create_access_token``."""

    return JWTHandler.create_access_token(user_id=user_id, email=email, tenant_id=tenant_id)


def create_refresh_token(user_id: str, email: str, tenant_id: Optional[str] = None) -> str:
    """Backwards-compatible wrapper around ``JWTHandler.create_refresh_token``."""

    return JWTHandler.create_refresh_token(user_id=user_id, email=email, tenant_id=tenant_id)


def verify_token(token: str) -> TokenData:
    """Convenience wrapper used by FastAPI dependencies/middleware."""

    return JWTHandler.decode_token(token)
