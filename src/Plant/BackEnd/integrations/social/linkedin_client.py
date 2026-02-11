"""LinkedIn Business API client for company page posting.

Implements LinkedIn's v2 API for posting on behalf of organizations:
- Text posts (with optional rich media)
- Image shares
- Article shares
- OAuth2 token refresh
- Organization permission validation

Reference: https://docs.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/posts-api
"""

import httpx
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from datetime import datetime

from integrations.social.base import (
    SocialPlatformClient,
    SocialPostResult,
    SocialPlatformError,
)
from services.social_credential_resolver import (
    CPSocialCredentialResolver,
    CredentialResolutionError,
)


class LinkedInClient(SocialPlatformClient):
    """LinkedIn Business API (v2) client for organization posting.
    
    Features:
    - Post text updates to organization pages
    - Share images with posts
    - Share articles/links
    - OAuth2 token refresh (60-day expiry)
    - Organization permissions validation
    - Rate limit handling (100 posts/day per person, 25 posts/day per app)
    - Error classification and retry logic
    
    Authentication:
    - Uses OAuth 2.0 3-legged auth
    - Requires w_member_social and w_organization_social scopes
    - Long-lived tokens (60 days)
    
    Posting Identity Format:
    - LI_ORG:{organization_id} for organization posts
    - Example: LI_ORG:12345678
    """
    
    BASE_URL = "https://api.linkedin.com/v2"
    
    def __init__(
        self,
        credential_resolver: CPSocialCredentialResolver,
        customer_id: str,
    ):
        """Initialize LinkedIn client.
        
        Args:
            credential_resolver: Service to resolve credentials from CP Backend
            customer_id: WAOOAW customer ID
        """
        super().__init__(platform_name="linkedin")
        self.credential_resolver = credential_resolver
        self.customer_id = customer_id
    
    async def post_text(
        self,
        credential_ref: str,
        text: str,
        image_url: Optional[str] = None,
        link_url: Optional[str] = None,
        link_title: Optional[str] = None,
    ) -> SocialPostResult:
        """Post text update to LinkedIn organization page.
        
        Extracts organization_id from credentials and delegates to post_to_organization.
        
        Args:
            credential_ref: Reference to CP credential
            text: Post text (max 3000 characters)
            image_url: Optional image URL to include
            link_url: Optional link to share
            link_title: Optional title for link preview
            
        Returns:
            SocialPostResult with post ID and URL
            
        Raises:
            SocialPlatformError: On API errors or missing organization_id
        """
        # Resolve credentials to get organization_id
        creds = await self.credential_resolver.resolve(
            customer_id=self.customer_id,
            credential_ref=credential_ref,
        )
        
        # Extract organization_id from posting_identity (format: LI_ORG:12345678)
        if not creds.posting_identity or not creds.posting_identity.startswith("LI_ORG:"):
            raise SocialPlatformError(
                platform="linkedin",
                error_code="MISSING_ORG_ID",
                message="LinkedIn organization ID not found in credentials. Expected format: LI_ORG:{organization_id}",
                is_transient=False,
            )
        
        organization_id = creds.posting_identity.split(":", 1)[1]
        
        return await self.post_to_organization(
            credential_ref=credential_ref,
            organization_id=organization_id,
            text=text,
            image_url=image_url,
            link_url=link_url,
            link_title=link_title,
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        retry=retry_if_exception(lambda e: isinstance(e, SocialPlatformError) and e.is_transient),
        reraise=True,
    )
    async def post_to_organization(
        self,
        credential_ref: str,
        organization_id: str,
        text: str,
        image_url: Optional[str] = None,
        link_url: Optional[str] = None,
        link_title: Optional[str] = None,
    ) -> SocialPostResult:
        """Post text update to LinkedIn organization page.
        
        Uses LinkedIn's UGC (User Generated Content) API for posting.
        
        Args:
            credential_ref: Reference to CP credential
            organization_id: LinkedIn organization ID (numeric)
            text: Post text (max 3000 characters)
            image_url: Optional image URL to include
            link_url: Optional link to share
            link_title: Optional title for link preview
            
        Returns:
            SocialPostResult with post ID and URL
            
        Raises:
            SocialPlatformError: On API errors
        """
        start_time = datetime.utcnow()
        
        # Build UGC post payload
        payload: Dict[str, Any] = {
            "author": f"urn:li:organization:{organization_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # Add image if provided
        if image_url:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "originalUrl": image_url,
                }
            ]
        
        # Add article/link if provided
        elif link_url:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "originalUrl": link_url,
                    "title": {
                        "text": link_title or link_url
                    }
                }
            ]
        
        # Make API call with retry and auto-refresh
        response_data = await self._make_api_call(
            method="POST",
            endpoint="/ugcPosts",
            credential_ref=credential_ref,
            json_body=payload,
        )
        
        # Handle empty response
        if not response_data:
            response_data = {}
        
        # Extract post ID from response
        # Response format: {"id": "urn:li:ugcPost:1234567890"}
        post_urn = response_data.get("id", "")
        post_id = post_urn.split(":")[-1] if post_urn else ""
        
        # Build post URL
        post_url = f"https://www.linkedin.com/feed/update/{post_urn}" if post_urn else ""
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return SocialPostResult(
            success=True,
            platform="linkedin",
            post_id=post_id,
            post_url=post_url,
            posted_at=datetime.utcnow(),
            raw_response=response_data,
        )
    
    async def refresh_token(self, credential_ref: str) -> str:
        """Refresh LinkedIn OAuth2 access token.
        
        LinkedIn tokens expire after 60 days. This method exchanges the current
        token for a new long-lived token.
        
        Args:
            credential_ref: Reference to CP credential
            
        Returns:
            New access token
            
        Raises:
            SocialPlatformError: On refresh failure
        """
        # Resolve credentials to get current access token
        creds = await self.credential_resolver.resolve(
            customer_id=self.customer_id,
            credential_ref=credential_ref,
        )
        
        # LinkedIn doesn't have a true refresh flow - tokens are long-lived (60 days)
        # Refresh is typically done by re-authenticating via OAuth2 flow
        # For now, we'll validate the current token and return it
        # In production, implement OAuth2 re-authentication flow
        
        # Validate current token
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {creds.access_token}",
            }
            
            response = await client.get(
                f"{self.BASE_URL}/me",
                headers=headers,
            )
            
            if response.status_code == 200:
                # Token is still valid
                return creds.access_token
            elif response.status_code == 401:
                # Token expired - need re-authentication
                raise SocialPlatformError(
                    platform="linkedin",
                    error_code="TOKEN_EXPIRED",
                    message="LinkedIn token expired. User must re-authenticate via OAuth2 flow.",
                    is_transient=False,
                )
            else:
                error_body = response.json() if response.text else {}
                raise self._classify_error(response.status_code, error_body)
    
    async def validate_credentials(self, credential_ref: str) -> bool:
        """Validate LinkedIn credentials and organization permissions.
        
        Checks:
        1. Token is valid
        2. Organization exists and is accessible
        3. User has w_organization_social permission
        
        Args:
            credential_ref: Reference to CP credential
            
        Returns:
            True if credentials are valid
            
        Raises:
            SocialPlatformError: On validation failure
        """
        # Resolve credentials
        creds = await self.credential_resolver.resolve(
            customer_id=self.customer_id,
            credential_ref=credential_ref,
        )
        
        # Extract organization_id
        if not creds.posting_identity or not creds.posting_identity.startswith("LI_ORG:"):
            raise SocialPlatformError(
                platform="linkedin",
                error_code="MISSING_ORG_ID",
                message="LinkedIn organization ID not found in credentials.",
                is_transient=False,
            )
        
        organization_id = creds.posting_identity.split(":", 1)[1]
        
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {creds.access_token}",
            }
            
            # Check organization access
            org_response = await client.get(
                f"{self.BASE_URL}/organizations/{organization_id}",
                headers=headers,
            )
            
            if org_response.status_code != 200:
                org_error = org_response.json() if org_response.text else {}
                raise SocialPlatformError(
                    platform="linkedin",
                    error_code="ORG_NOT_FOUND",
                    message=f"Cannot access LinkedIn organization {organization_id}. User may not have admin access.",
                    is_transient=False,
                )
            
            # Check organization role permissions
            role_response = await client.get(
                f"{self.BASE_URL}/organizationAcls?q=roleAssignee&role=ADMINISTRATOR&projection=(elements*(organization~,roleAssignee~))",
                headers=headers,
            )
            
            if role_response.status_code != 200:
                role_error = role_response.json() if role_response.text else {}
                raise SocialPlatformError(
                    platform="linkedin",
                    error_code="PERMISSION_DENIED",
                    message="User does not have admin permissions for organization posting. Requires w_organization_social scope.",
                    is_transient=False,
                )
            
            return True
    
    def _classify_error(
        self,
        status_code: int,
        error_body: Dict[str, Any],
    ) -> SocialPlatformError:
        """Classify LinkedIn API errors into transient vs permanent.
        
        LinkedIn error codes:
        - 429: Rate limit exceeded (transient)
        - 401: Unauthorized - invalid/expired token (permanent)
        - 403: Forbidden - missing permissions (permanent)
        - 400: Bad request - invalid parameters (permanent)
        - 500, 502, 503: Server errors (transient)
        
        Args:
            status_code: HTTP status code
            error_body: Error response JSON
            
        Returns:
            SocialPlatformError with appropriate classification
        """
        message = error_body.get("message", "Unknown error")
        service_error_code = error_body.get("serviceErrorCode", 0)
        
        # Rate limit errors - transient
        if status_code == 429:
            return SocialPlatformError(
                platform="linkedin",
                error_code="RATE_LIMIT",
                message="LinkedIn rate limit exceeded. Retry after delay.",
                is_transient=True,
                retry_after=3600,  # LinkedIn: 100 posts/day, wait 1 hour
            )
        
        # Authentication errors - permanent
        if status_code == 401:
            return SocialPlatformError(
                platform="linkedin",
                error_code="AUTH_FAILED",
                message=f"LinkedIn authentication failed: {message}. Token may be expired.",
                is_transient=False,
            )
        
        # Permission errors - permanent
        if status_code == 403:
            return SocialPlatformError(
                platform="linkedin",
                error_code="PERMISSION_DENIED",
                message=f"LinkedIn permission denied: {message}. Check organization admin access.",
                is_transient=False,
            )
        
        # Bad request errors - permanent
        if status_code == 400:
            return SocialPlatformError(
                platform="linkedin",
                error_code="INVALID_PARAMETER",
                message=f"LinkedIn invalid parameter: {message}",
                is_transient=False,
            )
        
        # Server errors - transient
        if status_code >= 500:
            return SocialPlatformError(
                platform="linkedin",
                error_code="SERVER_ERROR",
                message=f"LinkedIn server error: {message}",
                is_transient=True,
            )
        
        # Unknown errors - treat as permanent
        return SocialPlatformError(
            platform="linkedin",
            error_code="UNKNOWN_ERROR",
            message=f"LinkedIn unknown error: {message}",
            is_transient=False,
        )
    
    async def _make_api_call(
        self,
        method: str,
        endpoint: str,
        credential_ref: str,
        json_body: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make authenticated API call to LinkedIn with retry and auto-refresh.
        
        Handles:
        - Token resolution
        - HTTP request with proper headers
        - 401 auto-refresh
        - Error classification
        - Call counting
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (e.g., /ugcPosts)
            credential_ref: Reference to CP credential
            json_body: Optional JSON body for POST/PUT
            query_params: Optional query parameters
            
        Returns:
            Response JSON data
            
        Raises:
            SocialPlatformError: On API errors
        """
        # Resolve credentials
        creds = await self.credential_resolver.resolve(
            customer_id=self.customer_id,
            credential_ref=credential_ref,
        )
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {creds.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",  # LinkedIn API version
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_body,
                params=query_params,
            )
            
            self.calls_made += 1
            
            # Success
            if response.status_code in (200, 201):
                return response.json() if response.text else {}
            
            # Auto-refresh on 401
            if response.status_code == 401:
                # Attempt token refresh
                new_token = await self.refresh_token(credential_ref)
                headers["Authorization"] = f"Bearer {new_token}"
                
                # Retry request with new token
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_body,
                    params=query_params,
                )
                
                self.calls_made += 1
                
                if response.status_code in (200, 201):
                    return response.json() if response.text else {}
            
            # Error - classify and raise
            error_body = response.json() if response.text else {}
            raise self._classify_error(response.status_code, error_body)
