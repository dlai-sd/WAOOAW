from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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