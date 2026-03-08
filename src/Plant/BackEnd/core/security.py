"""
Security utilities - JWT, password hashing, RBAC helpers
"""

import functools
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import uuid4
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

# ── Constants ──────────────────────────────────────────────────────────────────
REFRESH_TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # E1-S1: 15 minutes for access tokens

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
        expires_delta: Token expiration time (default: 15 minutes per E1-S1)
        
    Returns:
        str: JWT token
        
    Example:
        token = create_access_token({"sub": user_id})
    """
    to_encode = data.copy()
    # E2-S2: always include a jti for per-token revocation support
    if "jti" not in to_encode:
        to_encode["jti"] = str(uuid4())
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
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


# ── Refresh token helpers (E1-S1, E1-S3, E2-S1) ───────────────────────────────

async def generate_refresh_token(user_id: str) -> tuple[str, str]:
    """Create a signed refresh JWT and persist its jti in Redis.

    Args:
        user_id: Customer UUID string.

    Returns:
        (token, jti) — the signed JWT string and its unique identifier.
    """
    from core.redis_client import get_async_redis

    jti = str(uuid4())
    expire = datetime.utcnow() + timedelta(seconds=REFRESH_TOKEN_TTL_SECONDS)
    claims = {
        "sub": user_id,
        "jti": jti,
        "exp": expire,
        "token_type": "refresh",
        "iss": "waooaw.com",
    }
    token = jwt.encode(claims, settings.secret_key, algorithm=settings.algorithm)

    r = get_async_redis()
    await r.set(f"refresh_token:{jti}", user_id, ex=REFRESH_TOKEN_TTL_SECONDS)

    return token, jti


async def is_refresh_token_valid(jti: str) -> bool:
    """Return True if the refresh token jti exists in Redis (not revoked/expired)."""
    from core.redis_client import get_async_redis

    r = get_async_redis()
    return bool(await r.exists(f"refresh_token:{jti}"))


async def revoke_refresh_token(jti: str) -> None:
    """Delete a refresh token jti from Redis, immediately revoking it."""
    from core.redis_client import get_async_redis

    r = get_async_redis()
    await r.delete(f"refresh_token:{jti}")


def decode_refresh_token_unverified(token: str) -> dict:
    """Decode refresh token payload without signature verification.

    Used for extracting jti during logout when the token may be expired.
    Returns empty dict on any error.
    """
    try:
        return jwt.get_unverified_claims(token)
    except Exception:
        return {}


# ── Circuit-breaker decorator (EXEC-ENGINE-001) ───────────────────────────────


def circuit_breaker(service: str):
    """Decorator that marks an async function as an external service call.

    In this MVP implementation the decorator acts as a pass-through while
    providing a consistent annotation point for every external HTTP call site.
    A production-grade implementation would track failure rates per *service*
    and open/half-open/close the circuit automatically.

    Usage::

        @circuit_breaker(service="delta_exchange_api")
        async def _fetch_candles(self, instrument: str, api_key: str) -> list[dict]:
            ...
    """
    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            return await fn(*args, **kwargs)
        return wrapper
    return decorator


# ── Access token revocation helpers (E2-S2) ───────────────────────────────────

async def revoke_access_token(jti: str, remaining_ttl_seconds: int) -> None:
    """Add an access token jti to the Redis revocation list.

    Args:
        jti: The jti claim from the access token.
        remaining_ttl_seconds: TTL for the Redis key (matches token remaining lifetime).
    """
    from core.redis_client import get_async_redis

    if remaining_ttl_seconds <= 0:
        return  # already expired — no need to store
    r = get_async_redis()
    await r.set(f"revoked_access:{jti}", "1", ex=remaining_ttl_seconds)


# ── Token version cache (E2-S3) ────────────────────────────────────────────────

TOKEN_VERSION_CACHE_TTL = 300  # 5 minutes


async def cache_token_version(user_id: str, version: int) -> None:
    """Store the current token_version for a user in Redis (TTL 5 min).

    Written at login time so the Gateway can perform near-instant version checks
    without a DB call on every request.
    """
    from core.redis_client import get_async_redis

    r = get_async_redis()
    await r.set(f"token_version:{user_id}", str(version), ex=TOKEN_VERSION_CACHE_TTL)

