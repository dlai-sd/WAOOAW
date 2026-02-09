"""
RBAC Middleware - GW-101

Role-Based Access Control for Partner Platform (PP) Gateway.
Queries OPA rbac_pp policy to enforce hierarchical role permissions.

7-Role Hierarchy:
- admin: Full platform access
- customer_admin: Manage customer account
- developer: API access, deploy agents
- manager: View agents, reports
- analyst: View data, reports
- support: View customer data
- viewer: Read-only access

25+ Permissions covering agent management, deployment, API access, customer management.
"""

import httpx
import logging
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dataclasses import dataclass, asdict

try:
    from ..infrastructure.feature_flags.feature_flags import FeatureFlagService, FeatureFlagContext
except ImportError:  # pragma: no cover
    from infrastructure.feature_flags.feature_flags import FeatureFlagService, FeatureFlagContext

logger = logging.getLogger(__name__)


@dataclass
class UserInfo:
    """User information extracted from OPA RBAC response."""
    
    user_id: str
    email: str
    roles: list[str]
    role_level: int  # 1 (admin) to 7 (viewer)
    is_admin: bool
    permissions: list[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions


class RBACMiddleware(BaseHTTPMiddleware):
    """
    RBAC Middleware for Partner Platform Gateway.
    
    Queries OPA rbac_pp policy to enforce role-based permissions.
    Only runs on PP Gateway (skipped on CP Gateway).
    
    Flow:
    1. Extract JWT claims from request.state.jwt (set by AuthMiddleware)
    2. Extract resource and action from request (path, method)
    3. Query OPA: POST /v1/data/gateway/rbac_pp/allow
    4. If allowed, attach user_info to request.state
    5. If denied, return 403 Forbidden with deny_reason
    
    Configuration:
    - OPA_SERVICE_URL: OPA endpoint (e.g., "http://opa:8181")
    - GATEWAY_TYPE: "PP" or "CP" (only runs on PP)
    - RBAC_TIMEOUT: OPA query timeout in seconds (default: 2)
    """
    
    def __init__(
        self,
        app,
        opa_service_url: str,
        gateway_type: str,
        feature_flag_service: Optional[FeatureFlagService] = None,
        timeout: int = 2
    ):
        super().__init__(app)
        self.opa_service_url = opa_service_url.rstrip("/")
        self.gateway_type = gateway_type.upper()
        self.feature_flag_service = feature_flag_service
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def dispatch(self, request: Request, call_next):
        """
        Intercept request, query OPA RBAC policy, enforce permissions.
        """
        # Skip RBAC on CP Gateway (only for Partner Platform)
        if self.gateway_type != "PP":
            return await call_next(request)
        
        # Check feature flag (allow disabling RBAC for rollout)
        if self.feature_flag_service:
            jwt_claims = getattr(request.state, "jwt", None)
            if jwt_claims:
                context = FeatureFlagContext(
                    user_id=jwt_claims.get("user_id"),
                    customer_id=jwt_claims.get("customer_id"),
                    email=jwt_claims.get("email"),
                    trial_mode=jwt_claims.get("trial_mode", False),
                    roles=jwt_claims.get("roles", []),
                    gateway_type=self.gateway_type
                )
                
                if not self.feature_flag_service.is_enabled("enable_rbac_pp", context, default=True):
                    logger.info(f"RBAC disabled via feature flag for user {jwt_claims.get('user_id')}")
                    return await call_next(request)
        
        # Skip public endpoints (health checks, metrics)
        path = request.url.path
        if (
            path in ["/health", "/healthz", "/ready", "/metrics", "/docs", "/redoc", "/openapi.json"]
            or path == "/api/health"
            or path.startswith("/api/health/")
        ):
            return await call_next(request)
        
        # Extract JWT claims (set by AuthMiddleware)
        jwt_claims = getattr(request.state, "jwt", None)
        if not jwt_claims:
            logger.error("RBAC middleware called without JWT claims (AuthMiddleware missing?)")
            return JSONResponse(
                status_code=500,
                content={
                    "type": "https://waooaw.com/errors/internal-server-error",
                    "title": "Internal Server Error",
                    "status": 500,
                    "detail": "RBAC middleware requires JWT claims (ensure AuthMiddleware runs first)",
                    "instance": str(request.url)
                }
            )
        
        # Extract resource and action from request
        resource, action = self._extract_resource_action(request)
        
        # Build OPA input
        opa_input = {
            "resource": resource,
            "action": action,
            "jwt": jwt_claims
        }
        
        try:
            # Query OPA rbac_pp policy
            opa_response = await self._query_opa(opa_input)
            
            if not opa_response.get("result", {}).get("allow", False):
                # Permission denied
                deny_reason = opa_response.get("result", {}).get("deny_reason", "Insufficient permissions")
                user_id = jwt_claims.get("user_id", "unknown")
                roles = jwt_claims.get("roles", [])
                
                logger.warning(
                    f"RBAC denied: user={user_id}, roles={roles}, "
                    f"resource={resource}, action={action}, reason={deny_reason}"
                )
                
                return JSONResponse(
                    status_code=403,
                    content={
                        "type": "https://waooaw.com/errors/permission-denied",
                        "title": "Permission Denied",
                        "status": 403,
                        "detail": deny_reason,
                        "instance": str(request.url),
                        "resource": resource,
                        "action": action,
                        "required_permission": f"{action}:{resource}"
                    }
                )
            
            # Extract user_info from OPA response
            user_info_data = opa_response.get("result", {}).get("user_info", {})
            user_info = UserInfo(
                user_id=user_info_data.get("user_id", jwt_claims.get("user_id")),
                email=user_info_data.get("email", jwt_claims.get("email")),
                roles=user_info_data.get("roles", jwt_claims.get("roles", [])),
                role_level=user_info_data.get("role_level", 7),  # Default to viewer
                is_admin=user_info_data.get("is_admin", False),
                permissions=user_info_data.get("permissions", [])
            )
            
            # Attach user_info to request state
            request.state.user_info = user_info
            
            logger.info(
                f"RBAC allowed: user={user_info.user_id}, roles={user_info.roles}, "
                f"resource={resource}, action={action}"
            )
            
            # Continue to next middleware
            response = await call_next(request)
            
            # Add RBAC headers to response
            response.headers["X-RBAC-User-ID"] = user_info.user_id
            response.headers["X-RBAC-Roles"] = ",".join(user_info.roles)
            response.headers["X-RBAC-Role-Level"] = str(user_info.role_level)
            
            return response
            
        except httpx.TimeoutException:
            logger.error(f"OPA RBAC query timeout after {self.timeout}s")
            return JSONResponse(
                status_code=503,
                content={
                    "type": "https://waooaw.com/errors/service-unavailable",
                    "title": "Service Unavailable",
                    "status": 503,
                    "detail": f"RBAC service timeout after {self.timeout}s",
                    "instance": str(request.url)
                }
            )
        except Exception as e:
            logger.error(f"RBAC middleware error: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "type": "https://waooaw.com/errors/internal-server-error",
                    "title": "Internal Server Error",
                    "status": 500,
                    "detail": f"RBAC error: {str(e)}",
                    "instance": str(request.url)
                }
            )
    
    def _extract_resource_action(self, request: Request) -> tuple[str, str]:
        """
        Extract resource and action from HTTP request.
        
        Examples:
        - GET /api/v1/agents → resource="agents", action="read"
        - POST /api/v1/agents → resource="agents", action="create"
        - PUT /api/v1/agents/123 → resource="agents", action="update"
        - DELETE /api/v1/agents/123 → resource="agents", action="delete"
        - POST /api/v1/deployments → resource="deployments", action="deploy"
        """
        path = request.url.path
        method = request.method.upper()
        
        # Remove /api/v1 prefix
        if path.startswith("/api/v1/"):
            path = path[8:]  # Remove "/api/v1/"
        
        # Extract resource (first path segment)
        parts = path.strip("/").split("/")
        resource = parts[0] if parts and parts[0] else "unknown"
        
        # Map HTTP method to action
        action_map = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete"
        }
        
        # Special cases for specific endpoints
        if resource == "deployments" and method == "POST":
            action = "deploy"
        elif resource == "agents" and len(parts) >= 3:
            # /agents/123/pause → action="pause"
            # /agents/123/resume → action="resume"
            if parts[2] in ["pause", "resume", "restart", "logs"]:
                action = parts[2]
            else:
                action = action_map.get(method, "unknown")
        else:
            action = action_map.get(method, "unknown")
        
        return resource, action
    
    async def _query_opa(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query OPA rbac_pp policy.
        
        POST /v1/data/gateway/rbac_pp/allow
        {
            "input": {
                "resource": "agents",
                "action": "create",
                "jwt": {...}
            }
        }
        
        Response:
        {
            "result": {
                "allow": true,
                "user_info": {
                    "user_id": "user123",
                    "email": "user@example.com",
                    "roles": ["developer"],
                    "role_level": 3,
                    "is_admin": false,
                    "permissions": ["read:agents", "create:agents", ...]
                }
            }
        }
        """
        url = f"{self.opa_service_url}/v1/data/gateway/rbac_pp/allow"
        
        response = await self.client.post(
            url,
            json={"input": input_data}
        )
        
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# FastAPI dependency for route-level RBAC checks
def require_permission(permission: str):
    """
    FastAPI dependency to require specific permission.
    
    Usage:
    @app.post("/api/v1/agents", dependencies=[Depends(require_permission("create:agents"))])
    async def create_agent(request: Request):
        ...
    """
    async def check_permission(request: Request):
        user_info: Optional[UserInfo] = getattr(request.state, "user_info", None)
        
        if not user_info:
            raise HTTPException(
                status_code=500,
                detail="RBAC middleware not configured (user_info missing)"
            )
        
        if not user_info.has_permission(permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: requires {permission}"
            )
        
        return user_info
    
    return check_permission


def require_role(role: str):
    """
    FastAPI dependency to require specific role.
    
    Usage:
    @app.delete("/api/v1/agents/{agent_id}", dependencies=[Depends(require_role("admin"))])
    async def delete_agent(agent_id: str, request: Request):
        ...
    """
    async def check_role(request: Request):
        user_info: Optional[UserInfo] = getattr(request.state, "user_info", None)
        
        if not user_info:
            raise HTTPException(
                status_code=500,
                detail="RBAC middleware not configured (user_info missing)"
            )
        
        if role not in user_info.roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role denied: requires {role} role"
            )
        
        return user_info
    
    return check_role
