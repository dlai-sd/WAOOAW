from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from .security import create_access_token, get_current_user, verify_password
from .middleware.auth import add_request_validation
from .config import settings
from datetime import timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")

class User(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

@router.post("/v1/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Here you would typically fetch the user from the database
    if form_data.username == "test@example.com" and form_data.password == "password":
        access_token = create_access_token(data={"user_id": "123", "tenant_id": "456"}, expires_delta=timedelta(hours=1))
        return {"access_token": access_token, "token_type": "bearer", "expires_in": 3600}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

@router.get("/auth/examples")
async def auth_examples():
    """Authentication examples in multiple languages"""
    return {
        "python": "import requests\nresponse = requests.post('http://localhost:8015/api/v1/token', data={'username': 'test@example.com', 'password': 'password'})",
        "javascript": "fetch('http://localhost:8015/api/v1/token', { method: 'POST', body: new URLSearchParams({ username: 'test@example.com', password: 'password' }), headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })",
        "java": "HttpPost post = new HttpPost('http://localhost:8015/api/v1/token');\npost.setEntity(new StringEntity(\"username=test@example.com&password=password\", ContentType.APPLICATION_FORM_URLENCODED));"
    }

add_request_validation(router)
