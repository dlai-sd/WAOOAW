from fastapi import Depends, HTTPException, status
from core.config import settings
import httpx

class GoogleOAuth:
    """Handles Google OAuth authentication."""

    @staticmethod
    async def get_user_info(token: str):
        """Fetch user info from Google using the provided token."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return response.json()
"""
Google OAuth functionality for Platform Portal.
"""

from fastapi import Depends, HTTPException, status
from core.config import settings
import httpx

class GoogleOAuth:
    """Handles Google OAuth authentication."""

    @staticmethod
    async def get_user_info(token: str):
        """Fetch user info from Google using the provided token."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return response.json()
"""
Google OAuth functionality for Platform Portal.
"""
"""
Google OAuth functionality for Platform Portal.
"""

from fastapi import Depends, HTTPException, status
from core.config import settings
import httpx

class GoogleOAuth:
    """Handles Google OAuth authentication."""

    @staticmethod
    async def get_user_info(token: str):
        """Fetch user info from Google using the provided token."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return response.json()
from fastapi import Depends, HTTPException, status
import httpx

class GoogleOAuth:
    """Handles Google OAuth authentication."""

    @staticmethod
    async def get_user_info(token: str):
        """Fetch user info from Google using the provided token."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return response.json()
