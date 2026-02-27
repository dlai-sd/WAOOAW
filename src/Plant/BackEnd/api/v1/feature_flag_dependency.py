"""Feature flag FastAPI dependency — C7 (NFR It-7 reusable interface).

Provides a dependency factory that routes can use to gate behaviour behind
a feature flag, evaluated against the live Plant FeatureFlagService (with
60-second Redis cache).

Problem solved:
    FeatureFlagService and the admin API exist and manage flags, but no
    business route ever checks a flag at runtime — flags are managed but
    never evaluated.

Solution:
    Add ``Depends(require_flag("my_feature"))`` to any route.  If the flag
    is off, the route returns a 404 automatically.

Usage::

    from api.v1.feature_flag_dependency import require_flag

    @router.post("/new-hire-wizard")
    async def hire(
        body: HireRequest,
        _: bool = Depends(require_flag("new_hire_wizard")),
    ):
        # Only reached when the "new_hire_wizard" flag is enabled
        ...

    # Optional: check flag without raising (use the service directly):
    @router.get("/preview")
    async def preview(
        is_on: bool = Depends(require_flag("preview_mode", raise_if_off=False)),
    ):
        if not is_on:
            return {"available": False}
        ...
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_read_db_session
from services.feature_flag_service import FeatureFlagService

logger = logging.getLogger(__name__)


def require_flag(
    flag_name: str,
    *,
    default: bool = False,
    raise_if_off: bool = True,
) -> None:
    """FastAPI dependency factory — evaluate a feature flag.

    Args:
        flag_name:    The flag key to evaluate, e.g. ``"new_hire_wizard"``.
        default:      Value to use when the flag is not found in the store.
                      Default is ``False`` (flags off-by-default until
                      explicitly enabled).
        raise_if_off: When True (default), raises HTTP 404 if the flag is
                      disabled, so the route is completely hidden.
                      When False, the dependency resolves to a bool and the
                      route decides what to do.

    Returns:
        A FastAPI dependency callable that resolves to ``bool``.

    Example::

        @router.post("/dashboard-v2")
        async def dashboard_v2(
            _: bool = Depends(require_flag("dashboard_v2")),
        ):
            ...
    """

    async def _check_flag(
        db: AsyncSession = Depends(get_read_db_session),
    ) -> bool:
        svc = FeatureFlagService(db)
        try:
            enabled = await svc.is_enabled(flag_name)
        except Exception:  # pragma: no cover — Redis/DB unavailable
            logger.warning(
                "feature_flag_dependency: error evaluating flag '%s', using default=%s",
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
