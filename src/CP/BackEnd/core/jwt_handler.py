"""
JWT token handling utilities
Create, validate, and decode JWT tokens for authentication
"""

from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError

from core.config import settings
from models.user import TokenData


class JWTHandler:
    """Handle JWT token creation and validation"""

    @staticmethod
    def create_access_token(user_id: str, email: str, tenant_id: str) -> str:
        """
        Create a new access token

        Args:
            user_id: User's unique identifier
            email: User's email address
            tenant_id: Tenant's unique identifier

        Returns:
            Encoded JWT access token
        """
        expires_delta = timedelta(hours=1)  # Token expiry set to 1 hour
        expire = datetime.utcnow() + expires_delta

        payload = {
            "user_id": user_id,
            "email": email,
            "tenant_id": tenant_id,
            "token_type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_refresh_token(user_id: str, email: str, tenant_id: str) -> str:
        """
        Create a new refresh token

        Args:
            user_id: User's unique identifier
            email: User's email address
            tenant_id: Tenant's unique identifier

        Returns:
            Encoded JWT refresh token
        """
        expires_delta = timedelta(days=30)  # Refresh token expiry set to 30 days
        expire = datetime.utcnow() + expires_delta

        payload = {
            "user_id": user_id,
            "email": email,
            "tenant_id": tenant_id,
            "token_type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

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
            tenant_id = payload.get("tenant_id")
            token_type = payload.get("token_type")

            if user_id is None or email is None or tenant_id is None:
                raise credentials_exception

            return TokenData(
                user_id=user_id, email=email, token_type=token_type, tenant_id=tenant_id
            )

        except InvalidTokenError:
            raise credentials_exception

    @staticmethod
    def create_token_pair(user_id: str, email: str, tenant_id: str) -> Dict[str, Any]:
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


# Convenience functions
def create_tokens(user_id: str, email: str, tenant_id: str) -> Dict[str, Any]:
    """Create access and refresh token pair"""
    return JWTHandler.create_token_pair(user_id, email, tenant_id)


def verify_token(token: str) -> TokenData:
    """Verify and decode a token"""
    return JWTHandler.decode_token(token)
