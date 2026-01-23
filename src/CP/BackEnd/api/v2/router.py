"""
API version 2 router
"""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.CP.BackEnd.api.auth import authenticate_user

api_v2_router = APIRouter(prefix="/api/v2")

@api_v2_router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    return {"access_token": user['username'], "token_type": "bearer"}
