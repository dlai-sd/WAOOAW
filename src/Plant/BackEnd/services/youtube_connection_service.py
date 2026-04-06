from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
import os
import secrets
import re

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from integrations.social.base import SocialPlatformError
from integrations.social.youtube_client import YouTubeClient
from models.customer_platform_credential import CustomerPlatformCredentialModel
from models.oauth_connection_session import OAuthConnectionSessionModel
from models.platform_connection import PlatformConnectionModel
from services.social_credential_resolver import CPSocialCredentialResolver, CredentialResolutionError, get_default_resolver


class YouTubeConnectionError(Exception):
    pass


@dataclass(frozen=True)
class StartConnectResult:
    state: str
    authorization_url: str
    expires_at: datetime


@dataclass(frozen=True)
class FinalizedCredentialResult:
    credential: CustomerPlatformCredentialModel
    secret_ref: str


@dataclass(frozen=True)
class RecentUploadPreview:
    video_id: str
    title: str
    published_at: str
    duration_seconds: int


@dataclass(frozen=True)
class ValidatedCredentialResult:
    credential: CustomerPlatformCredentialModel
    channel_count: int
    total_video_count: int
    recent_short_count: int
    recent_long_video_count: int
    subscriber_count: int
    view_count: int
    recent_uploads: list[RecentUploadPreview]
    next_action_hint: str


class YouTubeConnectionService:
    auth_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    channels_url = "https://www.googleapis.com/youtube/v3/channels"
    scopes = [
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]

    def __init__(
        self,
        *,
        db: AsyncSession,
        credential_resolver: CPSocialCredentialResolver | None = None,
    ) -> None:
        self._db = db
        self._credential_resolver = credential_resolver or get_default_resolver()

    def _oauth_client_id(self) -> str:
        return str(settings.google_client_id or "").strip()

    def _oauth_client_secret(self) -> str:
        return str(os.getenv("GOOGLE_CLIENT_SECRET") or "").strip()

    def _ensure_oauth_configured(self) -> None:
        if not self._oauth_client_id() or not self._oauth_client_secret():
            raise YouTubeConnectionError("youtube_oauth_not_configured")

    def _parse_iso8601_duration_seconds(self, raw_duration: str) -> int | None:
        match = re.fullmatch(
            r"P(?:\d+Y)?(?:\d+M)?(?:\d+W)?(?:\d+D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?",
            raw_duration,
        )
        if not match:
            return None

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds

    async def start_connect(self, *, customer_id: str, redirect_uri: str) -> StartConnectResult:
        self._ensure_oauth_configured()
        now = datetime.now(timezone.utc)
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(24)
        expires_at = now + timedelta(minutes=10)

        session = OAuthConnectionSessionModel(
            customer_id=customer_id,
            platform_key="youtube",
            state=state,
            nonce=nonce,
            redirect_uri=redirect_uri,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )
        self._db.add(session)
        await self._db.commit()

        params = {
            "client_id": self._oauth_client_id(),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "scope": " ".join(self.scopes),
            "state": state,
            "nonce": nonce,
        }
        return StartConnectResult(
            state=state,
            authorization_url=f"{self.auth_base_url}?{urlencode(params)}",
            expires_at=expires_at,
        )

    async def finalize_connect(
        self,
        *,
        customer_id: str,
        state: str,
        code: str,
        redirect_uri: str,
    ) -> FinalizedCredentialResult:
        session = await self._get_pending_session(customer_id=customer_id, state=state)
        if session.redirect_uri != redirect_uri:
            raise YouTubeConnectionError("redirect_uri_mismatch")

        token_payload = await self._exchange_code_for_tokens(code=code, redirect_uri=redirect_uri)
        access_token = str(token_payload.get("access_token") or "").strip()
        refresh_token = str(token_payload.get("refresh_token") or "").strip()
        if not access_token or not refresh_token:
            raise YouTubeConnectionError("missing_google_tokens")

        channel = await self._fetch_channel(access_token=access_token)
        provider_account_id = str(channel.get("id") or "").strip()
        if not provider_account_id:
            raise YouTubeConnectionError("missing_youtube_channel")

        channel_snippet = channel.get("snippet") or {}
        expires_in = int(token_payload.get("expires_in") or 3600)
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        granted_scopes = sorted(set(str(token_payload.get("scope") or "").split()))

        existing_credential = await self._find_credential_by_provider_account(
            customer_id=customer_id,
            provider_account_id=provider_account_id,
        )
        existing_ref = None
        if existing_credential is not None:
            candidate_ref = str(existing_credential.secret_ref or "").strip()
            if candidate_ref.startswith("CRED-"):
                existing_ref = candidate_ref

        try:
            stored_secret = await self._credential_resolver.upsert(
                customer_id=customer_id,
                platform="youtube",
                posting_identity=str(channel_snippet.get("title") or "YouTube Channel"),
                access_token=access_token,
                refresh_token=refresh_token,
                credential_ref=existing_ref,
                metadata={
                    "provider_account_id": provider_account_id,
                    "token_expires_at": token_expires_at.isoformat(),
                },
            )
        except CredentialResolutionError as exc:
            raise YouTubeConnectionError("credential_storage_failed") from exc

        credential = await self._upsert_customer_credential(
            customer_id=customer_id,
            provider_account_id=provider_account_id,
            display_name=str(channel_snippet.get("title") or "YouTube Channel"),
            granted_scopes=granted_scopes,
            secret_ref=stored_secret.credential_ref,
            token_expires_at=token_expires_at,
        )

        now = datetime.now(timezone.utc)
        session.status = "completed"
        session.consumed_at = now
        session.updated_at = now
        await self._db.commit()
        await self._db.refresh(credential)

        return FinalizedCredentialResult(credential=credential, secret_ref=stored_secret.credential_ref)

    async def _find_credential_by_provider_account(
        self,
        *,
        customer_id: str,
        provider_account_id: str,
    ) -> CustomerPlatformCredentialModel | None:
        result = await self._db.execute(
            select(CustomerPlatformCredentialModel)
            .where(CustomerPlatformCredentialModel.customer_id == customer_id)
            .where(CustomerPlatformCredentialModel.platform_key == "youtube")
            .where(CustomerPlatformCredentialModel.provider_account_id == provider_account_id)
        )
        return result.scalars().first()

    async def list_credentials(self, *, customer_id: str, platform_key: str = "youtube") -> list[CustomerPlatformCredentialModel]:
        result = await self._db.execute(
            select(CustomerPlatformCredentialModel)
            .where(CustomerPlatformCredentialModel.customer_id == customer_id)
            .where(CustomerPlatformCredentialModel.platform_key == platform_key)
            .order_by(CustomerPlatformCredentialModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_credential(self, *, customer_id: str, credential_id: str) -> CustomerPlatformCredentialModel | None:
        result = await self._db.execute(
            select(CustomerPlatformCredentialModel)
            .where(CustomerPlatformCredentialModel.id == credential_id)
            .where(CustomerPlatformCredentialModel.customer_id == customer_id)
        )
        return result.scalars().first()

    async def attach_connection_to_hired_agent(
        self,
        *,
        customer_id: str,
        credential_id: str,
        hired_instance_id: str,
        skill_id: str,
        platform_key: str = "youtube",
    ) -> PlatformConnectionModel:
        credential = await self.get_credential(customer_id=customer_id, credential_id=credential_id)
        if credential is None:
            raise YouTubeConnectionError("customer_platform_credential_not_found")

        result = await self._db.execute(
            select(PlatformConnectionModel)
            .where(PlatformConnectionModel.hired_instance_id == hired_instance_id)
            .where(PlatformConnectionModel.skill_id == skill_id)
            .where(PlatformConnectionModel.platform_key == platform_key)
        )
        connection = result.scalars().first()
        now = datetime.now(timezone.utc)
        if connection is None:
            connection = PlatformConnectionModel(
                hired_instance_id=hired_instance_id,
                skill_id=skill_id,
                platform_key=platform_key,
                customer_platform_credential_id=credential.id,
                secret_ref=credential.secret_ref,
                status="connected" if credential.connection_status == "connected" else "pending",
                connected_at=now if credential.connection_status == "connected" else None,
                last_verified_at=credential.last_verified_at,
                created_at=now,
                updated_at=now,
            )
            self._db.add(connection)
        else:
            connection.customer_platform_credential_id = credential.id
            connection.secret_ref = credential.secret_ref
            connection.status = "connected" if credential.connection_status == "connected" else connection.status
            connection.connected_at = connection.connected_at or (now if credential.connection_status == "connected" else None)
            connection.last_verified_at = credential.last_verified_at
            connection.updated_at = now
        await self._db.commit()
        await self._db.refresh(connection)
        return connection

    async def validate_connection(
        self,
        *,
        customer_id: str,
        credential_id: str,
    ) -> ValidatedCredentialResult:
        credential = await self.get_credential(customer_id=customer_id, credential_id=credential_id)
        if credential is None:
            raise YouTubeConnectionError("customer_platform_credential_not_found")

        client = YouTubeClient(customer_id=customer_id, credential_resolver=self._credential_resolver)

        try:
            access_token = await client._get_access_token(credential.secret_ref)
            channel_payload = await client._make_api_call_with_retry(
                endpoint="/channels",
                method="GET",
                access_token=access_token,
                params={"part": "snippet,statistics,contentDetails", "mine": "true"},
                credential_ref=credential.secret_ref,
            )
        except SocialPlatformError as exc:
            raise YouTubeConnectionError(exc.message) from exc
        except Exception as exc:  # noqa: BLE001
            raise YouTubeConnectionError(f"Failed to validate YouTube credentials: {exc}") from exc

        items = channel_payload.get("items") or []
        if not items:
            raise YouTubeConnectionError("No YouTube channel found for credentials")

        primary_channel = dict(items[0])
        snippet = primary_channel.get("snippet") or {}
        statistics = primary_channel.get("statistics") or {}
        content_details = primary_channel.get("contentDetails") or {}
        related_playlists = content_details.get("relatedPlaylists") or {}
        uploads_playlist_id = str(related_playlists.get("uploads") or "").strip()

        recent_short_count = 0
        recent_long_video_count = 0
        recent_uploads: list[RecentUploadPreview] = []
        if uploads_playlist_id:
            try:
                playlist_payload = await client._make_api_call_with_retry(
                    endpoint="/playlistItems",
                    method="GET",
                    access_token=access_token,
                    params={
                        "part": "contentDetails",
                        "playlistId": uploads_playlist_id,
                        "maxResults": "50",
                    },
                    credential_ref=credential.secret_ref,
                )
                video_ids = [
                    str(item.get("contentDetails", {}).get("videoId") or "").strip()
                    for item in (playlist_payload.get("items") or [])
                ]
                video_ids = [video_id for video_id in video_ids if video_id]
                if video_ids:
                    videos_payload = await client._make_api_call_with_retry(
                        endpoint="/videos",
                        method="GET",
                        access_token=access_token,
                        params={
                            "part": "contentDetails,snippet",
                            "id": ",".join(video_ids),
                            "maxResults": "50",
                        },
                        credential_ref=credential.secret_ref,
                    )
                    for video in (videos_payload.get("items") or []):
                        duration_raw = str(video.get("contentDetails", {}).get("duration") or "").strip()
                        if not duration_raw:
                            continue
                        duration_seconds = self._parse_iso8601_duration_seconds(duration_raw)
                        if duration_seconds is None:
                            continue
                        if duration_seconds <= 60:
                            recent_short_count += 1
                        else:
                            recent_long_video_count += 1
                        
                        # Collect preview data for up to 5 recent uploads
                        if len(recent_uploads) < 5:
                            video_id = str(video.get("id") or "").strip()
                            video_snippet = video.get("snippet") or {}
                            title = str(video_snippet.get("title") or "Untitled").strip()
                            published_at = str(video_snippet.get("publishedAt") or "").strip()
                            
                            recent_uploads.append(RecentUploadPreview(
                                video_id=video_id,
                                title=title,
                                published_at=published_at,
                                duration_seconds=duration_seconds,
                            ))
            except SocialPlatformError as exc:
                raise YouTubeConnectionError(exc.message) from exc
            except Exception:
                # Non-critical enrichment failure: keep validation successful with core channel stats.
                recent_short_count = 0
                recent_long_video_count = 0
                recent_uploads = []

        now = datetime.now(timezone.utc)
        credential.display_name = str(snippet.get("title") or credential.display_name or "YouTube Channel")
        credential.verification_status = "verified"
        credential.connection_status = "connected"
        credential.last_verified_at = now
        credential.updated_at = now
        await self._db.commit()
        await self._db.refresh(credential)

        # Determine next_action_hint based on token expiry and connection health
        next_action_hint = "connected_ready"
        if credential.token_expires_at:
            days_until_expiry = (credential.token_expires_at - now).days
            if days_until_expiry < 0:
                next_action_hint = "reconnect_required"
            elif days_until_expiry < 7:
                next_action_hint = "token_expiring_soon"

        return ValidatedCredentialResult(
            credential=credential,
            channel_count=len(items),
            total_video_count=int(statistics.get("videoCount") or 0),
            recent_short_count=recent_short_count,
            recent_long_video_count=recent_long_video_count,
            subscriber_count=int(statistics.get("subscriberCount") or 0),
            view_count=int(statistics.get("viewCount") or 0),
            recent_uploads=recent_uploads,
            next_action_hint=next_action_hint,
        )

    async def _get_pending_session(self, *, customer_id: str, state: str) -> OAuthConnectionSessionModel:
        result = await self._db.execute(
            select(OAuthConnectionSessionModel)
            .where(OAuthConnectionSessionModel.customer_id == customer_id)
            .where(OAuthConnectionSessionModel.platform_key == "youtube")
            .where(OAuthConnectionSessionModel.state == state)
            .where(OAuthConnectionSessionModel.status == "pending")
        )
        session = result.scalars().first()
        if session is None:
            raise YouTubeConnectionError("oauth_session_not_found")
        if session.expires_at < datetime.now(timezone.utc):
            raise YouTubeConnectionError("oauth_session_expired")
        return session

    async def _exchange_code_for_tokens(self, *, code: str, redirect_uri: str) -> dict[str, Any]:
        self._ensure_oauth_configured()
        payload = {
            "code": code,
            "client_id": self._oauth_client_id(),
            "client_secret": self._oauth_client_secret(),
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(self.token_url, data=payload)
        if response.status_code != 200:
            raise YouTubeConnectionError("google_token_exchange_failed")
        return response.json()

    async def _fetch_channel(self, *, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                self.channels_url,
                headers={"Authorization": f"Bearer {access_token}"},
                params={"part": "id,snippet", "mine": "true"},
            )
        if response.status_code != 200:
            raise YouTubeConnectionError("youtube_channel_lookup_failed")
        payload = response.json()
        items = payload.get("items") or []
        if not items:
            raise YouTubeConnectionError("youtube_channel_not_found")
        return dict(items[0])

    async def _upsert_customer_credential(
        self,
        *,
        customer_id: str,
        provider_account_id: str,
        display_name: str,
        granted_scopes: list[str],
        secret_ref: str,
        token_expires_at: datetime,
    ) -> CustomerPlatformCredentialModel:
        result = await self._db.execute(
            select(CustomerPlatformCredentialModel)
            .where(CustomerPlatformCredentialModel.customer_id == customer_id)
            .where(CustomerPlatformCredentialModel.platform_key == "youtube")
            .where(CustomerPlatformCredentialModel.provider_account_id == provider_account_id)
        )
        credential = result.scalars().first()
        now = datetime.now(timezone.utc)
        if credential is None:
            credential = CustomerPlatformCredentialModel(
                customer_id=customer_id,
                platform_key="youtube",
                provider_account_id=provider_account_id,
                display_name=display_name,
                granted_scopes=granted_scopes,
                verification_status="verified",
                connection_status="connected",
                secret_ref=secret_ref,
                token_expires_at=token_expires_at,
                last_verified_at=now,
                created_at=now,
                updated_at=now,
            )
            self._db.add(credential)
        else:
            credential.display_name = display_name
            credential.granted_scopes = granted_scopes
            credential.verification_status = "verified"
            credential.connection_status = "connected"
            credential.secret_ref = secret_ref
            credential.token_expires_at = token_expires_at
            credential.last_verified_at = now
            credential.updated_at = now
        await self._db.flush()
        return credential