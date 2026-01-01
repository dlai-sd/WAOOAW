"""Auth Module - Export routers"""

from .oauth import router as oauth_router

__all__ = ["oauth_router"]
