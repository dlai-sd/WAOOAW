"""
Password hashing utilities using bcrypt
"""

from passlib.context import CryptContext
from fastapi import HTTPException, status
import asyncio

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


async def retry_with_exponential_backoff(func, *args, max_attempts=3):
    """
    Retry a function with exponential backoff.

    Args:
        func: The function to retry.
        *args: Arguments to pass to the function.
        max_attempts: Maximum number of attempts.

    Returns:
        The result of the function if successful.

    Raises:
        Exception: If all attempts fail.
    """
    for attempt in range(max_attempts):
        try:
            return await func(*args)
        except Exception as e:
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise e


def standardize_error_handling(exception: Exception) -> HTTPException:
    """
    Standardize error handling for the application.

    Args:
        exception: The exception to handle.

    Returns:
        HTTPException with standardized error message.
    """
    if isinstance(exception, HTTPException):
        return exception
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception))
