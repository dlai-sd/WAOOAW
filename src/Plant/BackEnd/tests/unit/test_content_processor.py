"""Unit tests for ContentProcessor component (EXEC-ENGINE-001 E7-S2).

Tests:
  E7-S2-T1: Mock LLM returns "Great post!", platform_specs=[{platform:linkedin}]
             → success=True, data["per_platform_variants"]["linkedin"]["post_text"]="Great post!"
  E7-S2-T2: Mock LLM returns HTTP 429 (rate limit)
             → safe_execute() returns success=False
  E7-S2-T3: Inspect log records captured during execute
             → OpenAI API key value does NOT appear in any log record
"""
from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from components import ComponentInput, get_component


def _make_input(platform_specs: list[dict] | None = None, openai_api_key: str = "test-key-secret") -> ComponentInput:
    return ComponentInput(
        flow_run_id="fr-cp-001",
        customer_id="cust-001",
        skill_config={
            "pp_locked_fields": {"brand_voice_model": "gpt-4o-mini"},
            "customer_fields": {"openai_api_key": openai_api_key},
        },
        run_context={},
        previous_step_output={
            "brief_payload": {
                "campaign_brief": "Promote our product",
                "brand_name": "WAOOAW",
                "tone": "professional",
                "audience": "tech founders",
                "content_type": "post",
            },
            "platform_specs": platform_specs or [{"platform": "linkedin", "format": "post"}],
        },
    )


@pytest.fixture(autouse=True)
def _ensure_content_processor_registered():
    """Import module to trigger register_component() — makes tests order-independent."""
    from components import register_component
    import content_processor as _mod

    register_component(_mod.ContentProcessor())


@pytest.mark.unit
def test_content_processor_success():
    """E7-S2-T1: Mock LLM returns text → success=True, per_platform_variants populated."""
    from content_processor import ContentProcessor

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Great post!"}}]
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    proc = ContentProcessor()

    with patch("content_processor.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(proc.execute(_make_input()))

    assert result.success is True
    assert result.data["per_platform_variants"]["linkedin"]["post_text"] == "Great post!"


@pytest.mark.unit
def test_content_processor_llm_rate_limit():
    """E7-S2-T2: LLM returns HTTP 429 → safe_execute() returns success=False."""
    import httpx
    from content_processor import ContentProcessor

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=MagicMock(),
            response=MagicMock(status_code=429),
        )
    )

    proc = ContentProcessor()

    with patch("content_processor.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(proc.safe_execute(_make_input()))

    assert result.success is False
    assert result.error_message


@pytest.mark.unit
def test_content_processor_api_key_not_logged(caplog):
    """E7-S2-T3: API key must not appear in log records."""
    from content_processor import ContentProcessor

    secret_key = "super-secret-openai-key-12345"

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Content generated"}}]
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    proc = ContentProcessor()

    with caplog.at_level(logging.DEBUG), patch(
        "content_processor.httpx.AsyncClient", return_value=mock_client
    ):
        asyncio.run(proc.execute(_make_input(openai_api_key=secret_key)))

    for record in caplog.records:
        assert secret_key not in record.getMessage(), (
            f"API key found in log record: {record.getMessage()}"
        )


@pytest.mark.unit
def test_content_processor_registered_after_import():
    """get_component("ContentProcessor") succeeds after module import."""
    comp = get_component("ContentProcessor")
    assert comp.component_type == "ContentProcessor"
