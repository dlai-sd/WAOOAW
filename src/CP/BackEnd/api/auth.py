from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from .security import create_access_token, get_current_user, verify_password
from .middleware.auth import add_request_validation
from .config import settings
from datetime import timedelta

router = APIRouter()

class User(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

@router.post("/token", response_model=TokenResponse)
async def login(user: User):
    # Here you would typically fetch the user from the database
    # For demonstration, we assume a user with email "test@example.com" and password "password"
    if user.email == "test@example.com" and user.password == "password":
        access_token = create_access_token(data={"user_id": "123", "tenant_id": "456"}, expires_delta=timedelta(hours=1))
        return {"access_token": access_token, "token_type": "bearer", "expires_in": 3600}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

add_request_validation(router)
