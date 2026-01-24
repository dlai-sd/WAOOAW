from fastapi import APIRouter, Request, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi import FastAPI
from pydantic import BaseModel, ValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
import logging

api_v1_router = APIRouter(prefix="/api/v1")

@api_v1_router.get("/api/docs", include_in_schema=False)
async def swagger_ui():
    return get_swagger_ui_html(openapi_url=api_v1_router.openapi_url, title="Swagger UI")

class RequestValidatorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Validate request against OpenAPI schema
        try:
            # Here you would implement your validation logic
            response = await call_next(request)
            return response
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())

# Add middleware to the FastAPI app
middleware = [
    Middleware(RequestValidatorMiddleware),
    Middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]),
]

app = FastAPI(middleware=middleware)

# Include your routes here
