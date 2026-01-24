from fastapi import APIRouter
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from core.config import settings

router = APIRouter()

@router.get("/api/docs", include_in_schema=False)
async def swagger_ui():
    return get_swagger_ui_html(openapi_url="/openapi.json", title=settings.OPENAPI_TITLE)

@router.get("/openapi.json", include_in_schema=False)
async def openapi():
    return get_openapi(
        title=settings.OPENAPI_TITLE,
        version=settings.OPENAPI_VERSION,
        routes=router.routes,
    )
