"""
Policy Middleware - GW-102

Constitutional enforcement via OPA policies:
- trial_mode: 10 tasks/day limit, expiration checks
- governor_role: 5 sensitive actions require approval
- sandbox_routing: Route trial users to sandbox backend

Queries 3 OPA policies in parallel for performance.
"""

import httpx
import os
import time
import base64
import json
import logging
import asyncio
try:
    from .circuit_breaker import CircuitBreaker, GatewayCircuitOpenError
except ImportError:  # pragma: no cover
    from middleware.circuit_breaker import CircuitBreaker, GatewayCircuitOpenError

_opa_cb = CircuitBreaker(service_name="opa-policy")  # P-1: fast-fail when OPA is down
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from ..infrastructure.feature_flags.feature_flags import FeatureFlagService, FeatureFlagContext
except ImportError:  # pragma: no cover
    from infrastructure.feature_flags.feature_flags import FeatureFlagService, FeatureFlagContext

try:
    from ..middleware.auth import _is_public_path
except ImportError:  # pragma: no cover
    from middleware.auth import _is_public_path

logger = logging.getLogger(__name__)

# ── OPA Cloud Run identity-token helpers ─────────────────────────────────────
_METADATA_OPA_IDENTITY_URLS = [
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity",
    "http://metadata/computeMetadata/v1/instance/service-accounts/default/identity",
]
_METADATA_OPA_HEADERS = {"Metadata-Flavor": "Google"}
_opa_id_token_cache: Tuple[Optional[str], float] = (None, 0.0)


def _jwt_expiry_epoch_seconds_opa(token: str) -> Optional[float]:
    """Best-effort parse of JWT exp without external deps."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode("utf-8")))
        exp = payload.get("exp")
        return float(exp) if exp is not None else None
    except Exception:
        return None


async def _get_opa_id_token(audience: str) -> Optional[str]:
    """Fetch (and cache) a Google identity token for OPA Cloud Run requests."""
    global _opa_id_token_cache
    token, expires_at = _opa_id_token_cache
    now = time.time()
    if token and now < (expires_at - 30):
        return token
    params = {"audience": audience, "format": "full"}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for url in _METADATA_OPA_IDENTITY_URLS:
            try:
                res = await client.get(url, headers=_METADATA_OPA_HEADERS, params=params)
                if res.status_code != 200:
                    continue
                token = res.text.strip()
                exp = _jwt_expiry_epoch_seconds_opa(token)
                expires_at = exp if exp else (now + 300)
                _opa_id_token_cache = (token, expires_at)
                return token
            except Exception:
                continue
    return None


class PolicyMiddleware(BaseHTTPMiddleware):
    """
    Policy Middleware for CP and PP Gateways.
    
    Enforces constitutional policies via OPA:
    1. Trial Mode Policy (GW-000-002):
       - 10 tasks/day limit for trial users
       - Block requests after expiration
       - Update Redis task count
    
    2. Governor Role Policy (GW-000-003):
       - 5 sensitive actions require Governor approval:
         * delete_agent, update_billing, change_subscription, export_data, delete_customer
       - Return 307 redirect to approval UI
    
    3. Sandbox Routing Policy (GW-000-005):
       - Trial users route to sandbox backend
       - Paid users route to production backend
       - Set X-Target-Backend header
    
    Configuration:
    - OPA_SERVICE_URL: OPA endpoint
    - REDIS_URL: Redis for task counts
    - APPROVAL_UI_URL: Governor approval UI
    - POLICY_TIMEOUT: OPA query timeout (default: 2s)
    """
    
    # Sensitive actions requiring Governor approval
    SENSITIVE_ACTIONS = [
        "delete_agent",
        "update_billing",
        "change_subscription",
        "export_data",
        "delete_customer"
    ]
    
    def __init__(
        self,
        app,
        opa_service_url: str,
        redis_url: str,
        approval_ui_url: str,
        feature_flag_service: Optional[FeatureFlagService] = None,
        timeout: int = 2
    ):
        super().__init__(app)
        self.opa_service_url = opa_service_url.rstrip("/")
        self.redis_url = redis_url
        self.approval_ui_url = approval_ui_url.rstrip("/")
        self.feature_flag_service = feature_flag_service
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def dispatch(self, request: Request, call_next):
        """
        Intercept request, query OPA policies, enforce constitutional rules.
        """
        # Always allow CORS preflight requests through.
        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        # Skip public endpoints — use the shared helper from AuthMiddleware so
        # this list stays in sync automatically (covers health, docs, mobile
        # auth/register, auth/otp/start, auth/otp/verify, google/verify, etc.).
        path = request.url.path
        if _is_public_path(path):
            return await call_next(request)

        # Also skip the customers upsert path and OTP sessions path (CP→Plant registration,
        # guarded by X-CP-Registration-Key in AuthMiddleware instead of a JWT).
        if path.rstrip("/").startswith("/api/v1/customers") or path.rstrip("/").startswith("/api/v1/otp/sessions"):
            return await call_next(request)
        
        # Extract JWT claims (set by AuthMiddleware)
        jwt_claims = getattr(request.state, "jwt", None)
        if not jwt_claims:
            logger.error("Policy middleware called without JWT claims")
            return JSONResponse(
                status_code=500,
                content={
                    "type": "https://waooaw.com/errors/internal-server-error",
                    "title": "Internal Server Error",
                    "status": 500,
                    "detail": "Policy middleware requires JWT claims",
                    "instance": str(request.url)
                }
            )
        
        # Check feature flags
        context = FeatureFlagContext(
            user_id=jwt_claims.get("user_id"),
            customer_id=jwt_claims.get("customer_id"),
            email=jwt_claims.get("email"),
            trial_mode=jwt_claims.get("trial_mode", False),
            roles=jwt_claims.get("roles", []),
            gateway_type=getattr(request.state, "gateway_type", "CP")
        )
        
        # Extract resource and action
        resource, action = self._extract_resource_action(request)
        
        # Build OPA inputs
        base_input = {
            "jwt": jwt_claims,
            "resource": resource,
            "action": action,
            "method": request.method,
            "path": path
        }
        
        try:
            # Query OPA policies in parallel (for performance)
            policies_to_query = []
            
            # 1. Trial Mode Policy (if user is in trial)
            if jwt_claims.get("trial_mode", False) and self.feature_flag_service and \
               self.feature_flag_service.is_enabled("enable_trial_mode", context, default=True):
                policies_to_query.append("trial_mode")
            
            # 2. Governor Role Policy (if sensitive action)
            if action in self.SENSITIVE_ACTIONS and self.feature_flag_service and \
               self.feature_flag_service.is_enabled("enable_governor_approval", context, default=True):
                policies_to_query.append("governor_role")
            
            # 3. Sandbox Routing Policy (always check)
            if self.feature_flag_service and \
               self.feature_flag_service.is_enabled("enable_sandbox_routing", context, default=True):
                policies_to_query.append("sandbox_routing")
            
            # Query all policies in parallel
            policy_results = await self._query_policies_parallel(base_input, policies_to_query)
            
            # Process policy results
            
            # 1. Check Trial Mode Policy
            if "trial_mode" in policy_results:
                trial_result = policy_results["trial_mode"]
                if not trial_result.get("allow", False):
                    return self._handle_trial_mode_denial(trial_result, request)
            
            # 2. Check Governor Role Policy
            if "governor_role" in policy_results:
                governor_result = policy_results["governor_role"]
                if not governor_result.get("allow", False):
                    return self._handle_governor_approval_required(governor_result, request, action)
            
            # 3. Apply Sandbox Routing
            if "sandbox_routing" in policy_results:
                routing_result = policy_results["sandbox_routing"]
                target_backend = routing_result.get("target_backend", "production")
                request.state.target_backend = target_backend
                
                logger.info(
                    f"Sandbox routing: user={jwt_claims.get('user_id')}, "
                    f"trial_mode={jwt_claims.get('trial_mode')}, target={target_backend}"
                )
            
            # Continue to next middleware
            response = await call_next(request)
            
            # Add policy headers to response
            response.headers["X-Policy-Trial-Mode"] = str(jwt_claims.get("trial_mode", False))
            if hasattr(request.state, "target_backend"):
                response.headers["X-Target-Backend"] = request.state.target_backend
            
            return response
            
        except (httpx.TimeoutException, GatewayCircuitOpenError):
            logger.error(f"OPA policy query timeout or circuit open after {self.timeout}s")
            return JSONResponse(
                status_code=503,
                content={
                    "type": "https://waooaw.com/errors/service-unavailable",
                    "title": "Service Unavailable",
                    "status": 503,
                    "detail": f"Policy service timeout after {self.timeout}s",
                    "instance": str(request.url)
                }
            )
        except Exception as e:
            logger.error(f"Policy middleware error: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "type": "https://waooaw.com/errors/internal-server-error",
                    "title": "Internal Server Error",
                    "status": 500,
                    "detail": f"Policy error: {str(e)}",
                    "instance": str(request.url)
                }
            )
    
    def _extract_resource_action(self, request: Request) -> tuple[str, str]:
        """Extract resource and action from request."""
        path = request.url.path
        method = request.method.upper()
        
        # Remove /api/v1 prefix
        if path.startswith("/api/v1/"):
            path = path[8:]
        
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
        
        # Special cases
        if resource == "agents":
            if method == "DELETE" and len(parts) <= 2:
                # DELETE /api/v1/agents/{id} — deleting the agent itself
                action = "delete_agent"
            elif method == "DELETE" and len(parts) > 2:
                # DELETE /api/v1/agents/{id}/{sub_resource}/... — deleting a child
                # (e.g. skill detachment: DELETE /api/v1/agents/{id}/skills/{skill_id})
                # NOT a delete_agent — re-classify by sub-resource to avoid
                # spurious governor_role checks and SENSITIVE_ACTION triggering.
                resource = parts[2]  # e.g. "skills"
                action = "delete"
            elif len(parts) >= 3 and parts[2] in ["pause", "resume", "delete"]:
                # POST /api/v1/agents/{id}/delete -> delete_agent
                action = f"{parts[2]}_agent"
            else:
                action = action_map.get(method, "unknown")
        elif resource == "billing" and method in ["PUT", "PATCH"]:
            action = "update_billing"
        elif resource == "subscription" and method in ["PUT", "PATCH"]:
            action = "change_subscription"
        elif resource == "data" and "export" in path:
            action = "export_data"
        elif resource == "customers" and method == "DELETE":
            action = "delete_customer"
        else:
            action = action_map.get(method, "unknown")
        
        return resource, action
    
    async def _query_policies_parallel(
        self,
        base_input: Dict[str, Any],
        policies: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Query multiple OPA policies in parallel for performance.
        
        Args:
            base_input: Common input data for all policies
            policies: List of policy names to query (trial_mode, governor_role, sandbox_routing)
        
        Returns:
            Dict mapping policy name to result
        """
        if not policies:
            return {}
        
        # Create async tasks for each policy
        tasks = {
            policy: self._query_opa_policy(policy, base_input)
            for policy in policies
        }
        
        # Wait for all policies to complete
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Map results back to policy names
        policy_results = {}
        for policy, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                # Re-raise TimeoutException to be caught by outer handler
                if isinstance(result, httpx.TimeoutException):
                    raise result
                logger.error(f"Policy {policy} query failed: {result}")
                # Fail open: allow request if policy query fails (non-timeout errors)
                policy_results[policy] = {"allow": True, "error": str(result)}
            else:
                policy_results[policy] = result.get("result", {})
        
        return policy_results
    
    async def _query_opa_policy(self, policy: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query a single OPA policy.
        
        POST /v1/data/gateway/{policy}/allow
        """
        url = f"{self.opa_service_url}/v1/data/gateway/{policy}/allow"

        if not _opa_cb.is_call_permitted():  # P-1: fast-fail when circuit is open
            raise GatewayCircuitOpenError("OPA/policy")
        opa_headers: Dict[str, str] = {}
        if os.getenv("K_SERVICE"):  # running on Cloud Run — attach identity token
            id_token = await _get_opa_id_token(self.opa_service_url)
            if id_token:
                opa_headers["Authorization"] = f"Bearer {id_token}"
        try:
            response = await self.client.post(
                url,
                json={"input": input_data},
                headers=opa_headers
            )
            response.raise_for_status()
            _opa_cb.record_success()
            return response.json()
        except (httpx.TimeoutException, httpx.ConnectError):
            _opa_cb.record_failure()
            raise
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500:
                _opa_cb.record_failure()
            raise
    
    def _handle_trial_mode_denial(self, result: Dict[str, Any], request: Request) -> JSONResponse:
        """
        Handle trial mode policy denial (limit exceeded or expired).
        """
        deny_reason = result.get("deny_reason", "Trial limit exceeded")
        task_count = result.get("task_count", 0)
        limit = result.get("limit", 10)
        trial_expires_at = result.get("trial_expires_at")
        
        # Check if expired or limit exceeded
        if "expired" in deny_reason.lower():
            status_code = 403
            error_type = "trial-expired"
            title = "Trial Expired"
            detail = deny_reason
            extra = {
                "trial_expires_at": trial_expires_at,
                "upgrade_url": "https://waooaw.com/upgrade"
            }
        else:
            status_code = 429
            error_type = "trial-limit-exceeded"
            title = "Trial Limit Exceeded"
            detail = deny_reason
            extra = {
                "task_count": task_count,
                "limit": limit,
                "reset_at": self._get_next_day_midnight(),
                "upgrade_url": "https://waooaw.com/upgrade"
            }
        
        logger.warning(
            f"Trial mode denial: user={request.state.jwt.get('user_id')}, "
            f"reason={deny_reason}, task_count={task_count}/{limit}"
        )
        
        return JSONResponse(
            status_code=status_code,
            content={
                "type": f"https://waooaw.com/errors/{error_type}",
                "title": title,
                "status": status_code,
                "detail": detail,
                "instance": str(request.url),
                **extra
            },
            headers={"Retry-After": "86400"} if status_code == 429 else {}  # 24 hours
        )
    
    def _handle_governor_approval_required(
        self,
        result: Dict[str, Any],
        request: Request,
        action: str
    ) -> RedirectResponse:
        """
        Handle Governor approval requirement (redirect to approval UI).
        """
        deny_reason = result.get("deny_reason", "Governor approval required")
        governor_agent_id = request.state.jwt.get("governor_agent_id")
        
        logger.info(
            f"Governor approval required: user={request.state.jwt.get('user_id')}, "
            f"action={action}, governor={governor_agent_id}"
        )
        
        # Build approval UI URL with params
        approval_url = (
            f"{self.approval_ui_url}/approval?"
            f"action={action}&"
            f"user_id={request.state.jwt.get('user_id')}&"
            f"resource={request.url.path}&"
            f"governor_id={governor_agent_id or 'none'}"
        )
        
        # Return 307 redirect (preserves POST method)
        return RedirectResponse(
            url=approval_url,
            status_code=307,
            headers={
                "X-Governor-Approval-Required": "true",
                "X-Governor-Action": action,
                "X-Governor-Agent-ID": governor_agent_id or "none"
            }
        )
    
    def _get_next_day_midnight(self) -> str:
        """Get ISO timestamp for next day midnight (UTC)."""
        now = datetime.now(timezone.utc)
        next_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        next_day = next_day.replace(day=next_day.day + 1)
        return next_day.isoformat()
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
