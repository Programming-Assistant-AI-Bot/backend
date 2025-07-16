from fastapi import APIRouter,File, UploadFile, Form,HTTPException
from Controllers.Controller import updateSessionName,deleteSession,addMessage,addSession
from Controllers.UrlController import validateUrl,validateGithubUrl
from services.chatHistory.llm import make_conversational_chain
from models.session import Session
from database.db import message_collection, session_collection
from schemas.sessionschema import getFirstMessageBySessionId, getAllSessions
from utils.gemini import generate_session_title
from datetime import datetime
import uuid
from pydantic import BaseModel
from utils.auth_bearer import JWTBearer
from utils.auth_utils import get_current_user
from fastapi import Depends
from bson import ObjectId


router=APIRouter(prefix="/session",tags=["session"])



@router.put("/rename/{sessionId}/{newName}")
async def rename_Session(
    sessionId: str, 
    newName: str, 
    current_user: dict = Depends(get_current_user)
):
    session = None
    # First try to find by sessionId (UUID format)
    session = await session_collection.find_one({"sessionId": sessionId, "userId": current_user["id"]})
    
    # If not found and the ID is 24 chars (possible ObjectId), try by _id
    if not session and len(sessionId) == 24:
        try:
            obj_id = ObjectId(sessionId)
            session = await session_collection.find_one({"_id": obj_id, "userId": current_user["id"]})
            
            # If found by ObjectId, use its sessionId for the update
            if session:
                sessionId = session["sessionId"]
        except Exception:
            pass
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # User ownership already verified through the query filters
    return await updateSessionName(sessionId, newName, current_user["id"])


@router.delete("/deleteSession/{sessionId}")
async def delete_Session(
    sessionId: str,
    current_user: dict = Depends(get_current_user)
):
    # Add ownership verification
    session = await session_collection.find_one({"sessionId": sessionId})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if user owns this session
    if str(session["userId"]) != current_user["id"]:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this session")
    
    return await deleteSession(sessionId,current_user["id"])


class QueryInput(BaseModel):
    query: str
    
# Update the getAllSessions endpoint
@router.get("/getAllSessions")
async def fetch_Sessions(current_user: dict = Depends(get_current_user)):
    try:
        # Get sessions for current user only
        user_id = current_user["id"]
        
        # Find all sessions for this user
        cursor = session_collection.find({"userId": user_id})
        sessions = await cursor.to_list(length=100)
        
        return getAllSessions(sessions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update the createSession endpoint
@router.post("/createSession")
async def create_session(input: QueryInput, current_user: dict = Depends(get_current_user)):
    try:
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Generate session title from the query
        session_name = generate_session_title(input.query)
        
        # Current timestamp
        now = datetime.utcnow()
        
        # Create session data
        session_data = {
            "sessionId": session_id,
            "userId": current_user["id"],  # Use authenticated user ID
            "sessionName": session_name,
            "createdAt": now,
            "updatedAt": now
        }
        
        # Insert session into collection
        result = await session_collection.insert_one(session_data)

        # Check if query contains special markers
        if not ("[Repository Link]" in input.query or "[Website URL]" in input.query or "[Attachment]" in input.query):
            # Generate and save assistant response - ADD user_id parameter
            chain = make_conversational_chain(
                session_id=session_id,
                user_id=current_user["id"]  # Add this line
            )
            
            assistant_response = ""
            async for chunk in chain.astream(
                {"input": input.query},
                config={"configurable": {"session_id": session_id}}
            ):
                if isinstance(chunk, dict) and 'answer' in chunk:
                    assistant_response += chunk['answer']
        
        return {
            "id": str(result.inserted_id),
            "sessionId": session_id,
            "sessionName": session_name,
            "createdAt": now,
            "updatedAt": now
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")
    
@router.post("/createSession")
async def create_session(input: QueryInput, current_user: dict = Depends(get_current_user)):
    try:
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Generate session title from the query (or use a placeholder if query is empty)
        session_name = generate_session_title(input.query or "New Session")
        
        # Current timestamp
        now = datetime.utcnow()
        
        # Create session data
        session_data = {
            "sessionId": session_id,
            "userId": current_user["id"],
            "sessionName": session_name,
            "createdAt": now,
            "updatedAt": now
        }
        
        # Insert session into collection
        result = await session_collection.insert_one(session_data)

        # Do NOT add any messages or assistant response here!

        return {
            "id": str(result.inserted_id),
            "sessionId": session_id,
            "sessionName": session_name,
            "createdAt": now,
            "updatedAt": now
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")