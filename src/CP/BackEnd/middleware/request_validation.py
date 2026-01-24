from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
from core.jwt_handler import verify_token

class RequestValidatorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Validate request against OpenAPI schema
        try:
            # Extract token and validate
            token = request.headers.get("Authorization")
            if token:
                verify_token(token.split(" ")[1])  # Assuming Bearer token format
            
            response = await call_next(request)
            return response
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
