from fastapi import APIRouter
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi import FastAPI

api_v1_router = APIRouter(prefix="/api/v1")

@api_v1_router.get("/api/docs", include_in_schema=False)
async def swagger_ui():
    return get_swagger_ui_html(openapi_url=api_v1_router.openapi_url, title="Swagger UI")

# Include your routes here
