"""Auth placeholder routes for Platform Portal."""

from fastapi import APIRouter, Depends, HTTPException, status
from api.auth.google_oauth_service import GoogleOAuthService  # Import the service
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.config import settings, get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


class UserProfile(BaseModel):
    id: str
    email: str
    name: str | None = None
    provider: str = "google"
    environment: str


@router.get("/me", response_model=UserProfile)
async def me(app_settings: settings.__class__ = Depends(get_settings)) -> UserProfile:
    """Return a mock user profile; replace with real auth once backend is wired."""
    if not app_settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured: set GOOGLE_CLIENT_ID",
        )

    return UserProfile(
        id="demo-user",
        email="demo@waooaw.com",
        name="Demo User",
        provider="google",
        environment=app_settings.ENVIRONMENT,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> None:
    """Placeholder logout endpoint."""
    return None
