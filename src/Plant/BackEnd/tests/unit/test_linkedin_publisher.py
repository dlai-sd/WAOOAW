"""Unit tests for LinkedInPublisher component (EXEC-ENGINE-001 E7-S3).

Tests:
  E7-S3-T1: previous_step_output.per_platform_variants.linkedin set, mock HTTP 200
             → success=True, data["platform"]="linkedin"
  E7-S3-T2: LinkedIn API returns HTTP 4xx (post rejected)
             → safe_execute() returns success=False, error message contains "linkedin"
             (or error_message is non-empty with safe_execute)
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from components import ComponentInput, get_component


def _make_input(linkedin_variant: dict | None = None) -> ComponentInput:
    if linkedin_variant is None:
        linkedin_variant = {"post_text": "Check out our new product!", "hashtags": [], "format": "post"}
    return ComponentInput(
        flow_run_id="fr-li-001",
        customer_id="cust-001",
        skill_config={
            "customer_fields": {"linkedin_access_token": "test-li-token"},
        },
        run_context={},
        previous_step_output={
            "per_platform_variants": {
                "linkedin": linkedin_variant,
            }
        },
    )


@pytest.fixture(autouse=True)
def _ensure_linkedin_publisher_registered():
    """Import module to trigger register_component() — makes tests order-independent."""
    from components import register_component
    import linkedin_publisher as _mod

    register_component(_mod.LinkedInPublisher())


@pytest.mark.unit
def test_linkedin_publisher_success():
    """E7-S3-T1: LinkedIn mock HTTP 200 → success=True, platform=linkedin."""
    from linkedin_publisher import LinkedInPublisher

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.headers = {"x-linkedin-id": "post-123"}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    pub = LinkedInPublisher()

    with patch("linkedin_publisher.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(pub.execute(_make_input()))

    assert result.success is True
    assert result.data["platform"] == "linkedin"


@pytest.mark.unit
def test_linkedin_publisher_api_error():
    """E7-S3-T2: LinkedIn API 4xx → safe_execute() returns success=False."""
    import httpx
    from linkedin_publisher import LinkedInPublisher

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "403 Forbidden",
            request=MagicMock(),
            response=MagicMock(status_code=403),
        )
    )

    pub = LinkedInPublisher()

    with patch("linkedin_publisher.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(pub.safe_execute(_make_input()))

    assert result.success is False
    assert result.error_message


@pytest.mark.unit
def test_linkedin_publisher_no_variant():
    """Missing linkedin variant in previous_step_output → success=False."""
    from linkedin_publisher import LinkedInPublisher

    pub = LinkedInPublisher()
    inp = ComponentInput(
        flow_run_id="fr-li-002",
        customer_id="cust-001",
        skill_config={"customer_fields": {"linkedin_access_token": "tok"}},
        run_context={},
        previous_step_output={"per_platform_variants": {}},
    )
    result = asyncio.run(pub.execute(inp))

    assert result.success is False
    assert "linkedin" in result.error_message.lower()


@pytest.mark.unit
def test_linkedin_publisher_registered_after_import():
    """get_component("LinkedInPublisher") succeeds after module import."""
    comp = get_component("LinkedInPublisher")
    assert comp.component_type == "LinkedInPublisher"
