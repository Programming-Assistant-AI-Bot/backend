# schemas/user_schema.py
from pydantic import BaseModel, EmailStr

class UserSignup(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str  # Add user ID for direct reference
    username: str  # Include username for display purposes
    email: str  # Include email for user identification
