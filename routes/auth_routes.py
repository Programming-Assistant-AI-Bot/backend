# routes/auth_routes.py
from fastapi import APIRouter
from schemas.user_schema import UserSignup, UserLogin, TokenResponse, UserResponse
from services.auth.auth_service import signup_user, login_user

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
def register(user: UserSignup):
    return  signup_user(user)

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin):
    return  login_user(user)
