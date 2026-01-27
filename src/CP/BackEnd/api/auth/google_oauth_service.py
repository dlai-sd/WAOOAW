"""
Google OAuth service
Handles OAuth flow and user info retrieval
"""

from typing import Any, Dict
import httpx
from fastapi import HTTPException, status
from core.config import settings

class GoogleOAuthService:
    """Service for Google OAuth operations"""

    @staticmethod
    def get_authorization_url(redirect_uri: str, state: str) -> str:
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
        verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        async with httpx.AsyncClient() as client:
            response = await client.get(verify_url)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token"
                )
            token_info = response.json()
            if token_info.get("aud") != settings.GOOGLE_CLIENT_ID:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token not issued for this application",
                )
            return token_info
