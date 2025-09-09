from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from schemas.message import MessageRequest
from services.chatHistory.llm import make_conversational_chain
from models.chatMessages import Message
from datetime import datetime
import json
from database.db import message_collection, session_collection
from Controllers.Controller import addMessage, updateSessionName
from bson import ObjectId
from utils.gemini import generate_session_title
from schemas.sessionschema import getFirstMessageBySessionId
from utils.auth_utils import get_current_user  # Add this import

router = APIRouter(prefix="/chat", tags=["chat"])

async def getSessionObjToId(object_id: str, user_id: str):
    """Get session ID if it belongs to the specified user"""
    try:
        obj_id = ObjectId(object_id)  # Validate and convert to ObjectId
        session_data = await session_collection.find_one({
            "_id": obj_id,
            "userId": user_id  # Filter by user ID for ownership
        })
        
        if not session_data:
            return None
        
        return session_data.get("sessionId")
    except Exception as e:
        raise ValueError(f"Error retrieving session: {str(e)}")

@router.post("/{sessionId}")
async def simple_stream_chat_response(
    sessionId: str, 
    request: MessageRequest,
    current_user: dict = Depends(get_current_user)  # Add user authentication
):
    # Verify session ownership
    session = await session_collection.find_one({
        "sessionId": sessionId,
        "userId": current_user["id"]  # Check if session belongs to current user
    })
    
    if not session:
        # Try to handle ObjectId format
        try:
            actual_session_id = await getSessionObjToId(sessionId, current_user["id"])
            if not actual_session_id:
                raise HTTPException(status_code=403, detail="Access denied to this session")
            sessionId = actual_session_id
        except:
            raise HTTPException(status_code=403, detail="Access denied to this session")
    
    async def event_generator():
        try:
            # Pass both session_id and user_id
            chain = make_conversational_chain(
                session_id=sessionId,
                user_id=current_user["id"]
            )
            
            counter = 0
            assistant_full_message = ""
            
            async for chunk in chain.astream(
                {"input": request.message},
                config={"configurable": {"session_id": sessionId}}
            ):
                if isinstance(chunk, dict) and 'answer' in chunk:
                    token = chunk['answer']
                    if token:
                        assistant_full_message += token
                        json_data = json.dumps({"content": token, "formatted": True})
                        yield f"id: {counter}\nevent: message\ndata: {json_data}\n\n"
                        counter += 1
                
        except Exception as e:
            print(f"Error in streaming or saving assistant message: {str(e)}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )