# routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException
from schemas.user_schema import UserSignup, UserLogin, TokenResponse, UserResponse
from services.auth.auth_service import signup_user, login_user
from utils.auth_utils import get_current_user

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
def register(user: UserSignup):
    return signup_user(user)

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin):
    return login_user(user)

@router.get("/validate-token")
async def validate_token(current_user: dict = Depends(get_current_user)):
    # The get_current_user dependency already validates the token
    # Just return the user data
    return current_user