# items.py
from fastapi import APIRouter

# Create the API router for "items"
router = APIRouter()

@router.get("/{sessionId}")
def read_item(sessionId: str):
    # Return an object with a messages property containing the array
    return {
      "messages": [
        {"role": "assistant", "content": "Hello! How can I help you today?", "sources": [], "loading": False},
        {"role": "user", "content": "I need help with my bill", "sources": [], "loading": False},
        {"role": "assistant", "content": "Sure, I can help you with that. Can you please provide me with your account number?", "sources": [], "loading": False},
        {"role": "user", "content": "123456789", "sources": [], "loading": False},
        {"role": "assistant", "content": "Thank you. Can you please provide me with your full name?", "sources": [], "loading": False},
        {"role": "user", "content": "John Doe", "sources": [], "loading": False},
        {"role": "assistant", "content": "Thank you. Can you please provide me with your email address?", "sources": [], "loading": False},
        {"role": "user", "content": "john.doe@example.com", "sources": [], "loading": False}
      ]
    }
