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

@router.get("/auth/examples")
async def auth_examples():
    """Authentication examples in multiple languages"""
    return {
        "python": "import requests\nresponse = requests.post('http://localhost:8015/api/token', json={'email': 'test@example.com', 'password': 'password'})",
        "javascript": "fetch('http://localhost:8015/api/token', { method: 'POST', body: JSON.stringify({ email: 'test@example.com', password: 'password' }), headers: { 'Content-Type': 'application/json' } })",
        "java": "HttpPost post = new HttpPost('http://localhost:8015/api/token');\npost.setEntity(new StringEntity(\"{\\\"email\\\":\\\"test@example.com\\\",\\\"password\\\":\\\"password\\\"}\", ContentType.APPLICATION_JSON));"
    }

add_request_validation(router)
