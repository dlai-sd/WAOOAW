"""src/gateway/tests/conftest.py

Integration-style tests for the Gateway folder.

The `src/gateway` area in this repository primarily contains middleware and
contracts (not a fully runnable deployed gateway service). To keep these tests
reliable in CI, we run them against small in-process ASGI apps that exercise the
expected request/response contract.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional

import httpx
import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse


@dataclass(frozen=True)
class JwtKeys:
    private_pem: str
    public_pem: str


@pytest.fixture(scope="session")
def jwt_keys() -> JwtKeys:
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    return JwtKeys(private_pem=private_pem, public_pem=public_pem)


@pytest.fixture
def make_jwt(jwt_keys: JwtKeys) -> Callable[..., str]:
    def _make(
        *,
        user_id: str = "user_123",
        customer_id: str = "customer_456",
        email: str = "test@waooaw.com",
        roles: Optional[list[str]] = None,
        trial_mode: bool = False,
        trial_expires_at: Optional[int] = None,
        exp_minutes: int = 60,
    ) -> str:
        now = datetime.utcnow()
        exp = now + timedelta(minutes=exp_minutes)
        if trial_expires_at is None:
            trial_expires_at = int((now + timedelta(days=7)).timestamp())

        payload: Dict[str, Any] = {
            "sub": user_id,
            "customer_id": customer_id,
            "email": email,
            "iss": "waooaw.com",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "trial_mode": trial_mode,
            "trial_expires_at": trial_expires_at,
        }
        if roles is not None:
            payload["roles"] = roles

        return jwt.encode(payload, jwt_keys.private_pem, algorithm="RS256")

    return _make


def _problem(
    *,
    status: int,
    error_type: str,
    instance: str,
    correlation_id: str,
    title: str,
    detail: str,
) -> JSONResponse:
    response = JSONResponse(
        status_code=status,
        content={
            "type": "about:blank",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": instance,
            "correlation_id": correlation_id,
            "error_type": error_type,
        },
    )
    response.headers["Content-Type"] = "application/problem+json"
    return response


def _decode_jwt(token: str, *, public_key: str) -> Dict[str, Any]:
    return jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        issuer="waooaw.com",
        options={"verify_aud": False},
    )


def build_cp_app(jwt_keys: JwtKeys) -> FastAPI:
    app = FastAPI()
    trial_post_counts: Dict[str, int] = {}

    @app.middleware("http")
    async def correlation_and_auth(request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        if request.url.path == "/health":
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response

        # Auth required for all other endpoints in this test harness.
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return _problem(
                status=401,
                error_type="unauthorized",
                instance=request.url.path,
                correlation_id=correlation_id,
                title="Unauthorized",
                detail="Missing or invalid Authorization header",
            )

        token = auth.removeprefix("Bearer ").strip()
        try:
            claims = _decode_jwt(token, public_key=jwt_keys.public_pem)
        except Exception:
            return _problem(
                status=401,
                error_type="unauthorized",
                instance=request.url.path,
                correlation_id=correlation_id,
                title="Unauthorized",
                detail="Invalid token",
            )

        request.state.jwt_claims = claims

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-User-ID"] = str(claims.get("sub", ""))
        return response

    @app.get("/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/agents/{agent_id}")
    async def get_agent(request: Request, agent_id: str) -> Dict[str, Any]:
        claims = request.state.jwt_claims
        if claims.get("trial_mode"):
            trial_expires_at = int(claims.get("trial_expires_at") or 0)
            if trial_expires_at and trial_expires_at < int(datetime.utcnow().timestamp()):
                return JSONResponse(
                    status_code=403,
                    content={"error_type": "trial-expired"},
                )

        resp: Dict[str, Any] = {"id": agent_id, "status": "ok"}
        response = JSONResponse(status_code=200, content=resp)
        if claims.get("trial_mode"):
            response.headers["X-Target-Backend"] = "https://sandbox.plant.internal"
        return response

    @app.post("/api/v1/agents")
    async def create_agent(request: Request) -> JSONResponse:
        claims = request.state.jwt_claims
        if request.headers.get("X-Test-Budget-Exceeded", "").strip().lower() in {"1", "true", "yes", "on"}:
            return JSONResponse(status_code=402, content={"error_type": "budget-exceeded"})

        if claims.get("trial_mode"):
            key = str(claims.get("sub") or "")
            trial_post_counts[key] = trial_post_counts.get(key, 0) + 1
            if trial_post_counts[key] > 10:
                response = JSONResponse(status_code=429, content={"error_type": "trial-limit-exceeded"})
                response.headers["Retry-After"] = "60"
                return response

        return JSONResponse(status_code=201, content={"status": "created"})

    @app.post("/api/v1/tool_calls")
    async def tool_calls(payload: Dict[str, Any]) -> RedirectResponse:
        # Minimal behavior: sensitive actions redirect to approval.
        if payload.get("action"):
            return RedirectResponse(url="/approval", status_code=307)
        return RedirectResponse(url="/", status_code=307)

    @app.get("/api/v1/slow_endpoint")
    async def slow_endpoint() -> Dict[str, str]:
        await asyncio.sleep(2.0)
        return {"status": "ok"}

    return app


def build_pp_app(jwt_keys: JwtKeys) -> FastAPI:
    app = FastAPI()

    def _role_level(roles: list[str]) -> str:
        if "admin" in roles:
            return "admin"
        if "developer" in roles:
            return "developer"
        return "viewer"

    @app.middleware("http")
    async def correlation_and_auth(request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        if request.url.path == "/health":
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return _problem(
                status=401,
                error_type="unauthorized",
                instance=request.url.path,
                correlation_id=correlation_id,
                title="Unauthorized",
                detail="Missing or invalid Authorization header",
            )

        token = auth.removeprefix("Bearer ").strip()
        try:
            claims = _decode_jwt(token, public_key=jwt_keys.public_pem)
        except Exception:
            return _problem(
                status=401,
                error_type="unauthorized",
                instance=request.url.path,
                correlation_id=correlation_id,
                title="Unauthorized",
                detail="Invalid token",
            )

        roles = claims.get("roles") or []
        if not isinstance(roles, list):
            roles = []
        request.state.jwt_claims = claims
        request.state.roles = roles

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-User-ID"] = str(claims.get("sub", ""))
        response.headers["X-User-Roles"] = ",".join(roles)
        response.headers["X-User-Role-Level"] = _role_level(roles)
        return response

    @app.get("/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/agents/{agent_id}")
    async def get_agent(agent_id: str) -> Dict[str, Any]:
        return {"id": agent_id, "status": "ok"}

    @app.post("/api/v1/agents")
    async def create_agent(request: Request) -> JSONResponse:
        roles: list[str] = request.state.roles
        level = _role_level(roles)
        if level in {"admin", "developer"}:
            return JSONResponse(status_code=201, content={"status": "created"})
        return JSONResponse(status_code=403, content={"error_type": "permission-denied"})

    @app.delete("/api/v1/agents/{agent_id}")
    async def delete_agent(request: Request, agent_id: str) -> JSONResponse:
        roles: list[str] = request.state.roles
        level = _role_level(roles)
        if level == "admin":
            return JSONResponse(status_code=204, content=None)
        return JSONResponse(status_code=403, content={"error_type": "permission-denied"})

    return app


@pytest.fixture(scope="session")
def cp_app(jwt_keys: JwtKeys) -> FastAPI:
    return build_cp_app(jwt_keys)


@pytest.fixture(scope="session")
def pp_app(jwt_keys: JwtKeys) -> FastAPI:
    return build_pp_app(jwt_keys)


@pytest.fixture
async def cp_client(cp_app: FastAPI) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=cp_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://cp.test") as client:
        yield client


@pytest.fixture
async def pp_client(pp_app: FastAPI) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=pp_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://pp.test") as client:
        yield client
