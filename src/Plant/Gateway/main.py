"""
WAOOAW Plant Gateway - Main Application
Middleware stack + Proxy to Plant Backend
"""

import os
import time
import base64
import json
import logging
from urllib.parse import urlencode
from typing import Any, Dict, Optional, Tuple
from fastapi import FastAPI, Request, Response
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

try:
    from .middleware.error_handler import setup_error_handlers
    from .middleware.budget import BudgetGuardMiddleware
    from .middleware.policy import PolicyMiddleware
    from .middleware.rbac import RBACMiddleware
    from .middleware.auth import AuthMiddleware
    from .middleware.error_handler import create_problem_details
    from .middleware.audit import AuditLoggingMiddleware
except ImportError:  # pragma: no cover
    from middleware.error_handler import setup_error_handlers
    from middleware.budget import BudgetGuardMiddleware
    from middleware.policy import PolicyMiddleware
    from middleware.rbac import RBACMiddleware
    from middleware.auth import AuthMiddleware
    from middleware.error_handler import create_problem_details
    from middleware.audit import AuditLoggingMiddleware

# Configuration
PLANT_BACKEND_URL = os.getenv("PLANT_BACKEND_URL", "http://localhost:8001")
PLANT_BACKEND_USE_ID_TOKEN = os.getenv("PLANT_BACKEND_USE_ID_TOKEN", "true").lower() in {"1", "true", "yes"}
# For Cloud Run, audience should usually be the full service URL.
PLANT_BACKEND_AUDIENCE = os.getenv("PLANT_BACKEND_AUDIENCE", PLANT_BACKEND_URL)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DEBUG_VERBOSE = os.getenv("DEBUG_VERBOSE", "false").lower() in {"1", "true", "yes"}

logger = logging.getLogger("waooaw.plant_gateway")
if not logger.handlers:
    logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Metadata server for fetching identity tokens (works in Cloud Run/Compute).
# Cloud Run supports metadata.google.internal; keep a fallback for older aliases.
_METADATA_IDENTITY_URLS = [
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity",
    "http://metadata/computeMetadata/v1/instance/service-accounts/default/identity",
]
_METADATA_HEADERS = {"Metadata-Flavor": "Google"}

_backend_token_cache: Tuple[Optional[str], float] = (None, 0.0)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
OPA_URL = os.getenv("OPA_URL", "http://localhost:8181")
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "")
APPROVAL_UI_URL = os.getenv("APPROVAL_UI_URL", "http://localhost:3000/approvals")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()
GW_AUDIT_LOGGING_ENABLED = (os.getenv("GW_AUDIT_LOGGING_ENABLED") or "false").lower() in {"1", "true", "yes"}
GW_GATEWAY_TYPE = (os.getenv("GATEWAY_TYPE") or "CP").strip() or "CP"

# Create FastAPI app
app = FastAPI(
    title="WAOOAW Plant Gateway",
    description="API Gateway with middleware stack",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup error handlers (must be first)
setup_error_handlers(app)

# Add middleware stack (order matters - last added = first executed)
# Execution order: Auth → RBAC → Policy → Budget → ErrorHandling → Backend

# 1. Budget Guard (cost tracking)
app.add_middleware(
    BudgetGuardMiddleware,
    opa_service_url=OPA_URL,
    redis_url=REDIS_URL
)

# 2. Policy Enforcement (trial limits, sandbox routing)
app.add_middleware(
    PolicyMiddleware,
    opa_service_url=OPA_URL,
    redis_url=REDIS_URL,
    approval_ui_url=APPROVAL_UI_URL
)

# 3. RBAC (role-based access control)
app.add_middleware(
    RBACMiddleware,
    opa_service_url=OPA_URL,
    gateway_type="PLANT"
)

# 3.5 Audit logging (optional; must run after Auth to capture identity)
if GW_AUDIT_LOGGING_ENABLED and DATABASE_URL:
    app.add_middleware(
        AuditLoggingMiddleware,
        database_url=DATABASE_URL,
        gateway_type=GW_GATEWAY_TYPE,
    )

# 4. Authentication (JWT validation)
app.add_middleware(AuthMiddleware)

# HTTP client for proxying to backend
http_client = httpx.AsyncClient(timeout=30.0)


def _debug_trace_enabled(request: Request) -> bool:
    header = request.headers.get("X-Debug-Trace") or request.headers.get("x-debug-trace")
    return DEBUG_VERBOSE or (header or "").strip().lower() in {"1", "true", "yes"}


def _jwt_expiry_epoch_seconds(token: str) -> Optional[float]:
    """Best-effort parse of JWT exp without external deps."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        # Add padding
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode("utf-8")))
        exp = payload.get("exp")
        return float(exp) if exp is not None else None
    except Exception:
        return None


def _running_on_cloud_run() -> bool:
    # Cloud Run sets K_SERVICE; keep it generic and safe.
    return bool(os.getenv("K_SERVICE"))


def _should_use_backend_id_token() -> bool:
    if not PLANT_BACKEND_USE_ID_TOKEN:
        return False
    # In Cloud Run we may call the backend through internal HTTP, but it can
    # still be IAM-protected (expects an ID token). Allow this.
    return PLANT_BACKEND_URL.startswith("https://") or _running_on_cloud_run()


async def _get_backend_id_token() -> Optional[str]:
    """Fetch (and cache) an ID token for Plant Backend, using the metadata server."""
    global _backend_token_cache
    token, expires_at = _backend_token_cache
    now = time.time()
    if token and now < (expires_at - 30):
        return token

    # Request a fresh token
    params = {"audience": PLANT_BACKEND_AUDIENCE, "format": "full"}
    for url in _METADATA_IDENTITY_URLS:
        try:
            # Metadata calls should be fast; keep a tighter timeout than general upstream calls.
            res = await http_client.get(url, headers=_METADATA_HEADERS, params=params, timeout=5.0)
            if res.status_code != 200:
                if DEBUG_VERBOSE:
                    logger.warning(
                        "metadata identity token fetch failed: status=%s url=%s",
                        res.status_code,
                        url,
                    )
                continue
            token = res.text.strip()
            exp = _jwt_expiry_epoch_seconds(token)
            expires_at = exp if exp else (now + 300)
            _backend_token_cache = (token, expires_at)
            return token
        except Exception:
            if DEBUG_VERBOSE:
                logger.exception("metadata identity token fetch errored: url=%s", url)
            continue

    return None


def _docs_url_for_request(request: Request) -> str:
    host = (request.url.hostname or "").lower()
    # Expected: plant.<env>.waooaw.com
    parts = host.split(".")
    env = None
    if len(parts) >= 3 and parts[0] == "plant":
        env = parts[1]

    if env and env not in {"prod", "production", "www"}:
        return f"https://docs.{env}.waooaw.com"
    return "https://docs.waooaw.com"


def _rewrite_support_section(description: str, docs_url: str) -> str:
    marker = "## Support"
    support = (
        f"{marker}\n"
        f"- Documentation: {docs_url}\n"
        "- GitHub: https://github.com/dlai-sd/WAOOAW\n"
        "- WAOOAW Engineering Team - Website - https://dlaisd.com\n"
        "- Send email to WAOOAW Engineering Team- yogesh.khandge@dlaisd.com\n"
        "- Proprietary - https://dlaisd.com\n"
    )

    if not description:
        return support
    if marker not in description:
        return description.rstrip() + "\n\n" + support

    before, after = description.split(marker, 1)
    # Remove the existing support block (until the next heading or end).
    next_heading = after.find("\n## ")
    tail = after[next_heading:] if next_heading != -1 else ""
    return before.rstrip() + "\n\n" + support + tail.lstrip("\n")


def _is_subscription_cancel_request(request: Request) -> bool:
    if request.method.upper() != "POST":
        return False
    path = (request.url.path or "").rstrip("/")
    return path.startswith("/api/v1/payments/subscriptions/") and path.endswith("/cancel")


def _is_invoice_request(request: Request) -> bool:
    # Customer-scoped invoice endpoints must never accept a caller-supplied customer_id.
    if request.method.upper() != "GET":
        return False
    path = (request.url.path or "").rstrip("/")
    return path == "/api/v1/invoices" or path.startswith("/api/v1/invoices/")


def _is_receipt_request(request: Request) -> bool:
    # Customer-scoped receipt endpoints must never accept a caller-supplied customer_id.
    if request.method.upper() != "GET":
        return False
    path = (request.url.path or "").rstrip("/")
    return path == "/api/v1/receipts" or path.startswith("/api/v1/receipts/")


def _is_trial_status_request(request: Request) -> bool:
    # Customer-scoped trial-status endpoints must never accept a caller-supplied customer_id.
    if request.method.upper() != "GET":
        return False
    path = (request.url.path or "").rstrip("/")
    return path == "/api/v1/trial-status" or path.startswith("/api/v1/trial-status/")


def _is_payments_coupon_checkout_request(request: Request) -> bool:
    if request.method.upper() != "POST":
        return False
    path = (request.url.path or "").rstrip("/")
    return path == "/api/v1/payments/coupon/checkout"


def _is_payments_razorpay_order_request(request: Request) -> bool:
    if request.method.upper() != "POST":
        return False
    path = (request.url.path or "").rstrip("/")
    return path == "/api/v1/payments/razorpay/order"


def _is_payments_razorpay_confirm_request(request: Request) -> bool:
    if request.method.upper() != "POST":
        return False
    path = (request.url.path or "").rstrip("/")
    return path == "/api/v1/payments/razorpay/confirm"


def _is_payments_subscriptions_by_customer_request(request: Request) -> bool:
    if request.method.upper() != "GET":
        return False
    path = (request.url.path or "").rstrip("/")
    return path.startswith("/api/v1/payments/subscriptions/by-customer/")


def _is_hired_agents_draft_request(request: Request) -> bool:
    if request.method.upper() != "PUT":
        return False
    path = (request.url.path or "").rstrip("/")
    return path == "/api/v1/hired-agents/draft"


def _is_hired_agents_finalize_request(request: Request) -> bool:
    if request.method.upper() != "POST":
        return False
    path = (request.url.path or "").rstrip("/")
    return path.startswith("/api/v1/hired-agents/") and path.endswith("/finalize")


def _is_hired_agents_by_subscription_request(request: Request) -> bool:
    if request.method.upper() != "GET":
        return False
    path = (request.url.path or "").rstrip("/")
    return path.startswith("/api/v1/hired-agents/by-subscription/")


def _rewrite_subscriptions_by_customer_path(path: str, customer_id: str) -> str:
    prefix = "/api/v1/payments/subscriptions/by-customer/"
    normalized = (path or "")
    if not normalized.startswith(prefix):
        return normalized
    return f"{prefix}{customer_id}"


def _extract_subscription_id_from_cancel_path(path: str) -> Optional[str]:
    normalized = (path or "").rstrip("/")
    parts = [p for p in normalized.split("/") if p]
    # Expected: api/v1/payments/subscriptions/<id>/cancel
    if len(parts) >= 6 and parts[-1] == "cancel":
        return parts[-2]
    return None


def _rewrite_query_with_customer_id(request: Request, customer_id: str) -> str:
    items = list(request.query_params.multi_items())
    filtered = [(k, v) for (k, v) in items if k != "customer_id"]
    filtered.append(("customer_id", customer_id))
    return urlencode(filtered)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await http_client.aclose()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "plant-gateway",
        "backend": PLANT_BACKEND_URL
    }


@app.get("/api/health", include_in_schema=False)
async def api_health_check():
    """Compatibility health endpoint used by PP frontend."""
    return await health_check()


@app.get("/openapi.json", include_in_schema=False)
async def plant_openapi(request: Request) -> JSONResponse:
    """Serve the backend OpenAPI spec, rewritten to use the gateway base URL."""
    backend_spec_url = f"{PLANT_BACKEND_URL.rstrip('/')}/openapi.json"

    headers: Dict[str, str] = {}
    # If Plant Backend is IAM-protected (Cloud Run), attach an ID token.
    if _should_use_backend_id_token():
        token = await _get_backend_id_token()
        if not token:
            correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")
            logger.warning("failed to mint backend ID token for openapi; corr=%s", correlation_id)
            payload: Dict[str, Any] = {
                "error": "upstream_auth_unavailable",
                "reason": "failed_to_mint_cloud_run_id_token",
                "plant_backend_url": PLANT_BACKEND_URL,
                "plant_backend_audience": PLANT_BACKEND_AUDIENCE,
                "correlation_id": correlation_id,
            }
            if _debug_trace_enabled(request):
                payload["metadata_urls"] = list(_METADATA_IDENTITY_URLS)
            return JSONResponse(
                status_code=502,
                content=payload,
                headers={"X-Correlation-ID": correlation_id} if correlation_id else None,
            )
        headers["Authorization"] = f"Bearer {token}"

    correlation_id = (
        request.headers.get("X-Correlation-ID")
        or request.headers.get("x-correlation-id")
        or getattr(request.state, "correlation_id", None)
    )

    try:
        response = await http_client.get(backend_spec_url, headers=headers)
    except httpx.TimeoutException as exc:
        logger.warning("openapi upstream timeout: url=%s corr=%s", backend_spec_url, correlation_id)
        problem = create_problem_details(
            error_type="gateway-timeout",
            status=504,
            detail="Upstream Plant Backend timed out while generating OpenAPI spec",
            instance=str(request.url.path),
            plant_backend_url=PLANT_BACKEND_URL,
            upstream_url=backend_spec_url,
            correlation_id=correlation_id,
        )
        if _debug_trace_enabled(request):
            problem["exception_type"] = type(exc).__name__
            problem["exception"] = str(exc)
        return JSONResponse(
            status_code=504,
            content=problem,
            headers={"Content-Type": "application/problem+json", **({"X-Correlation-ID": correlation_id} if correlation_id else {})},
        )
    except httpx.RequestError as exc:
        logger.warning("openapi upstream request error: url=%s corr=%s", backend_spec_url, correlation_id)
        problem = create_problem_details(
            error_type="bad-gateway",
            status=502,
            detail="Failed to reach upstream Plant Backend for OpenAPI spec",
            instance=str(request.url.path),
            plant_backend_url=PLANT_BACKEND_URL,
            upstream_url=backend_spec_url,
            correlation_id=correlation_id,
        )
        if _debug_trace_enabled(request):
            problem["exception_type"] = type(exc).__name__
            problem["exception"] = str(exc)
        return JSONResponse(
            status_code=502,
            content=problem,
            headers={"Content-Type": "application/problem+json", **({"X-Correlation-ID": correlation_id} if correlation_id else {})},
        )

    if response.status_code >= 400:
        upstream_body = None
        if _debug_trace_enabled(request):
            # Limit size to avoid huge logs/responses.
            upstream_body = (response.text or "")[:2000]
        logger.warning(
            "openapi upstream error: status=%s url=%s corr=%s",
            response.status_code,
            backend_spec_url,
            correlation_id,
        )
        problem = create_problem_details(
            error_type="bad-gateway",
            status=502,
            detail=f"Upstream Plant Backend returned HTTP {response.status_code} for OpenAPI spec",
            instance=str(request.url.path),
            plant_backend_url=PLANT_BACKEND_URL,
            plant_backend_audience=PLANT_BACKEND_AUDIENCE,
            upstream_url=backend_spec_url,
            upstream_status=response.status_code,
            correlation_id=correlation_id,
            id_token_used=bool(headers.get("Authorization", "").startswith("Bearer ")),
        )
        if upstream_body is not None:
            problem["upstream_body"] = upstream_body
        return JSONResponse(
            status_code=502,
            content=problem,
            headers={"Content-Type": "application/problem+json", **({"X-Correlation-ID": correlation_id} if correlation_id else {})},
        )

    try:
        spec: Dict[str, Any] = response.json()
    except ValueError as exc:
        upstream_preview = (response.text or "")[:2000] if _debug_trace_enabled(request) else None
        logger.warning("openapi upstream returned non-json: corr=%s", correlation_id)
        problem = create_problem_details(
            error_type="bad-gateway",
            status=502,
            detail="Upstream Plant Backend returned non-JSON OpenAPI response",
            instance=str(request.url.path),
            plant_backend_url=PLANT_BACKEND_URL,
            upstream_url=backend_spec_url,
            correlation_id=correlation_id,
        )
        if upstream_preview is not None:
            problem["upstream_body"] = upstream_preview
            problem["exception"] = str(exc)
        return JSONResponse(
            status_code=502,
            content=problem,
            headers={"Content-Type": "application/problem+json", **({"X-Correlation-ID": correlation_id} if correlation_id else {})},
        )

    docs_url = _docs_url_for_request(request)
    info = spec.setdefault("info", {})
    info["description"] = _rewrite_support_section(info.get("description") or "", docs_url)
    info["contact"] = {
        "name": "WAOOAW Engineering Team",
        "url": "https://dlaisd.com",
        "email": "yogesh.khandge@dlaisd.com",
    }
    info["license"] = {"name": "Proprietary", "url": "https://dlaisd.com"}

    gateway_base = str(request.base_url).rstrip("/")
    spec["servers"] = [{"url": gateway_base}]
    return JSONResponse(spec)


@app.get("/docs", include_in_schema=False)
async def swagger_ui_html() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="WAOOAW Plant API - Docs",
    )


@app.get("/docs/oauth2-redirect", include_in_schema=False)
async def swagger_ui_redirect() -> HTMLResponse:
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html() -> HTMLResponse:
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="WAOOAW Plant API - ReDoc",
    )


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_to_backend(request: Request, path: str):
    """
    Proxy all requests to Plant Backend after middleware processing
    """
    # Skip health check
    if path == "health":
        return await health_check()
    
    # Build target URL
    target_url = f"{PLANT_BACKEND_URL}/{path}"

    force_customer_id_in_json_body = False

    # Gateway authz: enforce ownership by forcing customer_id for cancel.
    if _is_subscription_cancel_request(request):
        jwt_claims = getattr(request.state, "jwt", None)
        customer_id = None
        if isinstance(jwt_claims, dict):
            customer_id = jwt_claims.get("customer_id")
        if not (customer_id or "").strip():
            customer_id = getattr(request.state, "customer_id", None)
        customer_id = (customer_id or "").strip()
        if not customer_id:
            return JSONResponse(
                status_code=401,
                content={
                    "type": "https://waooaw.com/errors/unauthorized",
                    "title": "Unauthorized",
                    "status": 401,
                    "detail": "Missing customer_id in auth context",
                    "instance": str(request.url.path),
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        subscription_id = _extract_subscription_id_from_cancel_path(request.url.path)
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("x-correlation-id")
            or getattr(request.state, "correlation_id", None)
        )
        user_id = None
        if isinstance(jwt_claims, dict):
            user_id = jwt_claims.get("user_id")
        logger.info(
            "cancel_at_period_end requested: sub=%s customer=%s user=%s corr=%s",
            subscription_id,
            customer_id,
            user_id,
            correlation_id,
        )

        rewritten_query = _rewrite_query_with_customer_id(request, customer_id)
        target_url = f"{target_url}?{rewritten_query}"

    # Gateway authz: enforce ownership for invoice/receipt/trial-status/hired-agents operations.
    elif (
        _is_invoice_request(request)
        or _is_receipt_request(request)
        or _is_trial_status_request(request)
        or _is_hired_agents_by_subscription_request(request)
    ):
        jwt_claims = getattr(request.state, "jwt", None)
        customer_id = None
        if isinstance(jwt_claims, dict):
            customer_id = jwt_claims.get("customer_id")
        if not (customer_id or "").strip():
            customer_id = getattr(request.state, "customer_id", None)
        customer_id = (customer_id or "").strip()
        if not customer_id:
            return JSONResponse(
                status_code=401,
                content={
                    "type": "https://waooaw.com/errors/unauthorized",
                    "title": "Unauthorized",
                    "status": 401,
                    "detail": "Missing customer_id in auth context",
                    "instance": str(request.url.path),
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        rewritten_query = _rewrite_query_with_customer_id(request, customer_id)
        target_url = f"{target_url}?{rewritten_query}"

    # Gateway authz: payment endpoints must never accept caller-supplied customer identity.
    elif (
        _is_payments_coupon_checkout_request(request)
        or _is_payments_razorpay_order_request(request)
        or _is_payments_razorpay_confirm_request(request)
        or _is_payments_subscriptions_by_customer_request(request)
        or _is_hired_agents_draft_request(request)
        or _is_hired_agents_finalize_request(request)
    ):
        jwt_claims = getattr(request.state, "jwt", None)
        customer_id = None
        if isinstance(jwt_claims, dict):
            customer_id = jwt_claims.get("customer_id")
        if not (customer_id or "").strip():
            customer_id = getattr(request.state, "customer_id", None)
        customer_id = (customer_id or "").strip()
        if not customer_id:
            return JSONResponse(
                status_code=401,
                content={
                    "type": "https://waooaw.com/errors/unauthorized",
                    "title": "Unauthorized",
                    "status": 401,
                    "detail": "Missing customer_id in auth context",
                    "instance": str(request.url.path),
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        if _is_payments_subscriptions_by_customer_request(request):
            rewritten_path = _rewrite_subscriptions_by_customer_path(request.url.path, customer_id).lstrip("/")
            target_url = f"{PLANT_BACKEND_URL}/{rewritten_path}"
            if request.url.query:
                target_url = f"{target_url}?{request.url.query}"
        else:
            force_customer_id_in_json_body = True
            if request.url.query:
                target_url = f"{target_url}?{request.url.query}"

    # Forward query parameters (default)
    elif request.url.query:
        target_url = f"{target_url}?{request.url.query}"
    
    # Prepare headers
    headers = dict(request.headers)
    headers.pop("host", None)

    # Never forward the caller's Authorization header to Plant Backend.
    # Plant Backend is Cloud Run IAM-protected and expects an ID token.
    original_auth = request.headers.get("Authorization")
    for key in list(headers.keys()):
        if key.lower() == "authorization":
            headers.pop(key, None)

    # Prevent header spoofing: only the gateway sets X-Original-Authorization.
    for key in list(headers.keys()):
        if key.lower() == "x-original-authorization":
            headers.pop(key, None)

    if original_auth:
        headers["X-Original-Authorization"] = original_auth
    
    # Add gateway tracking headers
    headers["X-Gateway"] = "plant-gateway"
    if hasattr(request.state, "gateway_type"):
        headers["X-Gateway-Type"] = request.state.gateway_type

    # If Plant Backend is IAM-protected, attach an ID token from the metadata server.
    if _should_use_backend_id_token():
        token = await _get_backend_id_token()
        if not token:
            correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")
            logger.warning("failed to mint backend ID token; corr=%s", correlation_id)
            payload: Dict[str, Any] = {
                "error": "upstream_auth_unavailable",
                "reason": "failed_to_mint_cloud_run_id_token",
                "plant_backend_url": PLANT_BACKEND_URL,
                "plant_backend_audience": PLANT_BACKEND_AUDIENCE,
                "correlation_id": correlation_id,
            }
            if _debug_trace_enabled(request):
                payload["metadata_urls"] = list(_METADATA_IDENTITY_URLS)
                payload["original_auth_present"] = bool(original_auth)
            return JSONResponse(
                status_code=502,
                content=payload,
                headers={"X-Correlation-ID": correlation_id} if correlation_id else None,
            )

        headers["Authorization"] = f"Bearer {token}"
    
    # Get request body (optionally rewritten)
    body = await request.body()
    if force_customer_id_in_json_body and body:
        try:
            payload = json.loads(body)
            if isinstance(payload, dict):
                jwt_claims = getattr(request.state, "jwt", None)
                customer_id = None
                if isinstance(jwt_claims, dict):
                    customer_id = jwt_claims.get("customer_id")
                if not (customer_id or "").strip():
                    customer_id = getattr(request.state, "customer_id", None)
                customer_id = (customer_id or "").strip()
                if customer_id:
                    payload["customer_id"] = customer_id
                    body = json.dumps(payload).encode("utf-8")
                    headers["content-type"] = "application/json"
        except Exception:
            # Best-effort: if body isn't JSON, leave it unchanged.
            pass
    
    try:
        # Proxy to backend
        upstream_start = time.time()
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            follow_redirects=False
        )
        request.state.plant_latency_ms = (time.time() - upstream_start) * 1000.0

        if _debug_trace_enabled(request):
            content_type = (response.headers.get("content-type") or "").lower()
            if response.status_code in {401, 403} and ("text/html" in content_type or "text/plain" in content_type):
                correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")
                diagnostic: Dict[str, Any] = {
                    "error": "upstream_iam_rejected",
                    "reason": "cloud_run_invocation_unauthorized",
                    "upstream_status": response.status_code,
                    "upstream_content_type": response.headers.get("content-type"),
                    "plant_backend_url": PLANT_BACKEND_URL,
                    "plant_backend_audience": PLANT_BACKEND_AUDIENCE,
                    "id_token_used": bool(headers.get("Authorization", "").startswith("Bearer ")),
                    "original_auth_preserved": bool(headers.get("X-Original-Authorization")),
                    "correlation_id": correlation_id,
                }
                if DEBUG_VERBOSE:
                    logger.warning("backend returned HTML 401; corr=%s", correlation_id)
                return JSONResponse(
                    status_code=502,
                    content=diagnostic,
                    headers={"X-Correlation-ID": correlation_id} if correlation_id else None,
                )
        
        # Return backend response
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
        
    except httpx.RequestError as e:
        return Response(
            content=f"Backend unavailable: {str(e)}",
            status_code=503,
            media_type="text/plain"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
