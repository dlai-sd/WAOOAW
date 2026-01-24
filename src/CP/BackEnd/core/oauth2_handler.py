from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from jose import JWTError, jwt
from pydantic import BaseModel
from .security import create_access_token
from .database import get_db
from .models.user import User
from .models.user_db import User as UserDB
from .config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()

settings = get_settings()

class Token(BaseModel):
    access_token: str
    token_type: str

# OAuth2 token endpoint
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == form_data.username).first()
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
    
    # Create JWT token
    access_token_expires = timedelta(hours=1)
    access_token = create_access_token(data={"sub": user.username, "tenant_id": user.tenant_id}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt
