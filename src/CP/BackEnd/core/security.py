from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .config import Settings
import logging
import asyncio

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = Settings()
logger = logging.getLogger(__name__)

async def retry_with_exponential_backoff(operation, retries: int = 3):
    for attempt in range(retries):
        try:
            return await operation()
        except Exception as e:
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Retrying in {wait_time} seconds due to error: {str(e)}")
                await asyncio.sleep(wait_time)
            else:
                raise HTTPException(status_code=503, detail="Service unavailable. Please try again later.")

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def log_request_correlation_id(correlation_id: str):
    logger.info(f"Request correlation ID: {correlation_id}")
