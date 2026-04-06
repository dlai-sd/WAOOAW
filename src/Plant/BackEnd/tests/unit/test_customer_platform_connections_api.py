from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from models.customer_platform_credential import CustomerPlatformCredentialModel


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


def test_customer_platform_connections_router_prefix():
    from api.v1.platform_connections import customer_router

    assert customer_router.prefix == "/customer-platform-connections"


def test_customer_platform_connections_routes_registered():
    from api.v1.platform_connections import customer_router

    routes = {(frozenset(route.methods), route.path) for route in customer_router.routes}
    assert any("POST" in methods and path.endswith("/youtube/connect/start") for methods, path in routes)
    assert any("POST" in methods and path.endswith("/youtube/connect/finalize") for methods, path in routes)
    assert any("GET" in methods and path.endswith("/{customer_id}") for methods, path in routes)
    assert any("POST" in methods and path.endswith("/{credential_id}/attach") for methods, path in routes)
    assert any("POST" in methods and path.endswith("/{credential_id}/validate") for methods, path in routes)


@pytest.mark.asyncio
async def test_start_youtube_connect_maps_service_result(mock_db):
    from api.v1.platform_connections import StartYouTubeConnectRequest, start_youtube_connect

    service_result = MagicMock(
        state="state-123",
        authorization_url="https://accounts.google.com/o/oauth2/v2/auth?state=state-123",
        expires_at=datetime(2026, 3, 16, 12, 0, 0, tzinfo=timezone.utc),
    )

    with patch(
        "api.v1.platform_connections.YouTubeConnectionService.start_connect",
        AsyncMock(return_value=service_result),
    ):
        response = await start_youtube_connect(
            StartYouTubeConnectRequest(
                customer_id="cust-1",
                redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
            ),
            db=mock_db,
        )

    assert response.state == "state-123"
    assert "accounts.google.com" in response.authorization_url


@pytest.mark.asyncio
async def test_start_youtube_connect_returns_503_when_oauth_not_configured(mock_db):
    from api.v1.platform_connections import StartYouTubeConnectRequest, start_youtube_connect
    from services.youtube_connection_service import YouTubeConnectionError

    with patch(
        "api.v1.platform_connections.YouTubeConnectionService.start_connect",
        AsyncMock(side_effect=YouTubeConnectionError("youtube_oauth_not_configured")),
    ):
        with pytest.raises(HTTPException) as excinfo:
            await start_youtube_connect(
                StartYouTubeConnectRequest(
                    customer_id="cust-1",
                    redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
                ),
                db=mock_db,
            )

    assert excinfo.value.status_code == 503
    assert excinfo.value.detail == "YouTube OAuth is not configured on the Plant backend."


@pytest.mark.asyncio
async def test_finalize_youtube_connect_returns_503_when_credential_vault_is_unavailable(mock_db):
    from api.v1.platform_connections import FinalizeYouTubeConnectRequest, finalize_youtube_connect
    from services.youtube_connection_service import YouTubeConnectionError

    with patch(
        "api.v1.platform_connections.YouTubeConnectionService.finalize_connect",
        AsyncMock(side_effect=YouTubeConnectionError("credential_storage_failed")),
    ):
        with pytest.raises(HTTPException) as excinfo:
            await finalize_youtube_connect(
                FinalizeYouTubeConnectRequest(
                    customer_id="cust-1",
                    state="state-123",
                    code="google-auth-code",
                    redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
                ),
                db=mock_db,
            )

    assert excinfo.value.status_code == 503
    assert excinfo.value.detail == "YouTube credential vault is unavailable."


@pytest.mark.asyncio
async def test_finalize_youtube_connect_returns_customer_credential(mock_db):
    from api.v1.platform_connections import FinalizeYouTubeConnectRequest, finalize_youtube_connect

    now = datetime.now(timezone.utc)
    credential = CustomerPlatformCredentialModel(
        id="cred-1",
        customer_id="cust-1",
        platform_key="youtube",
        provider_account_id="channel-1",
        display_name="Channel One",
        granted_scopes=["scope-a"],
        verification_status="verified",
        connection_status="connected",
        secret_ref="projects/waooaw-oauth/secrets/customer-platform-youtube-cust-1/versions/latest",
        last_verified_at=now,
        created_at=now,
        updated_at=now,
    )
    service_result = MagicMock(credential=credential)

    with patch(
        "api.v1.platform_connections.YouTubeConnectionService.finalize_connect",
        AsyncMock(return_value=service_result),
    ):
        response = await finalize_youtube_connect(
            FinalizeYouTubeConnectRequest(
                customer_id="cust-1",
                state="state-123",
                code="google-auth-code",
                redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
            ),
            db=mock_db,
        )

    assert response.id == "cred-1"
    assert response.connection_status == "connected"


@pytest.mark.asyncio
async def test_list_customer_platform_credentials_maps_service_rows(mock_db):
    from api.v1.platform_connections import list_customer_platform_credentials

    now = datetime.now(timezone.utc)
    credential = CustomerPlatformCredentialModel(
        id="cred-1",
        customer_id="cust-1",
        platform_key="youtube",
        provider_account_id="channel-1",
        display_name="Channel One",
        granted_scopes=["scope-a"],
        verification_status="verified",
        connection_status="connected",
        secret_ref="projects/waooaw-oauth/secrets/customer-platform-youtube-cust-1/versions/latest",
        last_verified_at=now,
        created_at=now,
        updated_at=now,
    )

    with patch(
        "api.v1.platform_connections.YouTubeConnectionService.list_credentials",
        AsyncMock(return_value=[credential]),
    ):
        response = await list_customer_platform_credentials("cust-1", db=mock_db)

    assert len(response) == 1
    assert response[0].display_name == "Channel One"


@pytest.mark.asyncio
async def test_attach_customer_platform_credential_maps_connection(mock_db):
    from api.v1.platform_connections import AttachCustomerCredentialRequest, attach_customer_platform_credential

    connection = MagicMock(
        id="conn-1",
        hired_instance_id="hired-1",
        skill_id="skill-1",
        customer_platform_credential_id="cred-1",
        platform_key="youtube",
        status="connected",
        connected_at=datetime.now(timezone.utc),
        last_verified_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with patch(
        "api.v1.platform_connections.YouTubeConnectionService.attach_connection_to_hired_agent",
        AsyncMock(return_value=connection),
    ):
        response = await attach_customer_platform_credential(
            "cred-1",
            AttachCustomerCredentialRequest(
                customer_id="cust-1",
                hired_instance_id="hired-1",
                skill_id="skill-1",
            ),
            db=mock_db,
        )

    assert response.id == "conn-1"
    assert response.customer_platform_credential_id == "cred-1"


@pytest.mark.asyncio
async def test_validate_customer_platform_credential_maps_validation_result(mock_db):
    from api.v1.platform_connections import ValidateCustomerCredentialRequest, validate_customer_platform_credential

    now = datetime.now(timezone.utc)
    credential = CustomerPlatformCredentialModel(
        id="cred-1",
        customer_id="cust-1",
        platform_key="youtube",
        provider_account_id="channel-1",
        display_name="Channel One",
        granted_scopes=["scope-a"],
        verification_status="verified",
        connection_status="connected",
        secret_ref="projects/waooaw-oauth/secrets/customer-platform-youtube-cust-1/versions/latest",
        last_verified_at=now,
        created_at=now,
        updated_at=now,
    )
    service_result = MagicMock(
        credential=credential,
        channel_count=1,
        total_video_count=42,
        recent_short_count=7,
        recent_long_video_count=35,
        subscriber_count=1200,
        view_count=54000,
    )

    with patch(
        "api.v1.platform_connections.YouTubeConnectionService.validate_connection",
        AsyncMock(return_value=service_result),
    ):
        response = await validate_customer_platform_credential(
            "cred-1",
            ValidateCustomerCredentialRequest(customer_id="cust-1"),
            db=mock_db,
        )

    assert response.id == "cred-1"
    assert response.total_video_count == 42
    assert response.recent_short_count == 7


# E4-S1 Tests: Enriched YouTube validation with recent upload proof
@pytest.mark.asyncio
async def test_validate_with_preview_items_includes_recent_uploads(mock_db):
    """E4-S1-T1: Mock validate result with preview items — response includes preview list and next-action hint."""
    from api.v1.platform_connections import ValidateCustomerCredentialRequest, validate_customer_platform_credential
    from services.youtube_connection_service import RecentUploadPreview

    now = datetime.now(timezone.utc)
    credential = CustomerPlatformCredentialModel(
        id="cred-1",
        customer_id="cust-1",
        platform_key="youtube",
        provider_account_id="channel-1",
        display_name="Channel One",
        granted_scopes=["scope-a"],
        verification_status="verified",
        connection_status="connected",
        secret_ref="projects/waooaw-oauth/secrets/customer-platform-youtube-cust-1/versions/latest",
        last_verified_at=now,
        created_at=now,
        updated_at=now,
    )
    
    preview_items = [
        RecentUploadPreview(
            video_id="vid-1",
            title="Recent Video 1",
            published_at="2026-04-01T10:00:00Z",
            duration_seconds=300,
        ),
        RecentUploadPreview(
            video_id="vid-2",
            title="Recent Video 2",
            published_at="2026-04-02T10:00:00Z",
            duration_seconds=120,
        ),
    ]
    
    service_result = MagicMock(
        credential=credential,
        channel_count=1,
        total_video_count=42,
        recent_short_count=1,
        recent_long_video_count=1,
        subscriber_count=1200,
        view_count=54000,
        recent_uploads=preview_items,
        next_action_hint="connected_ready",
    )

    with patch(
        "api.v1.platform_connections.YouTubeConnectionService.validate_connection",
        AsyncMock(return_value=service_result),
    ):
        response = await validate_customer_platform_credential(
            "cred-1",
            ValidateCustomerCredentialRequest(customer_id="cust-1"),
            db=mock_db,
        )

    assert response.id == "cred-1"
    assert len(response.recent_uploads) == 2
    assert response.recent_uploads[0].video_id == "vid-1"
    assert response.recent_uploads[0].title == "Recent Video 1"
    assert response.next_action_hint == "connected_ready"


@pytest.mark.asyncio
async def test_validate_preserves_existing_aggregate_fields(mock_db):
    """E4-S1-T2: Existing customer-scoped validate call — aggregate fields still exist."""
    from api.v1.platform_connections import ValidateCustomerCredentialRequest, validate_customer_platform_credential

    now = datetime.now(timezone.utc)
    credential = CustomerPlatformCredentialModel(
        id="cred-1",
        customer_id="cust-1",
        platform_key="youtube",
        provider_account_id="channel-1",
        display_name="Channel One",
        granted_scopes=["scope-a"],
        verification_status="verified",
        connection_status="connected",
        secret_ref="projects/waooaw-oauth/secrets/customer-platform-youtube-cust-1/versions/latest",
        last_verified_at=now,
        created_at=now,
        updated_at=now,
    )
    service_result = MagicMock(
        credential=credential,
        channel_count=1,
        total_video_count=42,
        recent_short_count=7,
        recent_long_video_count=35,
        subscriber_count=1200,
        view_count=54000,
        recent_uploads=[],
        next_action_hint="connected_ready",
    )

    with patch(
        "api.v1.platform_connections.YouTubeConnectionService.validate_connection",
        AsyncMock(return_value=service_result),
    ):
        response = await validate_customer_platform_credential(
            "cred-1",
            ValidateCustomerCredentialRequest(customer_id="cust-1"),
            db=mock_db,
        )

    assert response.total_video_count == 42
    assert response.recent_short_count == 7
    assert response.recent_long_video_count == 35
    assert response.subscriber_count == 1200
    assert response.view_count == 54000
    assert response.channel_count == 1


@pytest.mark.asyncio
async def test_validate_handles_missing_credential_error(mock_db):
    """E4-S1-T3: Wrong or missing credential — existing error contract remains intact."""
    from api.v1.platform_connections import ValidateCustomerCredentialRequest, validate_customer_platform_credential
    from services.youtube_connection_service import YouTubeConnectionError

    with patch(
        "api.v1.platform_connections.YouTubeConnectionService.validate_connection",
        AsyncMock(side_effect=YouTubeConnectionError("customer_platform_credential_not_found")),
    ):
        with pytest.raises(HTTPException) as excinfo:
            await validate_customer_platform_credential(
                "cred-1",
                ValidateCustomerCredentialRequest(customer_id="cust-1"),
                db=mock_db,
            )

    assert excinfo.value.status_code == 404
    assert "not found" in excinfo.value.detail.lower()