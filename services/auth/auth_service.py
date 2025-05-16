# services/auth/auth_service.py
from passlib.context import CryptContext
from fastapi import HTTPException, status
from database.mongodb import user_collection
from models.user_model import user_helper
from utils.jwt_handler import create_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def signup_user(data):
    if  user_collection.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = pwd_context.hash(data.password)
    user_data = {
        "username": data.username,
        "email": data.email,
        "password": hashed_pwd
    }
    new_user =  user_collection.insert_one(user_data)
    user =  user_collection.find_one({"_id": new_user.inserted_id})
    return user_helper(user)

def login_user(data):
    user =  user_collection.find_one({"email": data.email})
    if not user or not pwd_context.verify(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"user_id": str(user["_id"])})
    return {"access_token": token}
