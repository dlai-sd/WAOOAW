from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from core.config import settings
from api.auth.google_oauth import get_user_from_google, verify_google_token
from api.auth.user_store import UserStore
from models.user import UserCreate, Token

async def handle_google_callback(code: str, state: str, user_store: UserStore):
    # Verify code exists
    if not code:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?error=no_code", status_code=302
        )

    try:
        # Exchange code for user info
        user_info = await get_user_from_google(code, settings.OAUTH_REDIRECT_URI)

        # Create or get user
        user_data = UserCreate(
            email=user_info["email"],
            name=user_info.get("name"),
            picture=user_info.get("picture"),
            provider="google",
            provider_id=user_info["id"],
        )

        user = user_store.get_or_create_user(user_data)

        return user

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to handle Google callback: {str(e)}",
        )
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from core.config import settings
from api.auth.google_oauth import get_user_from_google, verify_google_token
from api.auth.user_store import UserStore
from models.user import UserCreate, Token

async def handle_google_callback(code: str, state: str, user_store: UserStore):
    # Verify code exists
    if not code:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?error=no_code", status_code=302
        )

    try:
        # Exchange code for user info
        user_info = await get_user_from_google(code, settings.OAUTH_REDIRECT_URI)

        # Create or get user
        user_data = UserCreate(
            email=user_info["email"],
            name=user_info.get("name"),
            picture=user_info.get("picture"),
            provider="google",
            provider_id=user_info["id"],
        )

        user = user_store.get_or_create_user(user_data)

        return user

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to handle Google callback: {str(e)}",
        )
