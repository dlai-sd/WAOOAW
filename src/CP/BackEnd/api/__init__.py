"""API routes"""

from api.auth import router as auth_router
from api.auth_email import router as auth_email_router

__all__ = ["auth_router", "auth_email_router"]
