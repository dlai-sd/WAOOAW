"""
Google OAuth integration
Handles OAuth flow and user info retrieval
"""

from typing import Any, Dict

import httpx
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, status

from core.config import settings

# Initialize OAuth
oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        "prompt": "select_account",  # Force account selection
    },
)


class GoogleOAuth:
    """Handle Google OAuth operations"""

    @staticmethod
    def get_authorization_url(redirect_uri: str, state: str) -> str:
        """
        Generate Google OAuth authorization URL

        Args:
            redirect_uri: Where Google should redirect after auth
            state: CSRF token for security

        Returns:
            Authorization URL to redirect user to
        """
        return (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={settings.GOOGLE_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope=openid%20email%20profile&"
            f"state={state}&"
            f"prompt=select_account&"
            f"access_type=offline"
        )

    @staticmethod
    async def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from Google
            redirect_uri: Must match the one used in authorization

        Returns:
            Token response from Google

        Raises:
            HTTPException: If token exchange fails
        """
        token_url = "https://oauth2.googleapis.com/token"

        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token",
                )

            return response.json()

    @staticmethod
    async def get_user_info(access_token: str) -> Dict[str, Any]:
        """
        Get user information from Google

        Args:
            access_token: Google access token

        Returns:
            User profile information

        Raises:
            HTTPException: If user info retrieval fails
        """
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"

        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(userinfo_url, headers=headers)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch user info",
                )

            return response.json()

    @staticmethod
    async def verify_id_token(id_token: str) -> Dict[str, Any]:
        """
        Verify Google ID token (for frontend Google Sign-In)

        Args:
            id_token: ID token from Google Sign-In

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid
        """
        verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"

        async with httpx.AsyncClient() as client:
            response = await client.get(verify_url)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token"
                )

            token_info = response.json()

            # Verify the token is for our client
            if token_info.get("aud") != settings.GOOGLE_CLIENT_ID:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token not issued for this application",
                )

            return token_info


# Convenience functions
async def get_user_from_google(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Complete OAuth flow: exchange code for token and get user info

    Args:
        code: Authorization code from Google
        redirect_uri: Redirect URI used in authorization

    Returns:
        User profile information from Google
    """
    # Exchange code for token
    token_response = await GoogleOAuth.exchange_code_for_token(code, redirect_uri)
    access_token = token_response.get("access_token")

    if not access_token or not isinstance(access_token, str):
        raise HTTPException(status_code=400, detail="Failed to obtain access token")

    # Get user info
    user_info = await GoogleOAuth.get_user_info(access_token)

    return user_info


async def verify_google_token(id_token: str) -> Dict[str, Any]:
    """Verify Google ID token from frontend"""
    return await GoogleOAuth.verify_id_token(id_token)

