from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError

from core.config import settings
from core.jwt_utils import JWTHandler
from models.user import TokenData


# Remove the duplicate JWTHandler class


# Convenience functions
def create_tokens(user_id: str, email: str) -> Dict[str, Any]:
    """Create access and refresh token pair"""
    return JWTHandler.create_token_pair(user_id, email)


def verify_token(token: str) -> TokenData:
    """Verify and decode a token"""
    return JWTHandler.decode_token(token)
