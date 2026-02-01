"""
WAOOAW Plant Gateway - Main Application
Middleware stack + Proxy to Plant Backend
"""

import os
import time
import base64
import json
import logging
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

from middleware.error_handler import setup_error_handlers
from middleware.budget import BudgetGuardMiddleware
from middleware.policy import PolicyMiddleware
from middleware.rbac import RBACMiddleware
from middleware.auth import AuthMiddleware

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
            res = await http_client.get(url, headers=_METADATA_HEADERS, params=params)
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


@app.get("/openapi.json", include_in_schema=False)
async def plant_openapi(request: Request) -> JSONResponse:
    """Serve the backend OpenAPI spec, rewritten to use the gateway base URL."""
    backend_spec_url = f"{PLANT_BACKEND_URL.rstrip('/')}/openapi.json"
    response = await http_client.get(backend_spec_url)
    response.raise_for_status()
    spec: Dict[str, Any] = response.json()

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
    
    # Forward query parameters
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"
    
    # Prepare headers
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Add gateway tracking headers
    headers["X-Gateway"] = "plant-gateway"
    if hasattr(request.state, "gateway_type"):
        headers["X-Gateway-Type"] = request.state.gateway_type

    # If Plant Backend is IAM-protected, attach an ID token from the metadata server.
    if PLANT_BACKEND_USE_ID_TOKEN and PLANT_BACKEND_URL.startswith("https://"):
        original_auth = headers.get("authorization") or headers.get("Authorization")
        token = await _get_backend_id_token()
        if token:
            if original_auth:
                headers["X-Original-Authorization"] = original_auth
            headers["Authorization"] = f"Bearer {token}"
        elif _debug_trace_enabled(request):
            correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")
            payload: Dict[str, Any] = {
                "error": "upstream_auth_unavailable",
                "reason": "failed_to_mint_cloud_run_id_token",
                "plant_backend_url": PLANT_BACKEND_URL,
                "plant_backend_audience": PLANT_BACKEND_AUDIENCE,
                "metadata_urls": list(_METADATA_IDENTITY_URLS),
                "correlation_id": correlation_id,
            }
            if DEBUG_VERBOSE:
                logger.error("failed to mint backend ID token; corr=%s", correlation_id)
            return JSONResponse(
                status_code=502,
                content=payload,
                headers={"X-Correlation-ID": correlation_id} if correlation_id else None,
            )
    
    # Get request body
    body = await request.body()
    
    try:
        # Proxy to backend
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            follow_redirects=False
        )

        if _debug_trace_enabled(request):
            content_type = (response.headers.get("content-type") or "").lower()
            if response.status_code == 401 and ("text/html" in content_type or "text/plain" in content_type):
                correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")
                diagnostic: Dict[str, Any] = {
                    "error": "upstream_iam_rejected",
                    "reason": "cloud_run_invocation_unauthorized",
                    "upstream_status": response.status_code,
                    "upstream_content_type": response.headers.get("content-type"),
                    "plant_backend_url": PLANT_BACKEND_URL,
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
