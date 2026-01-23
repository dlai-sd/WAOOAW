from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import timedelta
from .security import create_access_token
from ..models.user import UserLogin
from ..services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")
router = APIRouter()

@router.post("/api/v1/token")
async def login(user: UserLogin, auth_service: AuthService = Depends()):
    user_data = await auth_service.login_user(user)
    if not user_data:
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})
    
    access_token = create_access_token(data={"user_id": str(user_data.id), "tenant_id": user_data.tenant_id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600
    }
