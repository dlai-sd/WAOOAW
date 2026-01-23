"""
Authentication routes for the API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from .security import create_access_token, verify_token
from fastapi.security import OAuth2PasswordRequestForm
from .config import settings

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 token endpoint for user login.
    
    Args:
        form_data: OAuth2 form data containing username and password
        
    Returns:
        Token containing access token and token type
    """
    # Here you would validate the user credentials
    # For example, check against a database
    user_id = "example_user_id"  # Replace with actual user ID
    tenant_id = "example_tenant_id"  # Replace with actual tenant ID

    access_token = create_access_token(data={"sub": user_id, "tenant_id": tenant_id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me(token: str = Depends(verify_token)):
    """
    Get current user information.
    
    Args:
        token: JWT token for authentication
        
    Returns:
        User information
    """
    return token  # Return user information based on token claims
