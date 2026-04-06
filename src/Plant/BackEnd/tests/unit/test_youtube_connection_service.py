from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.config import settings
from models.customer_platform_credential import CustomerPlatformCredentialModel
from models.oauth_connection_session import OAuthConnectionSessionModel
from services.social_credential_resolver import CredentialResolutionError, StoredSocialCredentials
from services.youtube_connection_service import YouTubeConnectionError, YouTubeConnectionService


@pytest.mark.asyncio
async def test_start_connect_persists_session_and_returns_google_url(monkeypatch):
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    monkeypatch.setattr(settings, "google_client_id", "test-google-client-id", raising=False)
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-google-client-secret")

    service = YouTubeConnectionService(db=db)
    result = await service.start_connect(
        customer_id="cust-1",
        redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
    )

    assert result.state
    assert "accounts.google.com" in result.authorization_url
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_start_connect_rejects_missing_youtube_oauth_config(monkeypatch):
    db = AsyncMock()
    monkeypatch.setattr(settings, "google_client_id", "", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)

    service = YouTubeConnectionService(db=db)

    with pytest.raises(YouTubeConnectionError, match="youtube_oauth_not_configured"):
        await service.start_connect(
            customer_id="cust-1",
            redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
        )


@pytest.mark.asyncio
async def test_start_connect_falls_back_to_google_oauth_config(monkeypatch):
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    monkeypatch.setattr(settings, "google_client_id", "google-web-client-id", raising=False)
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "google-web-client-secret")

    service = YouTubeConnectionService(db=db)
    result = await service.start_connect(
        customer_id="cust-1",
        redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
    )

    assert "client_id=google-web-client-id" in result.authorization_url


@pytest.mark.asyncio
async def test_finalize_connect_creates_verified_customer_credential():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    session = OAuthConnectionSessionModel(
        customer_id="cust-1",
        platform_key="youtube",
        state="state-123",
        nonce="nonce-123",
        redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    pending_result = MagicMock()
    pending_result.scalars.return_value.first.return_value = session

    existing_credential_result = MagicMock()
    existing_credential_result.scalars.return_value.first.return_value = None

    upsert_result = MagicMock()
    upsert_result.scalars.return_value.first.return_value = None

    db.execute = AsyncMock(side_effect=[pending_result, existing_credential_result, upsert_result])

    resolver = MagicMock()
    resolver.upsert = AsyncMock(
        return_value=StoredSocialCredentials(
            credential_ref="CRED-youtube-1",
            customer_id="cust-1",
            platform="youtube",
            posting_identity="Channel One",
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
    )

    service = YouTubeConnectionService(db=db, credential_resolver=resolver)
    with patch.object(
        service,
        "_exchange_code_for_tokens",
        AsyncMock(
            return_value={
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "scope": "scope-a scope-b",
                "expires_in": 3600,
            }
        ),
    ), patch.object(
        service,
        "_fetch_channel",
        AsyncMock(return_value={"id": "channel-1", "snippet": {"title": "Channel One"}}),
    ):
        result = await service.finalize_connect(
            customer_id="cust-1",
            state="state-123",
            code="google-auth-code",
            redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
        )

    assert isinstance(result.credential, CustomerPlatformCredentialModel)
    assert result.credential.connection_status == "connected"
    assert result.credential.verification_status == "verified"
    assert result.credential.provider_account_id == "channel-1"
    assert result.credential.secret_ref == "CRED-youtube-1"
    resolver.upsert.assert_awaited_once()


@pytest.mark.asyncio
async def test_finalize_connect_returns_storage_error_when_cp_vault_fails():
    db = AsyncMock()

    session = OAuthConnectionSessionModel(
        customer_id="cust-1",
        platform_key="youtube",
        state="state-123",
        nonce="nonce-123",
        redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    pending_result = MagicMock()
    pending_result.scalars.return_value.first.return_value = session

    existing_credential_result = MagicMock()
    existing_credential_result.scalars.return_value.first.return_value = None
    db.execute = AsyncMock(side_effect=[pending_result, existing_credential_result])

    resolver = MagicMock()
    resolver.upsert = AsyncMock(side_effect=CredentialResolutionError("vault down"))

    service = YouTubeConnectionService(db=db, credential_resolver=resolver)
    with patch.object(
        service,
        "_exchange_code_for_tokens",
        AsyncMock(
            return_value={
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "scope": "scope-a scope-b",
                "expires_in": 3600,
            }
        ),
    ), patch.object(
        service,
        "_fetch_channel",
        AsyncMock(return_value={"id": "channel-1", "snippet": {"title": "Channel One"}}),
    ):
        with pytest.raises(YouTubeConnectionError, match="credential_storage_failed"):
            await service.finalize_connect(
                customer_id="cust-1",
                state="state-123",
                code="google-auth-code",
                redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
            )


@pytest.mark.asyncio
async def test_finalize_connect_rejects_expired_session():
    db = AsyncMock()
    expired_session = OAuthConnectionSessionModel(
        customer_id="cust-1",
        platform_key="youtube",
        state="expired-state",
        nonce="nonce-123",
        redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    result = MagicMock()
    result.scalars.return_value.first.return_value = expired_session
    db.execute = AsyncMock(return_value=result)

    service = YouTubeConnectionService(db=db)
    with pytest.raises(YouTubeConnectionError):
        await service.finalize_connect(
            customer_id="cust-1",
            state="expired-state",
            code="google-auth-code",
            redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
        )


@pytest.mark.asyncio
async def test_attach_connection_to_hired_agent_uses_customer_credential():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

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
        last_verified_at=datetime.now(timezone.utc),
    )

    credential_result = MagicMock()
    credential_result.scalars.return_value.first.return_value = credential
    connection_result = MagicMock()
    connection_result.scalars.return_value.first.return_value = None
    db.execute = AsyncMock(side_effect=[credential_result, connection_result])

    service = YouTubeConnectionService(db=db)
    connection = await service.attach_connection_to_hired_agent(
        customer_id="cust-1",
        credential_id="cred-1",
        hired_instance_id="hired-1",
        skill_id="skill-1",
    )

    assert connection.customer_platform_credential_id == "cred-1"
    assert connection.status == "connected"


@pytest.mark.asyncio
async def test_validate_connection_returns_channel_metrics_and_refreshes_credential():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    credential = CustomerPlatformCredentialModel(
        id="cred-1",
        customer_id="cust-1",
        platform_key="youtube",
        provider_account_id="channel-1",
        display_name="Channel One",
        granted_scopes=["scope-a"],
        verification_status="pending",
        connection_status="pending",
        secret_ref="CRED-youtube-1",
        last_verified_at=None,
    )

    credential_result = MagicMock()
    credential_result.scalars.return_value.first.return_value = credential
    db.execute = AsyncMock(return_value=credential_result)

    resolver = MagicMock()
    service = YouTubeConnectionService(db=db, credential_resolver=resolver)
    client = AsyncMock()
    client._get_access_token = AsyncMock(return_value="access-token")
    client._make_api_call_with_retry = AsyncMock(
        side_effect=[
            {
                "items": [
                    {
                        "id": "channel-1",
                        "snippet": {"title": "Channel One"},
                        "statistics": {
                            "videoCount": "42",
                            "subscriberCount": "1200",
                            "viewCount": "54000",
                        },
                        "contentDetails": {"relatedPlaylists": {"uploads": "uploads-1"}},
                    }
                ]
            },
            {
                "items": [
                    {"contentDetails": {"videoId": "video-1"}},
                    {"contentDetails": {"videoId": "video-2"}},
                ]
            },
            {
                "items": [
                    {"contentDetails": {"duration": "PT45S"}},
                    {"contentDetails": {"duration": "PT5M"}},
                ]
            },
        ]
    )

    with patch("services.youtube_connection_service.YouTubeClient", return_value=client):
        result = await service.validate_connection(customer_id="cust-1", credential_id="cred-1")

    assert result.credential.id == "cred-1"
    assert result.channel_count == 1
    assert result.total_video_count == 42
    assert result.recent_short_count == 1
    assert result.recent_long_video_count == 1
    assert result.subscriber_count == 1200
    assert result.view_count == 54000
    assert credential.verification_status == "verified"
    assert credential.connection_status == "connected"
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(credential)