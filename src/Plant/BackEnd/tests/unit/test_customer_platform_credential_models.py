from __future__ import annotations

from datetime import datetime, timezone

import pytest

from models.customer_platform_credential import CustomerPlatformCredentialModel
from models.oauth_connection_session import OAuthConnectionSessionModel


@pytest.mark.unit
def test_customer_platform_credential_tablename():
    assert CustomerPlatformCredentialModel.__tablename__ == "customer_platform_credentials"


@pytest.mark.unit
def test_customer_platform_credential_defaults():
    credential = CustomerPlatformCredentialModel(
        customer_id="cust-1",
        platform_key="youtube",
        provider_account_id="channel-1",
        display_name="Channel One",
        secret_ref="projects/waooaw-oauth/secrets/customer-platform-youtube-cust-1/versions/latest",
    )
    assert credential.verification_status == "pending"
    assert credential.connection_status == "pending"
    assert credential.granted_scopes == []


@pytest.mark.unit
def test_customer_platform_credential_accepts_explicit_verification_fields():
    ts = datetime(2026, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
    credential = CustomerPlatformCredentialModel(
        customer_id="cust-1",
        platform_key="youtube",
        provider_account_id="channel-1",
        display_name="Channel One",
        granted_scopes=["scope-a", "scope-b"],
        verification_status="verified",
        connection_status="connected",
        secret_ref="projects/waooaw-oauth/secrets/customer-platform-youtube-cust-1/versions/latest",
        token_expires_at=ts,
        last_verified_at=ts,
    )
    assert credential.verification_status == "verified"
    assert credential.connection_status == "connected"
    assert credential.granted_scopes == ["scope-a", "scope-b"]
    assert credential.token_expires_at == ts


@pytest.mark.unit
def test_oauth_connection_session_tablename():
    assert OAuthConnectionSessionModel.__tablename__ == "oauth_connection_sessions"


@pytest.mark.unit
def test_oauth_connection_session_defaults():
    expires_at = datetime(2026, 3, 16, 11, 0, 0, tzinfo=timezone.utc)
    session = OAuthConnectionSessionModel(
        customer_id="cust-1",
        platform_key="youtube",
        state="state-123",
        nonce="nonce-123",
        redirect_uri="https://cp.demo.waooaw.com/oauth/youtube/callback",
        expires_at=expires_at,
    )
    assert session.status == "pending"
    assert session.consumed_at is None
    assert session.expires_at == expires_at