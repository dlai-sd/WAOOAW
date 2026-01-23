"""
Password hashing utilities using bcrypt
"""

from passlib.context import CryptContext
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.lifespan import Lifespan
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi import FastAPI

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiting configuration
RATE_LIMIT = 100  # requests per minute

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Implement rate limiting logic here
        # Check tenant ID from request and track requests
        # If limit exceeded, raise HTTPException
        response = await call_next(request)
        return response


def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password to check
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)
