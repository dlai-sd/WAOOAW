"""
User models for authentication
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user"""

    provider: str = "google"
    provider_id: str


class User(UserBase):
    """User schema with ID"""

    id: str
    provider: str
    provider_id: str
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserInDB(User):
    """User schema as stored in database"""

    pass


class TokenData(BaseModel):
    """JWT token payload data"""

    user_id: str
    email: str
    token_type: str  # "access" or "refresh"
    iat: int | None = None
    exp: int | None = None


class Token(BaseModel):
    """Token response schema"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class TokenRefresh(BaseModel):
    """Request schema for token refresh"""

    refresh_token: str


# Email/Password Auth Models (MVP addition)

class UserRegister(BaseModel):
    """Schema for email/password registration"""
    
    email: EmailStr
    password: str
    full_name: str
    
    model_config = {"json_schema_extra": {
        "example": {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe"
        }
    }}


class UserLogin(BaseModel):
    """Schema for email/password login"""
    
    email: EmailStr
    password: str
    
    model_config = {"json_schema_extra": {
        "example": {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }
    }}


class UserDB(BaseModel):
    """User as stored in database with hashed password"""
    
    id: str
    email: EmailStr
    hashed_password: str
    full_name: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
