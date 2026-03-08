"""Unit tests for YouTubePublisher component (EXEC-ENGINE-001 E7-S3).

Tests:
  E7-S3-T3: previous_step_output.per_platform_variants.youtube set, mock HTTP 200
             → success=True, data["platform"]="youtube"
  E7-S3-T4: YouTube API returns HTTP 5xx (server error)
             → safe_execute() returns success=False
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from components import ComponentInput, get_component


def _make_input(youtube_variant: dict | None = None) -> ComponentInput:
    if youtube_variant is None:
        youtube_variant = {"post_text": "Check out our new video!", "hashtags": [], "format": "video"}
    return ComponentInput(
        flow_run_id="fr-yt-001",
        customer_id="cust-001",
        skill_config={
            "customer_fields": {"youtube_api_key": "test-yt-key"},
        },
        run_context={},
        previous_step_output={
            "per_platform_variants": {
                "youtube": youtube_variant,
            }
        },
    )


@pytest.fixture(autouse=True)
def _ensure_youtube_publisher_registered():
    """Import module to trigger register_component() — makes tests order-independent."""
    from components import register_component
    import youtube_publisher as _mod

    register_component(_mod.YouTubePublisher())


@pytest.mark.unit
def test_youtube_publisher_success():
    """E7-S3-T3: YouTube mock HTTP 200 → success=True, platform=youtube."""
    from youtube_publisher import YouTubePublisher

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"id": "yt-post-456"}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    pub = YouTubePublisher()

    with patch("youtube_publisher.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(pub.execute(_make_input()))

    assert result.success is True
    assert result.data["platform"] == "youtube"


@pytest.mark.unit
def test_youtube_publisher_server_error():
    """E7-S3-T4: YouTube API 5xx → safe_execute() returns success=False."""
    import httpx
    from youtube_publisher import YouTubePublisher

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=MagicMock(status_code=500),
        )
    )

    pub = YouTubePublisher()

    with patch("youtube_publisher.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(pub.safe_execute(_make_input()))

    assert result.success is False
    assert result.error_message


@pytest.mark.unit
def test_youtube_publisher_no_variant():
    """Missing youtube variant in previous_step_output → success=False."""
    from youtube_publisher import YouTubePublisher

    pub = YouTubePublisher()
    inp = ComponentInput(
        flow_run_id="fr-yt-002",
        customer_id="cust-001",
        skill_config={"customer_fields": {"youtube_api_key": "key"}},
        run_context={},
        previous_step_output={"per_platform_variants": {}},
    )
    result = asyncio.run(pub.execute(inp))

    assert result.success is False
    assert result.error_message


@pytest.mark.unit
def test_youtube_publisher_registered_after_import():
    """get_component("YouTubePublisher") succeeds after module import."""
    comp = get_component("YouTubePublisher")
    assert comp.component_type == "YouTubePublisher"
