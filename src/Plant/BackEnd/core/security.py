"""
Security utilities - JWT, password hashing, RBAC helpers
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from passlib.context import CryptContext
from jose import JWTError, jwt, ExpiredSignatureError

from core.config import settings
from core.observability import get_logger
from core.exceptions import (
    JWTTokenExpiredError,
    JWTInvalidSignatureError,
    JWTInvalidTokenError,
    JWTMissingClaimError,
)

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Hash a plain password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
        
    Example:
        hashed = get_password_hash("mypassword")
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hash
        
    Returns:
        bool: True if password matches hash
        
    Example:
        if verify_password("mypassword", hashed):
            print("Password is correct")
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Claims to encode in token
        expires_delta: Token expiration time (default: 30 minutes)
        
    Returns:
        str: JWT token
        
    Example:
        token = create_access_token({"sub": user_id})
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode JWT token with detailed error handling.
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Decoded claims if valid
        
    Raises:
        JWTTokenExpiredError: Token has expired
        JWTInvalidSignatureError: Signature verification failed
        JWTInvalidTokenError: Token format is invalid
        
    Example:
        try:
            claims = verify_token(token)
            user_id = claims.get("sub")
        except JWTTokenExpiredError:
            # Handle expired token - refresh required
            pass
        except JWTInvalidSignatureError:
            # Handle tampered/wrong key
            pass
        except JWTInvalidTokenError:
            # Handle malformed token
            pass
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
        
    except ExpiredSignatureError as e:
        # Token has expired - extract expiration time if available
        expired_at = None
        try:
            # Decode without verification to get exp claim
            unverified = jwt.get_unverified_claims(token)
            if 'exp' in unverified:
                exp_timestamp = unverified['exp']
                expired_at = datetime.fromtimestamp(exp_timestamp).isoformat()
        except Exception:
            pass  # couldn't extract expiration, continue with None
        
        # Log for security monitoring
        logger.warning(
            f"JWT token expired",
            extra={
                "expired_at": expired_at,
                "token_prefix": token[:20] if token else None,
            }
        )
        raise JWTTokenExpiredError(expired_at=expired_at)
    
    except JWTError as e:
        error_msg = str(e).lower()
        
        # Check for signature verification failure
        if 'signature' in error_msg or 'verify' in error_msg:
            logger.error(
                "JWT signature verification failed - possible tampering or wrong key",
                extra={"error": str(e), "token_prefix": token[:20] if token else None}
            )
            raise JWTInvalidSignatureError()
        
        # All other JWT errors indicate malformed token
        logger.warning(
            "JWT token format invalid",
            extra={"error": str(e), "token_prefix": token[:20] if token else None}
        )
        raise JWTInvalidTokenError(reason=str(e))
