"""
Gateway Auth Middleware (GW-100)
Version: 1.0
Purpose: JWT validation, claim extraction, request context enrichment

Features:
- JWT signature verification (RS256 algorithm)
- Token expiration validation
- Issuer verification (iss claim must be "waooaw.com")
- Extract claims to request.state (user_id, email, roles, trial_mode, etc.)
- Handle expired/invalid/missing tokens (401 Unauthorized)
- Support for Bearer token authentication
- Public endpoints bypass (health checks, docs)
- Performance: <5ms overhead per request

Dependencies:
- PyJWT (JWT encoding/decoding)
- cryptography (RSA signature verification)
- FastAPI (middleware framework)

Environment Variables:
- JWT_PUBLIC_KEY: RSA public key for signature verification (PEM format)
- JWT_ALGORITHM: Algorithm (default: RS256)
- JWT_ISSUER: Expected issuer (default: waooaw.com)
- JWT_AUDIENCE: Expected audience (optional)
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import jwt
from jwt import PyJWTError, ExpiredSignatureError, InvalidTokenError
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from time import monotonic
from collections import deque
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

import httpx
logger = logging.getLogger(__name__)

# JWT configuration from environment
JWT_PUBLIC_KEY = os.environ.get("JWT_PUBLIC_KEY", "").replace("\\n", "\n")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "RS256")
JWT_ISSUER = os.environ.get("JWT_ISSUER", "waooaw.com")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE")  # Optional

# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = [
    "/health",
    "/healthz",
    "/ready",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/metrics",
]

# Some deployments sit behind a proxy that prefixes application routes with `/api`.
# Treat the `/api/*` equivalents of public endpoints as public as well.
PUBLIC_ENDPOINTS = PUBLIC_ENDPOINTS + [
    f"/api{path}" for path in PUBLIC_ENDPOINTS if not path.startswith("/api/")
]

CUSTOMERS_ENDPOINT_PREFIX = "/api/v1/customers"
NOTIFICATION_EVENTS_INGEST_PATH = "/api/v1/notifications/events"

# Anti-abuse header for CP→Plant registration calls.
CP_REGISTRATION_KEY_HEADER = "X-CP-Registration-Key"
CP_REGISTRATION_KEY_ENV = "CP_REGISTRATION_KEY"


def _is_public_path(path: str) -> bool:
    normalized = (path or "").rstrip("/") or "/"
    if normalized in {p.rstrip("/") or "/" for p in PUBLIC_ENDPOINTS}:
        return True
    # Note: Health endpoints may have nested paths (e.g. /api/health/stream).
    if normalized.startswith("/api/health/") or normalized == "/api/health":
        return True
    return False


def _is_customers_path(path: str) -> bool:
    normalized = (path or "").rstrip("/")
    return normalized == CUSTOMERS_ENDPOINT_PREFIX or normalized.startswith(CUSTOMERS_ENDPOINT_PREFIX + "/")


def _is_notification_events_ingest_path(request: Request) -> bool:
    if request.method.upper() != "POST":
        return False
    normalized = (request.url.path or "").rstrip("/")
    return normalized == NOTIFICATION_EVENTS_INGEST_PATH


def _validate_registration_key(request: Request) -> Optional[JSONResponse]:
    expected = (os.environ.get(CP_REGISTRATION_KEY_ENV) or "").strip()
    provided = (request.headers.get(CP_REGISTRATION_KEY_HEADER) or "").strip()

    if not expected:
        logger.error("%s not configured; refusing customer registration traffic", CP_REGISTRATION_KEY_ENV)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "type": "https://waooaw.com/errors/internal-server-error",
                "title": "Internal Server Error",
                "status": 500,
                "detail": f"{CP_REGISTRATION_KEY_ENV} not configured",
                "instance": request.url.path,
            },
        )

    if not provided or provided != expected:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "type": "https://waooaw.com/errors/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": "Missing or invalid registration key",
                "instance": request.url.path,
            },
        )

    return None


AUTH_ENDPOINT_PREFIX = "/api/v1/auth"


class _InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: Dict[str, deque[float]] = {}

    def allow(self, key: str, *, limit: int, window_seconds: int) -> bool:
        if limit <= 0:
            return True

        now = monotonic()
        q = self._events.get(key)
        if q is None:
            q = deque()
            self._events[key] = q

        cutoff = now - float(window_seconds)
        while q and q[0] <= cutoff:
            q.popleft()

        if len(q) >= limit:
            return False

        q.append(now)
        return True


_auth_rate_limiter = _InMemoryRateLimiter()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    if request.client is None:
        return "unknown"
    return request.client.host or "unknown"


def _rate_limit_auth_endpoints(request: Request) -> Optional[JSONResponse]:
    path = request.url.path or ""
    if not (path == AUTH_ENDPOINT_PREFIX or path.startswith(AUTH_ENDPOINT_PREFIX + "/")):
        return None

    try:
        per_minute = int(os.environ.get("GW_AUTH_RATE_LIMIT_PER_MINUTE", "30"))
    except ValueError:
        per_minute = 30

    key = f"auth:{_client_ip(request)}"
    allowed = _auth_rate_limiter.allow(key, limit=per_minute, window_seconds=60)
    if allowed:
        return None

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "type": "https://waooaw.com/errors/too-many-requests",
            "title": "Too Many Requests",
            "status": 429,
            "detail": "Too many authentication requests. Please retry shortly.",
            "instance": request.url.path,
        },
        headers={"Retry-After": "60"},
    )


async def _plant_validate_customer_context(request: Request, bearer_token: str) -> Dict[str, Any]:
    """Validate token with Plant and return normalized customer context.

    Expected response body is the Plant backend's TokenValidateResponse.
    """

    plant_backend_url = (os.getenv("PLANT_BACKEND_URL") or "").rstrip("/")
    if not plant_backend_url:
        raise RuntimeError("PLANT_BACKEND_URL not configured")

    url = f"{plant_backend_url}/api/v1/auth/validate"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "X-Original-Authorization": f"Bearer {bearer_token}",
        "X-Forwarded-For": _client_ip(request),
        "User-Agent": request.headers.get("user-agent") or "plant-gateway",
    }

    async with httpx.AsyncClient(timeout=5.0) as client:
        res = await client.get(url, headers=headers)

    if res.status_code == status.HTTP_200_OK:
        data = res.json()
        if not isinstance(data, dict) or not data.get("valid"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return data

    if res.status_code in {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if res.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Customer not found")

    logger.warning("Plant validate failed: status=%s body=%s", res.status_code, res.text[:2000])
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Auth service unavailable")


class JWTClaims:
    """
    JWT claims data class.
    
    Conforms to JWT_CONTRACT.md specification:
    - user_id (UUID): Unique user identifier
    - email (string): User email address
    - customer_id (UUID): Customer/organization ID
    - roles (string[]): User roles (e.g., ["user"], ["admin", "agent_orchestrator"])
    - governor_agent_id (string|null): Governor agent ID (if Governor user)
    - trial_mode (boolean): Whether user is in trial mode
    - trial_expires_at (string|null): ISO 8601 trial expiration timestamp
    - iat (number): Issued at timestamp (Unix epoch)
    - exp (number): Expiration timestamp (Unix epoch)
    - iss (string): Issuer (must be "waooaw.com")
    - sub (string): Subject (user_id as string)
    """
    
    def __init__(self, payload: Dict[str, Any]):
        """
        Initialize JWT claims from decoded payload.
        
        Args:
            payload: Decoded JWT payload
        
        Raises:
            ValueError: If required claims are missing
        """
        # Required claims (per JWT_CONTRACT.md)
        self.user_id: str = payload.get("user_id")
        self.email: str = payload.get("email")
        self.customer_id: Optional[str] = payload.get("customer_id")
        self.roles: List[str] = payload.get("roles", [])
        self.iat: int = payload.get("iat")
        self.exp: int = payload.get("exp")
        self.iss: str = payload.get("iss")
        self.sub: str = payload.get("sub")
        
        # Optional claims
        self.governor_agent_id: Optional[str] = payload.get("governor_agent_id")
        self.trial_mode: bool = payload.get("trial_mode", False)
        self.trial_expires_at: Optional[str] = payload.get("trial_expires_at")
        
        # Validate required claims
        if not self.user_id:
            raise ValueError("Missing required claim: user_id")
        if not self.email:
            raise ValueError("Missing required claim: email")
        if not self.roles:
            raise ValueError("Missing required claim: roles")
        if not self.iat:
            raise ValueError("Missing required claim: iat")
        if not self.exp:
            raise ValueError("Missing required claim: exp")
        if not self.iss:
            raise ValueError("Missing required claim: iss")
        if not self.sub:
            raise ValueError("Missing required claim: sub")
        
        # Validate trial mode requirements
        if self.trial_mode and not self.trial_expires_at:
            raise ValueError("trial_expires_at required when trial_mode is true")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert claims to dictionary."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "customer_id": self.customer_id,
            "roles": self.roles,
            "governor_agent_id": self.governor_agent_id,
            "trial_mode": self.trial_mode,
            "trial_expires_at": self.trial_expires_at,
            "iat": self.iat,
            "exp": self.exp,
            "iss": self.iss,
            "sub": self.sub,
        }
    
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return "admin" in self.roles
    
    def is_governor(self) -> bool:
        """Check if user is a Governor (admin with governor_agent_id)."""
        return self.is_admin() and self.governor_agent_id is not None
    
    def is_trial_expired(self) -> bool:
        """Check if trial period has expired."""
        if not self.trial_mode or not self.trial_expires_at:
            return False
        
        try:
            from datetime import datetime
            trial_expiry = datetime.fromisoformat(self.trial_expires_at.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > trial_expiry
        except Exception as e:
            logger.error(f"Error parsing trial_expires_at: {e}")
            return True  # Treat parse errors as expired


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    """
    Extract JWT from Authorization header.
    
    Args:
        authorization_header: Authorization header value (e.g., "Bearer eyJhbGc...")
    
    Returns:
        JWT token string, or None if invalid format
    """
    if not authorization_header:
        return None
    
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]


def validate_jwt(token: str) -> JWTClaims:
    """
    Validate JWT and extract claims.
    
    Args:
        token: JWT token string
    
    Returns:
        JWTClaims object with validated claims
    
    Raises:
        ExpiredSignatureError: Token has expired
        InvalidTokenError: Token signature invalid or claims missing
        ValueError: Required claims missing or invalid
    """
    # NOTE: The module-level JWT_* values are read at import time for
    # performance, but tests and some deployments may override env vars at
    # runtime (e.g., key rotation). Prefer the current environment.
    jwt_public_key = os.environ.get("JWT_PUBLIC_KEY", "").replace("\\n", "\n") or JWT_PUBLIC_KEY
    jwt_algorithm = os.environ.get("JWT_ALGORITHM") or JWT_ALGORITHM
    jwt_issuer = os.environ.get("JWT_ISSUER") or JWT_ISSUER
    jwt_audience = os.environ.get("JWT_AUDIENCE") or JWT_AUDIENCE

    if not jwt_public_key:
        raise RuntimeError("JWT_PUBLIC_KEY environment variable not configured")
    
    try:
        # Decode and verify JWT
        payload = jwt.decode(
            token,
            jwt_public_key,
            algorithms=[jwt_algorithm],
            issuer=jwt_issuer,
            audience=jwt_audience if jwt_audience else None,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": True,
                "require": ["user_id", "email", "roles", "iat", "exp", "iss", "sub"],
            }
        )
        
        # Parse claims
        claims = JWTClaims(payload)
        
        logger.debug(f"JWT validated successfully for user {claims.user_id}")
        return claims
    
    except ExpiredSignatureError:
        logger.warning("JWT expired")
        raise
    except InvalidTokenError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise
    except ValueError as e:
        logger.error(f"JWT claims validation failed: {e}")
        raise InvalidTokenError(str(e))


class AuthMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for JWT authentication.
    
    Responsibilities:
    1. Extract JWT from Authorization header
    2. Validate JWT signature and claims
    3. Attach claims to request.state.jwt
    4. Return 401 Unauthorized for invalid/missing tokens
    5. Skip authentication for public endpoints
    
    Usage:
        from gateway.middleware.auth import AuthMiddleware
        
        app = FastAPI()
        app.add_middleware(AuthMiddleware)
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process request through auth middleware.
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/endpoint in chain
        
        Returns:
            Response object
        """
        if _is_customers_path(request.url.path):
            denial = _validate_registration_key(request)
            if denial is not None:
                return denial
            return await call_next(request)

        if _is_notification_events_ingest_path(request):
            denial = _validate_registration_key(request)
            if denial is not None:
                return denial
            return await call_next(request)

        # Skip authentication for public endpoints.
        if _is_public_path(request.url.path):
            logger.debug(f"Skipping auth for public endpoint: {request.url.path}")
            return await call_next(request)

        denial = _rate_limit_auth_endpoints(request)
        if denial is not None:
            return denial
        
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning(f"Missing Authorization header for {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "type": "https://waooaw.com/errors/unauthorized",
                    "title": "Unauthorized",
                    "status": 401,
                    "detail": "Missing Authorization header. Please provide a valid Bearer token.",
                    "instance": request.url.path,
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract Bearer token
        token = extract_bearer_token(auth_header)
        if not token:
            logger.warning(f"Invalid Authorization header format for {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "type": "https://waooaw.com/errors/invalid-token-format",
                    "title": "Invalid Token Format",
                    "status": 401,
                    "detail": "Authorization header must be in format: Bearer <token>",
                    "instance": request.url.path,
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate JWT
        try:
            claims = validate_jwt(token)

            always_validate_with_plant = (os.getenv("GW_ALWAYS_VALIDATE_WITH_PLANT") or "false").lower() in {
                "1",
                "true",
                "yes",
            }

            # Default to enabling Plant-backed enrichment when customer_id is missing.
            # This keeps the gateway resilient to older/partial JWTs while still avoiding
            # extra calls when customer_id is already present.
            allow_customer_enrichment = (os.getenv("GW_ALLOW_PLANT_CUSTOMER_ENRICHMENT") or "true").lower() in {
                "1",
                "true",
                "yes",
            }

            if always_validate_with_plant or (allow_customer_enrichment and not (claims.customer_id or "").strip()):
                plant_ctx = await _plant_validate_customer_context(request, token)
                customer_id = plant_ctx.get("customer_id")
                email_norm = plant_ctx.get("email")
                if isinstance(customer_id, str) and customer_id.strip():
                    claims.customer_id = customer_id.strip()
                if isinstance(email_norm, str) and email_norm.strip():
                    claims.email = email_norm.strip().lower()
            
            # Attach claims to request state
            # Most gateway middlewares treat request.state.jwt as a dict-like object
            # (calling .get()). Keep that contract while also exposing the typed
            # claims object for route-level dependencies.
            request.state.jwt = claims.to_dict()
            request.state.jwt_claims = claims
            request.state.user_id = claims.user_id
            request.state.customer_id = claims.customer_id
            request.state.roles = claims.roles
            request.state.trial_mode = claims.trial_mode
            
            logger.info(f"Authenticated user {claims.user_id} for {request.method} {request.url.path}")
            
            # Proceed to next middleware/endpoint
            response = await call_next(request)
            return response

        except HTTPException as e:
            # Raised by Plant-backed validation helpers.
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "type": "https://waooaw.com/errors/unauthorized"
                    if e.status_code == status.HTTP_401_UNAUTHORIZED
                    else "https://waooaw.com/errors/service-unavailable"
                    if e.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                    else "https://waooaw.com/errors/error",
                    "title": "Unauthorized"
                    if e.status_code == status.HTTP_401_UNAUTHORIZED
                    else "Service Unavailable"
                    if e.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                    else "Error",
                    "status": e.status_code,
                    "detail": str(e.detail),
                    "instance": request.url.path,
                },
                headers={"WWW-Authenticate": "Bearer"}
                if e.status_code == status.HTTP_401_UNAUTHORIZED
                else None,
            )
        
        except ExpiredSignatureError:
            logger.warning(f"Expired JWT for {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "type": "https://waooaw.com/errors/token-expired",
                    "title": "Token Expired",
                    "status": 401,
                    "detail": "Your authentication token has expired. Please log in again.",
                    "instance": request.url.path,
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        except InvalidTokenError as e:
            logger.warning(f"Invalid JWT for {request.url.path}: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "type": "https://waooaw.com/errors/invalid-token",
                    "title": "Invalid Token",
                    "status": 401,
                    "detail": f"Token validation failed: {str(e)}",
                    "instance": request.url.path,
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        except Exception as e:
            logger.error(f"Unexpected error in auth middleware: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "type": "https://waooaw.com/errors/internal-server-error",
                    "title": "Internal Server Error",
                    "status": 500,
                    "detail": "An unexpected error occurred during authentication.",
                    "instance": request.url.path,
                }
            )


# Dependency for route-level auth (alternative to middleware)
async def get_current_user(request: Request) -> JWTClaims:
    """
    FastAPI dependency to get current authenticated user.
    
    Usage:
        from gateway.middleware.auth import get_current_user
        
        @app.get("/api/v1/profile")
        async def get_profile(user: JWTClaims = Depends(get_current_user)):
            return {"user_id": user.user_id, "email": user.email}
    
    Args:
        request: FastAPI Request object
    
    Returns:
        JWTClaims object
    
    Raises:
        HTTPException: 401 if not authenticated
    """
    if not hasattr(request.state, "jwt") and not hasattr(request.state, "jwt_claims"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = getattr(request.state, "jwt_claims", None)
    if claims is not None:
        return claims

    # Fallback for callers/tests that may have set request.state.jwt to a dict
    jwt_dict = getattr(request.state, "jwt", None)
    if isinstance(jwt_dict, dict):
        return JWTClaims(jwt_dict)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
