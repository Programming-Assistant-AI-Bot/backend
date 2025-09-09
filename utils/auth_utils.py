from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from utils.jwt_handler import verify_token
from database.db import user_collection
from bson import ObjectId

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user information from token
    user_id = payload.get("user_id")
    username = payload.get("username")
    email = payload.get("email")
    
    if not user_id or not username or not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Return user data from token
    return {
        "id": user_id,
        "username": username,
        "email": email
    }