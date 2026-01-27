"""
JWT token handling utilities
Create, validate, and decode JWT tokens for authentication
"""

from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError

from core.config import settings
from models.user import TokenData


# Remove the duplicate JWTHandler class
