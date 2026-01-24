from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from .security import create_access_token, verify_password, get_current_user
from .models.user import UserCreate, UserDB
from .database import get_user_by_email
from core.error_handling import raise_http_exception
from core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter, Limiter
from prometheus_client import generate_latest, CollectorRegistry

router = APIRouter()
limiter = Limiter(key_func=lambda: "tenant_id")
registry = CollectorRegistry()

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

@router.post("/v1/token", response_model=Token)
@limiter.limit("100/minute")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise_http_exception(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email, "user_id": str(user.id), "tenant_id": user.tenant_id})
    return {"access_token": access_token, "token_type": "bearer", "expires_in": settings.access_token_expire_seconds}

@router.get("/v1/me", response_model=UserDB)
async def read_users_me(current_user: UserDB = Depends(get_current_user)):
    return current_user

@router.get("/v2/me", response_model=UserDB)
async def read_users_me_v2(current_user: UserDB = Depends(get_current_user)):
    return current_user

@router.get("/metrics")
async def metrics():
    return generate_latest(registry)
