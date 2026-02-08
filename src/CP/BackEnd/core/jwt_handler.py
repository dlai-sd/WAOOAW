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
    def create_access_token(user_id: str, email: str) -> str:
        """
        Create a new access token

        Args:
            user_id: User's unique identifier
            email: User's email address

        Returns:
            Encoded JWT access token
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta

        payload = {
            "user_id": user_id,
            "email": email,
            "token_type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_refresh_token(user_id: str, email: str) -> str:
        """
        Create a new refresh token

        Args:
            user_id: User's unique identifier
            email: User's email address

        Returns:
            Encoded JWT refresh token
        """
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.utcnow() + expires_delta

        payload = {
            "user_id": user_id,
            "email": email,
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
            token_type = payload.get("token_type")
            iat = payload.get("iat")
            exp = payload.get("exp")

            if user_id is None or email is None:
                raise credentials_exception

            # Type narrowing after None check
            user_id_str: str = user_id
            email_str: str = email
            token_type_str: str = token_type if token_type else "access"

            return TokenData(
                user_id=user_id_str,
                email=email_str,
                token_type=token_type_str,
                iat=int(iat) if iat is not None else None,
                exp=int(exp) if exp is not None else None,
            )

        except InvalidTokenError:
            raise credentials_exception

    @staticmethod
    def create_token_pair(user_id: str, email: str) -> Dict[str, Any]:
        """
        Create both access and refresh tokens

        Args:
            user_id: User's unique identifier
            email: User's email address

        Returns:
            Dictionary with access_token, refresh_token, and metadata
        """
        access_token = JWTHandler.create_access_token(user_id, email)
        refresh_token = JWTHandler.create_refresh_token(user_id, email)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_seconds,
        }


# Convenience functions
def create_tokens(user_id: str, email: str) -> Dict[str, Any]:
    """Create access and refresh token pair"""
    return JWTHandler.create_token_pair(user_id, email)


def verify_token(token: str) -> TokenData:
    """Verify and decode a token"""
    return JWTHandler.decode_token(token)
