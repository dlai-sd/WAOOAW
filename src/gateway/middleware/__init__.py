"""
WAOOAW API Gateway Middleware Package

Constitutional enforcement middleware for CP (Customer Portal) and PP (Partner Platform) gateways.

Middleware Chain (execution order):
1. ErrorHandlingMiddleware (GW-105): Wraps all middleware, catches exceptions
2. AuditLoggingMiddleware (GW-104): Logs all requests/responses
3. AuthMiddleware (GW-100): JWT validation, attach user claims
4. RBACMiddleware (GW-101): Role-based access control (PP only)
5. PolicyMiddleware (GW-102): Trial mode, Governor approval, sandbox routing
6. BudgetGuardMiddleware (GW-103): Budget enforcement, block at 100%

Usage:
```python
from fastapi import FastAPI
from src.gateway.middleware import setup_middleware

app = FastAPI()
setup_middleware(
    app,
    gateway_type="CP",
    opa_service_url="http://opa:8181",
    redis_url="redis://redis:6379",
    database_url="postgresql://...",
    approval_ui_url="https://approval.waooaw.com"
)
```
"""

from .auth import AuthMiddleware, JWTClaims, validate_jwt, get_current_user
from .rbac import RBACMiddleware, UserInfo, require_permission, require_role
from .policy import PolicyMiddleware
from .budget import BudgetGuardMiddleware
from .audit_logging_middleware import AuditLoggingMiddleware
from .error_handler import setup_error_handlers, create_problem_details

from typing import Optional
from fastapi import FastAPI
from infrastructure.feature_flags.feature_flags import FeatureFlagService


def setup_middleware(
    app: FastAPI,
    gateway_type: str,
    opa_service_url: str,
    redis_url: str,
    database_url: str,
    approval_ui_url: str,
    jwt_public_key: str,
    jwt_issuer: str = "waooaw.com",
    feature_flag_service: Optional[FeatureFlagService] = None,
    environment: str = "production"
):
    """
    Set up all gateway middleware in correct order.
    
    Args:
        app: FastAPI application
        gateway_type: "CP" (Customer Portal) or "PP" (Partner Platform)
        opa_service_url: OPA service endpoint (e.g., "http://opa:8181")
        redis_url: Redis connection string (e.g., "redis://redis:6379")
        database_url: PostgreSQL connection string
        approval_ui_url: Governor approval UI URL
        jwt_public_key: RSA public key for JWT verification
        jwt_issuer: JWT issuer (default: "waooaw.com")
        feature_flag_service: Optional LaunchDarkly service
        environment: "production" or "development"
    
    Middleware Order (outer to inner):
    1. ErrorHandlers: Exception handlers (RFC 7807 format)
    2. AuditLoggingMiddleware: Log all requests
    3. AuthMiddleware: JWT validation
    4. RBACMiddleware: Role-based access (PP only)
    5. PolicyMiddleware: Trial/Governor/Sandbox
    6. BudgetGuardMiddleware: Budget enforcement
    """
    
    # 1. Error Handling (exception handlers - NOT middleware)
    setup_error_handlers(
        app,
        environment=environment,
        include_trace=(environment == "development")
    )
    
    # 2. Audit Logging (log everything, including errors)
    app.add_middleware(
        AuditLoggingMiddleware,
        database_url=database_url,
        gateway_type=gateway_type,
        batch_interval=5,  # Flush every 5 seconds
        batch_size=100  # Max 100 logs per batch
    )
    
    # 3. Authentication (JWT validation)
    app.add_middleware(
        AuthMiddleware,
        jwt_public_key=jwt_public_key,
        jwt_issuer=jwt_issuer
    )
    
    # 4. RBAC (PP Gateway only)
    if gateway_type.upper() == "PP":
        app.add_middleware(
            RBACMiddleware,
            opa_service_url=opa_service_url,
            gateway_type=gateway_type,
            feature_flag_service=feature_flag_service,
            timeout=2
        )
    
    # 5. Policy Enforcement (Trial, Governor, Sandbox)
    app.add_middleware(
        PolicyMiddleware,
        opa_service_url=opa_service_url,
        redis_url=redis_url,
        approval_ui_url=approval_ui_url,
        feature_flag_service=feature_flag_service,
        timeout=2
    )
    
    # 6. Budget Guard (innermost - closest to handler)
    app.add_middleware(
        BudgetGuardMiddleware,
        opa_service_url=opa_service_url,
        redis_url=redis_url,
        feature_flag_service=feature_flag_service,
        timeout=2
    )


__all__ = [
    # Middleware classes
    "AuthMiddleware",
    "RBACMiddleware",
    "PolicyMiddleware",
    "BudgetGuardMiddleware",
    "AuditLoggingMiddleware",
    "ErrorHandlingMiddleware",
    
    # Helper classes
    "JWTClaims",
    "UserInfo",
    
    # Helper functions
    "validate_jwt",
    "get_current_user",
    "require_permission",
    "require_role",
    "create_problem_details",
    
    # Setup function
    "setup_middleware"
]
