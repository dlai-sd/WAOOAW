from datetime import datetime, timedelta
def create_refresh_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create a refresh token.

    Args:
        data: The data to encode in the token.
        expires_delta: Optional expiration time.

    Returns:
        The encoded JWT token as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt
from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError

from core.config import settings
from models.user import TokenData


def create_tokens(user_id: str, email: str) -> Dict[str, Any]:
    """
    Create JWT tokens for user authentication.

    Args:
        user_id: The ID of the user.
        email: The email of the user.

    Returns:
        A dictionary containing access and refresh tokens.
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email, "user_id": user_id}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": email, "user_id": user_id})

    return {"access_token": access_token, "refresh_token": refresh_token}


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create an access token.

    Args:
        data: The data to encode in the token.
        expires_delta: Optional expiration time.

    Returns:
        The encoded JWT token as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify a JWT token and decode its payload.

    Args:
        token: The JWT token to verify.

    Returns:
        The decoded token data.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return TokenData(**payload)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError

from core.config import settings
from models.user import TokenData


# Remove the duplicate JWTHandler class
