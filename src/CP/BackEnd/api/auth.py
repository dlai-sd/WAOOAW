from fastapi import APIRouter, Depends
from pydantic import BaseModel
from .security import get_current_user
from .middleware.auth import add_request_validation

router = APIRouter()

class User(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register(user: User):
    # Registration logic here
    pass

@router.post("/login")
async def login(user: User):
    # Login logic here
    pass

add_request_validation(router)

