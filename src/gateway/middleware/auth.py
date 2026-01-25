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
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

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
    # NOTE: JWT_PUBLIC_KEY is read at module import time for performance, but
    # tests (and some deployments) may set env vars after import. Re-check env
    # at call time to avoid stale empty config.
    jwt_public_key = JWT_PUBLIC_KEY or os.environ.get("JWT_PUBLIC_KEY", "").replace("\\n", "\n")
    jwt_algorithm = os.environ.get("JWT_ALGORITHM", JWT_ALGORITHM)
    jwt_issuer = os.environ.get("JWT_ISSUER", JWT_ISSUER)
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
        # Skip authentication for public endpoints
        if request.url.path in PUBLIC_ENDPOINTS:
            logger.debug(f"Skipping auth for public endpoint: {request.url.path}")
            return await call_next(request)
        
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
            
            # Attach claims to request state
            request.state.jwt = claims
            request.state.user_id = claims.user_id
            request.state.customer_id = claims.customer_id
            request.state.roles = claims.roles
            request.state.trial_mode = claims.trial_mode
            
            logger.info(f"Authenticated user {claims.user_id} for {request.method} {request.url.path}")
            
            # Proceed to next middleware/endpoint
            response = await call_next(request)
            return response
        
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
    if not hasattr(request.state, "jwt"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return request.state.jwt
