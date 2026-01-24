from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel  # Importing BaseModel from pydantic
from .database import get_db
from .models.user import User
from .security import create_access_token, verify_password
from .schemas import Token
from fastapi_limiter import Limiter

router = APIRouter()
limiter = Limiter(key='global', default_limits=["100/minute"])

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

@router.post("/token", response_model=Token)
@limiter.limit("100/minute")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "tenant_id": user.tenant_id, "user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer", "expires_in": 3600}
