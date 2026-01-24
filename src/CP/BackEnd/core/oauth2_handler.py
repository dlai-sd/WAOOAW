from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .database import get_db
from .models.user import User
from .jwt_handler import JWTHandler

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class OAuth2Handler:
    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(self, username: str, password: str):
        user = self.db.query(User).filter(User.username == username).first()
        if not user or not user.verify_password(password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    def create_access_token(self, data: dict):
        return JWTHandler.create_access_token(data=data)
