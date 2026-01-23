"""
OAuth2 token endpoint for Plant API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from src.CP.BackEnd.core.security import create_access_token, verify_password
from src.CP.BackEnd.core.config import settings

router = APIRouter()

@router.post("/token", response_model=dict)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Here you would normally verify the user credentials
    # For demonstration, we will assume the user is valid
    user_id = form_data.username
    tenant_id = "example_tenant"  # This should be fetched based on the user

    access_token = create_access_token(data={"user_id": user_id, "tenant_id": tenant_id})
    return {"access_token": access_token, "token_type": "bearer"}
