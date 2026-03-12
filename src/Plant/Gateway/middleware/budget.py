"""
Budget Guard Middleware - GW-103

Constitutional budget enforcement:
- Platform Budget: $100/month total spend
- Agent Budget: $1/day per agent
- Alert Thresholds: 80% (warning), 95% (high), 100% (critical)

Queries OPA agent_budget policy, blocks at 100%, updates Redis post-request.
"""

import httpx
import os
import time
import base64
import json
import redis.asyncio as redis
import logging
try:
    from .circuit_breaker import CircuitBreaker, GatewayCircuitOpenError
except ImportError:  # pragma: no cover
    from middleware.circuit_breaker import CircuitBreaker, GatewayCircuitOpenError

_opa_cb = CircuitBreaker(service_name="opa-budget")  # P-1: fast-fail when OPA is down
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from ..infrastructure.feature_flags.feature_flags import FeatureFlagService, FeatureFlagContext
except ImportError:  # pragma: no cover
    from infrastructure.feature_flags.feature_flags import FeatureFlagService, FeatureFlagContext

try:
    from .auth import _is_public_path
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


class BudgetGuardMiddleware(BaseHTTPMiddleware):
    """
    Budget Guard Middleware for CP and PP Gateways.
    
    Constitutional Budget Enforcement (GW-000-004):
    - Platform Budget: $100/month maximum spend
    - Agent Budget: $1/day per agent maximum spend
    - Alert Thresholds:
      * 80%: Warning (Slack alert)
      * 95%: High (Email + Slack)
      * 100%: Critical (Block requests + pause agents)
    
    Flow:
    1. Query OPA agent_budget policy pre-request
    2. If critical (≥100%), return 402 Payment Required
    3. Allow request if below 100%
    4. Update Redis with request cost post-request
    5. Emit alert_level metrics to Cloud Monitoring
    
    Configuration:
    - OPA_SERVICE_URL: OPA endpoint
    - REDIS_URL: Redis for budget tracking
    - BUDGET_TIMEOUT: OPA query timeout (default: 2s)
    - COST_PER_REQUEST: Cost per request in USD (default: 0.001)
    """
    
    # Budget thresholds
    PLATFORM_BUDGET_MONTHLY = Decimal("100.00")  # $100/month
    AGENT_BUDGET_DAILY = Decimal("1.00")  # $1/day per agent
    
    # Alert thresholds (percentage)
    THRESHOLD_WARNING = 80
    THRESHOLD_HIGH = 95
    THRESHOLD_CRITICAL = 100
    
    # Cost per request (in USD)
    COST_PER_REQUEST = Decimal("0.001")  # $0.001 per request
    
    def __init__(
        self,
        app,
        opa_service_url: str,
        redis_url: str,
        feature_flag_service: Optional[FeatureFlagService] = None,
        timeout: int = 2
    ):
        super().__init__(app)
        self.opa_service_url = opa_service_url.rstrip("/")
        self.redis_url = redis_url
        self.feature_flag_service = feature_flag_service
        self.timeout = timeout
        self.http_client = httpx.AsyncClient(timeout=timeout)
        self.redis_client: Optional[redis.Redis] = None
    
    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis client."""
        if not self.redis_client:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
        return self.redis_client
    
    async def dispatch(self, request: Request, call_next):
        """
        Intercept request, check budget, enforce limits, update Redis.
        """
        # Always allow CORS preflight requests through.
        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        # Skip public endpoints
        path = request.url.path
        normalized = (path or "").rstrip("/")
        if normalized.endswith("/auth/google/verify"):
            return await call_next(request)

        if (
            _is_public_path(path)
            or path.rstrip("/").startswith("/api/v1/customers")
            or path.rstrip("/").startswith("/api/v1/otp/sessions")
        ):
            return await call_next(request)
        
        # Extract JWT claims
        jwt_claims = getattr(request.state, "jwt", None)
        if not jwt_claims:
            logger.error("Budget middleware called without JWT claims")
            return JSONResponse(
                status_code=500,
                content={
                    "type": "https://waooaw.com/errors/internal-server-error",
                    "title": "Internal Server Error",
                    "status": 500,
                    "detail": "Budget middleware requires JWT claims",
                    "instance": str(request.url)
                }
            )
        
        # Check feature flag
        context = FeatureFlagContext(
            user_id=jwt_claims.get("user_id"),
            customer_id=jwt_claims.get("customer_id"),
            email=jwt_claims.get("email"),
            trial_mode=jwt_claims.get("trial_mode", False),
            roles=jwt_claims.get("roles", []),
            gateway_type=getattr(request.state, "gateway_type", "CP")
        )
        
        if self.feature_flag_service:
            if not self.feature_flag_service.is_enabled("enable_budget_enforcement", context, default=True):
                logger.info(f"Budget enforcement disabled via feature flag for user {jwt_claims.get('user_id')}")
                return await call_next(request)
            
            # Get dynamic thresholds from feature flags
            thresholds = self.feature_flag_service.get_variation(
                "budget_alert_thresholds",
                context,
                default={
                    "warning": self.THRESHOLD_WARNING,
                    "high": self.THRESHOLD_HIGH,
                    "critical": self.THRESHOLD_CRITICAL
                }
            )
        else:
            thresholds = {
                "warning": self.THRESHOLD_WARNING,
                "high": self.THRESHOLD_HIGH,
                "critical": self.THRESHOLD_CRITICAL
            }
        
        try:
            # Extract agent_id from JWT (if present)
            agent_id = jwt_claims.get("agent_id") or jwt_claims.get("sub")
            customer_id = jwt_claims.get("customer_id")
            
            # Build OPA input
            opa_input = {
                "jwt": jwt_claims,
                "agent_id": agent_id,
                "customer_id": customer_id,
                "path": path,
                "method": request.method
            }
            
            # Query OPA agent_budget policy
            budget_result = await self._query_opa_budget(opa_input)

            # Fail open when OPA does not return an explicit decision. This can
            # happen in dev/test environments where the policy bundle isn't loaded.
            if "allow" not in budget_result:
                logger.warning("OPA budget result missing 'allow'; allowing request")
                return await call_next(request)
            
            if not budget_result.get("allow", False):
                # Budget exceeded, block request
                return self._handle_budget_exceeded(budget_result, request, thresholds)
            
            # Check alert level
            alert_level = budget_result.get("alert_level", "normal")
            platform_utilization = budget_result.get("platform_utilization_percent", 0)
            agent_utilization = budget_result.get("agent_utilization_percent", 0)
            
            # Attach budget info to request state
            request.state.budget_alert_level = alert_level
            request.state.platform_utilization = platform_utilization
            request.state.agent_utilization = agent_utilization
            
            # Continue to next middleware
            response = await call_next(request)
            
            # Update Redis with request cost (post-request, non-blocking)
            try:
                await self._update_budget_redis(agent_id, customer_id, self.COST_PER_REQUEST)
            except Exception as e:
                logger.error(f"Failed to update budget in Redis: {e}")
                # Don't fail request if Redis update fails
            
            # Add budget headers to response
            response.headers["X-Budget-Alert-Level"] = alert_level
            response.headers["X-Platform-Utilization"] = f"{platform_utilization:.2f}"
            response.headers["X-Agent-Utilization"] = f"{agent_utilization:.2f}"
            
            return response
            
        except (httpx.TimeoutException, GatewayCircuitOpenError):
            logger.error(f"OPA budget query timeout or circuit open after {self.timeout}s")
            # Fail open: allow request if budget service is down
            logger.warning("Budget service timeout or circuit open, allowing request (fail-open)")
            return await call_next(request)
        except Exception as e:
            logger.error(f"Budget middleware error: {e}", exc_info=True)
            # Fail open: allow request if budget check fails
            logger.warning("Budget check failed, allowing request")
            return await call_next(request)
    
    async def _query_opa_budget(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query OPA agent_budget policy.
        
        POST /v1/data/gateway/agent_budget/allow
        {
            "input": {
                "jwt": {...},
                "agent_id": "agent123",
                "customer_id": "customer123"
            }
        }
        
        Response:
        {
            "result": {
                "allow": true,
                "alert_level": "warning",
                "platform_utilization_percent": 85.3,
                "agent_utilization_percent": 42.7,
                "platform_budget": {
                    "limit": 100.0,
                    "spent": 85.3,
                    "remaining": 14.7
                },
                "agent_budget": {
                    "limit": 1.0,
                    "spent": 0.427,
                    "remaining": 0.573
                }
            }
        }
        """
        url = f"{self.opa_service_url}/v1/data/gateway/agent_budget/allow"

        if not _opa_cb.is_call_permitted():  # P-1: fast-fail when circuit is open
            raise GatewayCircuitOpenError("OPA/budget")
        opa_headers: Dict[str, str] = {}
        if os.getenv("K_SERVICE"):  # running on Cloud Run — attach identity token
            id_token = await _get_opa_id_token(self.opa_service_url)
            if id_token:
                opa_headers["Authorization"] = f"Bearer {id_token}"
        try:
            response = await self.http_client.post(
                url,
                json={"input": input_data},
                headers=opa_headers
            )
            response.raise_for_status()
            _opa_cb.record_success()
            return response.json().get("result", {})
        except (httpx.TimeoutException, httpx.ConnectError):
            _opa_cb.record_failure()
            raise
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500:
                _opa_cb.record_failure()
            raise
    
    async def _update_budget_redis(
        self,
        agent_id: Optional[str],
        customer_id: str,
        cost: Decimal
    ):
        """
        Update Redis with request cost.
        
        Redis Keys:
        - platform_budget:spent_usd: Total platform spend
        - agent_budgets:{agent_id}:spent_usd: Per-agent spend
        - customer_budgets:{customer_id}:spent_usd: Per-customer spend
        """
        r = await self._get_redis()
        cost_str = str(cost)
        
        # Update platform budget
        await r.hincrbyfloat("platform_budget", "spent_usd", float(cost))
        
        # Update agent budget (if agent_id present)
        if agent_id:
            await r.hincrbyfloat(f"agent_budgets:{agent_id}", "spent_usd", float(cost))
        
        # Update customer budget
        await r.hincrbyfloat(f"customer_budgets:{customer_id}", "spent_usd", float(cost))
        
        logger.debug(f"Updated budget: agent={agent_id}, customer={customer_id}, cost=${cost}")
    
    def _handle_budget_exceeded(
        self,
        result: Dict[str, Any],
        request: Request,
        thresholds: Dict[str, int]
    ) -> JSONResponse:
        """
        Handle budget exceeded (block request with 402 Payment Required).
        """
        deny_reason = result.get("deny_reason", "Budget exceeded")
        alert_level = result.get("alert_level", "critical")
        platform_utilization = result.get("platform_utilization_percent", 100)
        agent_utilization = result.get("agent_utilization_percent", 100)
        
        platform_budget = result.get("platform_budget", {})
        agent_budget = result.get("agent_budget", {})
        
        logger.error(
            f"Budget exceeded: user={request.state.jwt.get('user_id')}, "
            f"alert_level={alert_level}, platform={platform_utilization:.2f}%, "
            f"agent={agent_utilization:.2f}%"
        )
        
        return JSONResponse(
            status_code=402,
            content={
                "type": "https://waooaw.com/errors/budget-exceeded",
                "title": "Budget Exceeded",
                "status": 402,
                "detail": deny_reason,
                "instance": str(request.url),
                "alert_level": alert_level,
                "platform_budget": {
                    "limit_usd": platform_budget.get("limit", 100.0),
                    "spent_usd": platform_budget.get("spent", 0.0),
                    "remaining_usd": platform_budget.get("remaining", 0.0),
                    "utilization_percent": platform_utilization
                },
                "agent_budget": {
                    "limit_usd": agent_budget.get("limit", 1.0),
                    "spent_usd": agent_budget.get("spent", 0.0),
                    "remaining_usd": agent_budget.get("remaining", 0.0),
                    "utilization_percent": agent_utilization
                },
                "upgrade_url": "https://waooaw.com/upgrade",
                "contact_sales": "https://waooaw.com/contact"
            },
            headers={
                "Retry-After": "3600",  # 1 hour
                "X-Budget-Alert-Level": alert_level
            }
        )
    
    async def close(self):
        """Close HTTP and Redis clients."""
        await self.http_client.aclose()
        if self.redis_client:
            await self.redis_client.close()
