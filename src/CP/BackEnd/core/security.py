"""
Password hashing utilities using bcrypt and JWT handling
"""

from passlib.context import CryptContext
from fastapi import HTTPException, status
import time
import jwt
from datetime import datetime, timedelta
from .config import settings
from fastapi.openapi.models import APIKey
from fastapi import Request

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def retry_with_exponential_backoff(func, *args, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return func(*args)
        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
            else:
                raise HTTPException(status_code=500, detail="Internal Server Error") from e

def standardize_error_handling(exception: Exception) -> dict:
    if isinstance(exception, HTTPException):
        return {
            "detail": exception.detail,
            "status_code": exception.status_code,
        }
    return {
        "detail": "Internal Server Error",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

def validate_request(request: Request):
    # Implement OpenAPI schema validation here
    pass

def inject_tenant(request: Request):
    # Implement tenant isolation logic here
    pass
