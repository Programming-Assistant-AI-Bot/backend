# items.py
from fastapi import APIRouter
from services.chatHistory.chatMessageServices import getMessage

# Create the API router for "items"
router = APIRouter()

@router.get("/{sessionId}")
async def read_item(sessionId: str):
    # Return an object with a messages property containing the array
    messages = await getMessage(sessionId)
    return messages