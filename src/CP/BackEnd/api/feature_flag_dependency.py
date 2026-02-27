"""Feature flag FastAPI dependency — C7 (NFR It-7 reusable interface), CP mirror.

Mirrors the Plant Backend ``require_flag`` dependency for use in CP Backend
routes.  Evaluates flags by calling the Plant Gateway feature-flags API
(GET /api/v1/feature-flags/{key}), which has Redis caching (60-second TTL)
on the Plant side.

Falls back to ``default`` (False) when the Plant Gateway is unavailable or
returns an unexpected response, so CP routes stay up even if Plant is down.

Usage::

    from api.feature_flag_dependency import require_flag

    @router.get("/beta-dashboard")
    async def beta_dashboard(
        _: bool = Depends(require_flag("beta_dashboard")),
    ):
        # Only reached when "beta_dashboard" flag is enabled in Plant
        ...
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import Depends, HTTPException, Request

from services.plant_gateway_client import PlantGatewayClient, ServiceUnavailableError

logger = logging.getLogger(__name__)


def require_flag(
    flag_name: str,
    *,
    default: bool = False,
    raise_if_off: bool = True,
) -> None:
    """FastAPI dependency factory — evaluate a Plant feature flag from CP.

    Calls GET /api/v1/feature-flags/{flag_name} on Plant Gateway.

    Args:
        flag_name:    The flag key to evaluate, e.g. ``"new_hire_wizard"``.
        default:      Value when Plant is unreachable or the flag is not found.
                      Defaults to ``False`` (safe off-by-default).
        raise_if_off: When True (default), raises HTTP 404 if flag is disabled.

    Returns:
        A FastAPI dependency callable that resolves to ``bool``.
    """

    async def _check_flag(request: Request) -> bool:
        base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
        if not base_url:
            logger.warning(
                "feature_flag_dependency: PLANT_GATEWAY_URL not set; using default=%s for '%s'",
                default,
                flag_name,
            )
            enabled = default
        else:
            cp_key = os.getenv("CP_REGISTRATION_KEY", "")
            headers = {"X-CP-Registration-Key": cp_key} if cp_key else {}
            client = PlantGatewayClient(base_url=base_url)
            try:
                resp = await client.request_json(
                    method="GET",
                    path=f"/api/v1/feature-flags/{flag_name}",
                    headers=headers or None,
                )
                if resp.status_code == 200 and isinstance(resp.json, dict):
                    enabled = bool(resp.json.get("enabled", default))
                elif resp.status_code == 404:
                    enabled = default
                else:
                    logger.warning(
                        "feature_flag_dependency: unexpected status %s for '%s'; using default=%s",
                        resp.status_code,
                        flag_name,
                        default,
                    )
                    enabled = default
            except ServiceUnavailableError:
                logger.warning(
                    "feature_flag_dependency: Plant Gateway unavailable for flag '%s'; using default=%s",
                    flag_name,
                    default,
                )
                enabled = default

        if not enabled and raise_if_off:
            raise HTTPException(
                status_code=404,
                detail=f"Feature '{flag_name}' is not available.",
            )
        return enabled

    return _check_flag  # type: ignore[return-value]
