"""Instagram Business API (Graph API) client for posting content.

Implements production-ready Instagram integration with:
- Real Facebook Graph API authentication
- Feed posts (square/portrait images)
- Stories (24hr expiry)
- Reels (video content)
- Two-step media upload flow
- Exponential backoff retry logic
- Rate limit tracking (200 calls/hour)
- Comprehensive error classification
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, Literal

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from integrations.social.base import (
    SocialPlatformClient,
    SocialPostResult,
    SocialPlatformError,
)
from services.social_credential_resolver import (
    CPSocialCredentialResolver,
    get_default_resolver,
    CredentialResolutionError,
)


logger = logging.getLogger(__name__)


# Transient errors that should trigger retry
class _TransientInstagramError(Exception):
    """Marker exception for transient errors that should be retried."""
    pass


class InstagramClient(SocialPlatformClient):
    """Instagram Business API (Graph API) client for posting content."""
    
    def __init__(
        self, 
        api_version: str = "v18.0",
        rate_limit_per_hour: int = 200,
        credential_resolver: Optional[CPSocialCredentialResolver] = None,
        customer_id: Optional[str] = None,
    ):
        """Initialize Instagram client.
        
        Args:
            api_version: Facebook Graph API version (default: v18.0)
            rate_limit_per_hour: Rate limit per hour (default: 200)
            credential_resolver: Resolver for credential_ref → secrets
            customer_id: Customer ID for credential resolution
        """
        self.api_base_url = f"https://graph.facebook.com/{api_version}"
        self.api_version = api_version
        
        self.rate_limit_per_hour = rate_limit_per_hour
        self.calls_made = 0
        
        # Credential resolver (Plant → CP Backend)
        self._resolver = credential_resolver or get_default_resolver()
        self._customer_id = customer_id  # Set by service layer from context
    
    async def post_text(
        self,
        credential_ref: str,
        text: str,
        image_url: Optional[str] = None
    ) -> SocialPostResult:
        """Post to Instagram feed (requires image for Instagram).
        
        Instagram requires images for feed posts. This delegates to post_feed().
        
        Args:
            credential_ref: Reference to OAuth2 credentials in CP Backend
            text: Caption text (max 2,200 characters)
            image_url: Image URL (REQUIRED for Instagram)
            
        Returns:
            SocialPostResult with post_id and URL
            
        Raises:
            SocialPlatformError: If image_url is missing or posting fails
        """
        if not image_url:
            raise SocialPlatformError(
                message="Instagram feed posts require an image",
                platform="instagram",
                error_code="IMAGE_REQUIRED",
                is_transient=False
            )
        
        return await self.post_feed(
            credential_ref=credential_ref,
            caption=text,
            image_url=image_url,
        )
    
    async def post_feed(
        self,
        credential_ref: str,
        caption: str,
        image_url: str,
        location_id: Optional[str] = None,
    ) -> SocialPostResult:
        """Create Instagram feed post (image + caption).
        
        Two-step process:
        1. Create media container (upload)
        2. Publish container
        
        Args:
            credential_ref: Reference to OAuth2 credentials
            caption: Post caption (max 2,200 characters)
            image_url: Image URL (publicly accessible)
            location_id: Optional location ID for tagging
            
        Returns:
            SocialPostResult with post_id and URL
            
        Raises:
            SocialPlatformError: If posting fails
        """
        try:
            # Validate caption length
            if len(caption) > 2200:
                raise SocialPlatformError(
                    message="Instagram captions limited to 2,200 characters",
                    platform="instagram",
                    error_code="CAPTION_TOO_LONG",
                    is_transient=False
                )
            
            # Resolve credentials
            credentials = await self._get_credentials(credential_ref)
            access_token = credentials.access_token
            
            # Get Instagram Business Account ID from posting_identity
            # Format: "IG:{instagram_business_account_id}"
            ig_account_id = credentials.posting_identity
            if ig_account_id and ig_account_id.startswith("IG:"):
                ig_account_id = ig_account_id[3:]
            
            if not ig_account_id:
                raise SocialPlatformError(
                    message="Instagram Business Account ID not found in credentials",
                    platform="instagram",
                    error_code="MISSING_ACCOUNT_ID",
                    is_transient=False
                )
            
            # Step 1: Create media container
            container_data = {
                "image_url": image_url,
                "caption": caption,
            }
            if location_id:
                container_data["location_id"] = location_id
            
            container_response = await self._make_api_call_with_retry(
                endpoint=f"/{ig_account_id}/media",
                method="POST",
                access_token=access_token,
                params=container_data,
                credential_ref=credential_ref,
            )
            
            container_id = container_response.get("id")
            if not container_id:
                raise SocialPlatformError(
                    message="Failed to create media container",
                    platform="instagram",
                    error_code="CONTAINER_CREATION_FAILED",
                    is_transient=True
                )
            
            # Step 2: Publish container
            publish_response = await self._make_api_call_with_retry(
                endpoint=f"/{ig_account_id}/media_publish",
                method="POST",
                access_token=access_token,
                params={"creation_id": container_id},
                credential_ref=credential_ref,
            )
            
            media_id = publish_response.get("id")
            
            # Track API calls (2 calls: container + publish)
            self.calls_made += 2
            
            return SocialPostResult(
                success=True,
                platform="instagram",
                post_id=media_id,
                post_url=f"https://www.instagram.com/p/{media_id}/",
                posted_at=datetime.utcnow(),
                raw_response=publish_response
            )
            
        except SocialPlatformError:
            raise
        except CredentialResolutionError as e:
            logger.error(f"Failed to resolve Instagram credentials: {e}", exc_info=True)
            raise SocialPlatformError(
                message=f"Credential resolution failed: {str(e)}",
                platform="instagram",
                error_code="CREDENTIAL_RESOLUTION_FAILED",
                is_transient=False
            )
        except Exception as e:
            logger.error(f"Instagram post_feed failed: {e}", exc_info=True)
            raise SocialPlatformError(
                message=f"Failed to post to Instagram: {str(e)}",
                platform="instagram",
                error_code="POST_FAILED",
                is_transient=True
            )
    
    async def post_story(
        self,
        credential_ref: str,
        image_url: str,
    ) -> SocialPostResult:
        """Create Instagram Story (24hr expiry).
        
        Args:
            credential_ref: Reference to OAuth2 credentials
            image_url: Image URL (publicly accessible, vertical 9:16)
            
        Returns:
            SocialPostResult with story details
        """
        try:
            # Resolve credentials
            credentials = await self._get_credentials(credential_ref)
            access_token = credentials.access_token
            
            ig_account_id = credentials.posting_identity
            if ig_account_id and ig_account_id.startswith("IG:"):
                ig_account_id = ig_account_id[3:]
            
            if not ig_account_id:
                raise SocialPlatformError(
                    message="Instagram Business Account ID not found",
                    platform="instagram",
                    error_code="MISSING_ACCOUNT_ID",
                    is_transient=False
                )
            
            # Step 1: Create story container
            container_data = {
                "image_url": image_url,
                "media_type": "STORIES",
            }
            
            container_response = await self._make_api_call_with_retry(
                endpoint=f"/{ig_account_id}/media",
                method="POST",
                access_token=access_token,
                params=container_data,
                credential_ref=credential_ref,
            )
            
            container_id = container_response.get("id")
            if not container_id:
                raise SocialPlatformError(
                    message="Failed to create story container",
                    platform="instagram",
                    error_code="STORY_CONTAINER_FAILED",
                    is_transient=True
                )
            
            # Step 2: Publish story
            publish_response = await self._make_api_call_with_retry(
                endpoint=f"/{ig_account_id}/media_publish",
                method="POST",
                access_token=access_token,
                params={"creation_id": container_id},
                credential_ref=credential_ref,
            )
            
            story_id = publish_response.get("id")
            
            # Track API calls
            self.calls_made += 2
            
            return SocialPostResult(
                success=True,
                platform="instagram",
                post_id=story_id,
                post_url=f"https://www.instagram.com/stories/{ig_account_id}/{story_id}/",
                posted_at=datetime.utcnow(),
                raw_response=publish_response
            )
            
        except SocialPlatformError:
            raise
        except Exception as e:
            logger.error(f"Instagram post_story failed: {e}", exc_info=True)
            raise SocialPlatformError(
                message=f"Failed to post Instagram story: {str(e)}",
                platform="instagram",
                error_code="STORY_POST_FAILED",
                is_transient=True
            )
    
    async def post_reel(
        self,
        credential_ref: str,
        video_url: str,
        caption: Optional[str] = None,
        share_to_feed: bool = True,
    ) -> SocialPostResult:
        """Create Instagram Reel (short-form video).
        
        Args:
            credential_ref: Reference to OAuth2 credentials
            video_url: Video URL (publicly accessible, vertical 9:16)
            caption: Optional caption
            share_to_feed: Whether to share to main feed
            
        Returns:
            SocialPostResult with reel details
        """
        try:
            # Resolve credentials
            credentials = await self._get_credentials(credential_ref)
            access_token = credentials.access_token
            
            ig_account_id = credentials.posting_identity
            if ig_account_id and ig_account_id.startswith("IG:"):
                ig_account_id = ig_account_id[3:]
            
            if not ig_account_id:
                raise SocialPlatformError(
                    message="Instagram Business Account ID not found",
                    platform="instagram",
                    error_code="MISSING_ACCOUNT_ID",
                    is_transient=False
                )
            
            # Step 1: Create reel container
            container_data = {
                "video_url": video_url,
                "media_type": "REELS",
                "share_to_feed": str(share_to_feed).lower(),
            }
            if caption:
                container_data["caption"] = caption
            
            container_response = await self._make_api_call_with_retry(
                endpoint=f"/{ig_account_id}/media",
                method="POST",
                access_token=access_token,
                params=container_data,
                credential_ref=credential_ref,
            )
            
            container_id = container_response.get("id")
            if not container_id:
                raise SocialPlatformError(
                    message="Failed to create reel container",
                    platform="instagram",
                    error_code="REEL_CONTAINER_FAILED",
                    is_transient=True
                )
            
            # Step 2: Publish reel (may take time for video processing)
            publish_response = await self._make_api_call_with_retry(
                endpoint=f"/{ig_account_id}/media_publish",
                method="POST",
                access_token=access_token,
                params={"creation_id": container_id},
                credential_ref=credential_ref,
            )
            
            reel_id = publish_response.get("id")
            
            # Track API calls
            self.calls_made += 2
            
            return SocialPostResult(
                success=True,
                platform="instagram",
                post_id=reel_id,
                post_url=f"https://www.instagram.com/reel/{reel_id}/",
                posted_at=datetime.utcnow(),
                raw_response=publish_response
            )
            
        except SocialPlatformError:
            raise
        except Exception as e:
            logger.error(f"Instagram post_reel failed: {e}", exc_info=True)
            raise SocialPlatformError(
                message=f"Failed to post Instagram reel: {str(e)}",
                platform="instagram",
                error_code="REEL_POST_FAILED",
                is_transient=True
            )
    
    async def refresh_token(self, credential_ref: str) -> str:
        """Refresh Facebook/Instagram long-lived access token.
        
        Args:
            credential_ref: Reference to stored credentials
            
        Returns:
            New access token
        """
        try:
            # Get current access token
            credentials = await self._get_credentials(credential_ref)
            current_token = credentials.access_token
            
            # Facebook Graph API token refresh
            # Long-lived tokens can be refreshed to extend lifetime
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": os.getenv("FACEBOOK_APP_ID", ""),
                "client_secret": os.getenv("FACEBOOK_APP_SECRET", ""),
                "fb_exchange_token": current_token,
            }
            
            result = await self._make_api_call_with_retry(
                endpoint="/oauth/access_token",
                method="GET",
                access_token=current_token,  # Still use current token for auth
                params=params,
                credential_ref=None,  # Don't auto-refresh during refresh
            )
            
            new_access_token = result.get("access_token", "")
            if not new_access_token:
                raise SocialPlatformError(
                    message="Instagram/Facebook returned empty access_token",
                    platform="instagram",
                    error_code="TOKEN_REFRESH_FAILED",
                    is_transient=False
                )
            
            # Update token in CP Backend
            await self._update_access_token(credential_ref, new_access_token)
            
            logger.info(f"Instagram token refreshed for credential_ref={credential_ref}")
            return new_access_token
            
        except SocialPlatformError:
            raise
        except Exception as e:
            logger.error(f"Instagram token refresh failed: {e}", exc_info=True)
            raise SocialPlatformError(
                message=f"Failed to refresh Instagram token: {str(e)}",
                platform="instagram",
                error_code="TOKEN_REFRESH_FAILED",
                is_transient=False
            )
    
    async def validate_credentials(self, credential_ref: str) -> bool:
        """Validate Instagram credentials and check account.
        
        Args:
            credential_ref: Reference to stored credentials
            
        Returns:
            True if credentials are valid
        """
        try:
            credentials = await self._get_credentials(credential_ref)
            access_token = credentials.access_token
            
            ig_account_id = credentials.posting_identity
            if ig_account_id and ig_account_id.startswith("IG:"):
                ig_account_id = ig_account_id[3:]
            
            if not ig_account_id:
                raise SocialPlatformError(
                    message="Instagram Business Account ID not found",
                    platform="instagram",
                    error_code="MISSING_ACCOUNT_ID",
                    is_transient=False
                )
            
            # Check if token is valid by fetching account info
            result = await self._make_api_call_with_retry(
                endpoint=f"/{ig_account_id}",
                method="GET",
                access_token=access_token,
                params={"fields": "id,username"},
                credential_ref=credential_ref,
            )
            
            if not result.get("id"):
                raise SocialPlatformError(
                    "No Instagram account found for credentials",
                    platform="instagram",
                    error_code="NO_ACCOUNT",
                    is_transient=False
                )
            
            logger.info(f"Instagram credentials validated for credential_ref={credential_ref}")
            return True
            
        except SocialPlatformError:
            raise
        except Exception as e:
            logger.error(f"Instagram credential validation failed: {e}", exc_info=True)
            raise SocialPlatformError(
                message=f"Failed to validate Instagram credentials: {str(e)}",
                platform="instagram",
                error_code="VALIDATION_FAILED",
                is_transient=True
            )
    
    def _classify_error(self, status_code: int, error_body: dict) -> SocialPlatformError:
        """Classify Instagram/Facebook Graph API error.
        
        Args:
            status_code: HTTP status code
            error_body: Error response body
            
        Returns:
            SocialPlatformError with appropriate classification
        """
        error_obj = error_body.get("error", {})
        error_message = error_obj.get("message", "Unknown error")
        error_type = error_obj.get("type", "unknown")
        error_code = error_obj.get("code", 0)
        error_subcode = error_obj.get("error_subcode", 0)
        
        # Rate limit (transient)
        if error_code == 4 or error_code == 17 or error_code == 32 or error_code == 613:
            return SocialPlatformError(
                message=f"Instagram rate limit exceeded: {error_message}",
                platform="instagram",
                error_code="RATE_LIMIT",
                is_transient=True,
                retry_after=3600  # 1 hour
            )
        
        # Unauthorized (permanent - need new token)
        if status_code == 401 or error_code == 190:
            return SocialPlatformError(
                message=f"Instagram authentication failed: {error_message}",
                platform="instagram",
                error_code="AUTH_FAILED",
                is_transient=False
            )
        
        # Permission denied (permanent)
        if error_code == 200 or error_code == 10:
            return SocialPlatformError(
                message=f"Instagram permission denied: {error_message}",
                platform="instagram",
                error_code="PERMISSION_DENIED",
                is_transient=False
            )
        
        # Server error (transient)
        if status_code >= 500 or error_code == 1 or error_code == 2:
            return SocialPlatformError(
                message=f"Instagram server error: {error_message}",
                platform="instagram",
                error_code="SERVER_ERROR",
                is_transient=True
            )
        
        # Media upload errors (check if transient based on subcode)
        if error_code == 9004 or error_code == 100:
            # Some media errors are transient (processing issues)
            is_transient = error_subcode in (2207013, 2207043, 2207051)
            return SocialPlatformError(
                message=f"Instagram media error: {error_message}",
                platform="instagram",
                error_code="MEDIA_ERROR",
                is_transient=is_transient
            )
        
        # Client error (permanent)
        return SocialPlatformError(
            message=error_message,
            platform="instagram",
            error_code=f"ERROR_{error_code}",
            is_transient=False
        )
    
    # Helper methods
    
    async def _get_credentials(self, credential_ref: str):
        """Retrieve credentials from CP Backend via credential resolver."""
        if not self._customer_id:
            raise SocialPlatformError(
                message="customer_id not set on InstagramClient instance",
                platform="instagram",
                error_code="MISSING_CUSTOMER_ID",
                is_transient=False
            )
        
        credentials = await self._resolver.resolve(
            customer_id=self._customer_id,
            credential_ref=credential_ref,
        )
        
        if not credentials.access_token:
            raise SocialPlatformError(
                message="No access_token in resolved credentials",
                platform="instagram",
                error_code="MISSING_ACCESS_TOKEN",
                is_transient=False
            )
        
        return credentials
    
    async def _update_access_token(self, credential_ref: str, access_token: str) -> None:
        """Update access token in CP Backend after token refresh."""
        if not self._customer_id:
            raise SocialPlatformError(
                message="customer_id not set on InstagramClient instance",
                platform="instagram",
                error_code="MISSING_CUSTOMER_ID",
                is_transient=False
            )
        
        await self._resolver.update_access_token(
            customer_id=self._customer_id,
            credential_ref=credential_ref,
            new_access_token=access_token,
        )
    
    @retry(
        retry=retry_if_exception_type(_TransientInstagramError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _make_api_call_with_retry(
        self,
        endpoint: str,
        method: str,
        access_token: str,
        params: Optional[Dict[str, str]] = None,
        credential_ref: Optional[str] = None,
    ) -> dict:
        """Make API call with automatic retry on transient errors."""
        return await self._make_api_call(
            endpoint=endpoint,
            method=method,
            access_token=access_token,
            params=params,
            credential_ref=credential_ref,
        )
    
    async def _make_api_call(
        self,
        endpoint: str,
        method: str,
        access_token: str,
        params: Optional[Dict[str, str]] = None,
        credential_ref: Optional[str] = None,
    ) -> dict:
        """Make authenticated API call to Instagram/Facebook Graph API.
        
        Args:
            endpoint: API endpoint (e.g., "/{ig_account_id}/media")
            method: HTTP method (GET, POST)
            access_token: OAuth2 access token
            params: Query/form parameters
            credential_ref: Credential ref for auto-refresh on 401
            
        Returns:
            Response JSON
            
        Raises:
            SocialPlatformError: On API error
            _TransientInstagramError: On transient error (triggers retry)
        """
        url = f"{self.api_base_url}{endpoint}"
        
        # Add access_token to params
        params = params or {}
        params["access_token"] = access_token
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for media
                if method.upper() == "GET":
                    resp = await client.get(url, params=params)
                elif method.upper() == "POST":
                    resp = await client.post(url, data=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Success
            if resp.status_code in (200, 201):
                return resp.json()
            
            # Handle errors
            try:
                error_body = resp.json()
            except Exception:
                error_body = {"error": {"message": resp.text}}
            
            error = self._classify_error(resp.status_code, error_body)
            
            # Auto-refresh token on 401/190 if refresh available
            if (resp.status_code == 401 or error_body.get("error", {}).get("code") == 190) and credential_ref:
                logger.warning("Instagram token expired, attempting refresh...")
                try:
                    new_token = await self.refresh_token(credential_ref)
                    # Retry once with new token
                    params["access_token"] = new_token
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        if method.upper() == "GET":
                            resp = await client.get(url, params=params)
                        else:
                            resp = await client.post(url, data=params)
                    
                    if resp.status_code in (200, 201):
                        logger.info("Instagram API call succeeded after token refresh")
                        return resp.json()
                except Exception as refresh_error:
                    logger.error(f"Token refresh failed: {refresh_error}")
            
            # Raise transient error to trigger retry
            if error.is_transient:
                raise _TransientInstagramError(error.message)
            
            # Permanent error - don't retry
            raise error
            
        except _TransientInstagramError:
            raise  # Let tenacity handle retry
        except SocialPlatformError:
            raise
        except Exception as e:
            logger.error(f"Instagram API call failed: {e}", exc_info=True)
            # Treat unknown errors as transient
            raise _TransientInstagramError(f"API call failed: {str(e)}")
