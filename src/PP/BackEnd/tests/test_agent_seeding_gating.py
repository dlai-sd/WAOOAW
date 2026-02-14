from __future__ import annotations

import time

import jwt

from core.config import settings


def _mint_admin_token() -> str:
    now = int(time.time())
    payload = {
        "sub": "test-admin",
        "iat": now,
        "exp": now + 60,
        "iss": settings.JWT_ISSUER,
        "roles": ["admin"],
        "email": "admin@waooaw.com",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def test_seed_defaults_disabled_returns_404(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_AGENT_SEEDING", False, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    resp = await client.post(
        "/api/pp/agents/seed-defaults",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_seed_defaults_prod_like_env_returns_404_even_if_enabled(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "uat", raising=False)
    monkeypatch.setattr(settings, "ENABLE_AGENT_SEEDING", True, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    resp = await client.post(
        "/api/pp/agents/seed-defaults",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
