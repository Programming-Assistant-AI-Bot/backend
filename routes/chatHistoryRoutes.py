# items.py
from fastapi import APIRouter, Depends, HTTPException
from services.chatHistory.chatMessageServices import getMessage
from utils.auth_utils import get_current_user
from database.db import session_collection


# Create the API router for "items"
router = APIRouter()

@router.get("/{sessionId}")
async def read_item(sessionId: str, current_user: dict = Depends(get_current_user)):
    # Verify session belongs to user first
    session = await session_collection.find_one({"sessionId": sessionId})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if user owns this session
    if str(session["userId"]) != current_user["id"]:
        raise HTTPException(status_code=403, detail="You don't have permission to access this session")
    
    # Get messages with user filtering
    messages = await getMessage(sessionId, current_user["id"])
    return messages