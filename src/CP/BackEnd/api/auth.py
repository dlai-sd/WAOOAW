from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from .security import create_access_token, verify_password, get_current_user
from .models.user import UserCreate, UserDB
from .database import get_user_by_email

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/v1/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id, "tenant_id": user.tenant_id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/v1/me", response_model=UserDB)
async def read_users_me(current_user: UserDB = Depends(get_current_user)):
    return current_user
