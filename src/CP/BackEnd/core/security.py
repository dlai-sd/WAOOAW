"""
Password hashing utilities using bcrypt with retry logic
"""

from passlib.context import CryptContext
import time
import logging

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class HashingError(Exception):
    """Custom exception for hashing errors."""
    pass

def retry_with_exponential_backoff(func, *args, max_attempts=3):
    """Retry a function with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return func(*args)
        except Exception as e:
            if attempt < max_attempts - 1:
                wait_time = 2 ** attempt
                logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time} seconds.")
                time.sleep(wait_time)
            else:
                raise HashingError("Max attempts reached for hashing operation.") from e

def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt with retry logic.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return retry_with_exponential_backoff(pwd_context.hash, password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password with retry logic.
    
    Args:
        plain_password: Plain text password to check
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return retry_with_exponential_backoff(pwd_context.verify, plain_password, hashed_password)
