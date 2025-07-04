from fastapi import APIRouter,File, UploadFile, Form,HTTPException
from Controllers.Controller import updateSessionName,deleteSession,addMessage,addSession
from Controllers.UrlController import validateUrl,validateGithubUrl
from models.session import Session
from database.db import message_collection
from database.db import session_collection
from schemas.sessionschema import getFirstMessageBySessionId
from utils.gemini import generate_session_title
from datetime import datetime
from schemas.sessionschema import getAllSessions
import uuid
from pydantic import BaseModel
from utils.gemini import getResponse



router=APIRouter(prefix="/session",tags=["session"])



@router.post("/addMessage/{sessionId}")
async def add_Message(sessionId:str,content:str):
    return await addMessage(sessionId,content)

@router.post('/')
async def add_Session(content:str,userId:str):
    return await addSession(content,userId)


@router.put("/rename/{sessionId}/{newName}")
async def rename_Session(sessionId: str, newName: str):
    return await updateSessionName(sessionId, newName)


@router.delete("/deleteSession/{sessionId}")
async def delete_Session(sessionId:str):
    return await deleteSession(sessionId)


@router.post("/generateSessionTitle/{sessionId}")
async def generate_session_title_route(sessionId: str):
    # Step 1: Get first user message for the session
    firstMessage = await getFirstMessageBySessionId(sessionId)
    
    if "error" in firstMessage:
        return firstMessage
    
    query = firstMessage["content"]

    # Step 2: Generate session title from the query
    title = generate_session_title(query)

    # Step 3: Insert into session_collection
    now = datetime.utcnow()
    sessionData = {
        "sessionId": sessionId,
        "sessionName": title,
        "createdAt":now,
        "updatedAt":now
    }

    result = await session_collection.insert_one(sessionData)
    return {"id": str(result.inserted_id), 
            "sessionName": title,
            "createdAt":now,
            "updatedAt":now,
            }

@router.get("/getFirstQuery{sessionId}")
async def fetch_First_User_Message(sessionId: str):
    return await getFirstMessageBySessionId(sessionId)


class QueryInput(BaseModel):
    query: str
    
@router.post("/createSession")
async def create_session(payload: QueryInput):
    query = payload.query
    
    try:
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Generate session title from the query
        session_name = generate_session_title(query)
        
        # Current timestamp
        now = datetime.utcnow()
        
        # Create session data
        session_data = {
            "sessionId": session_id,
            "sessionName": session_name,
            "createdAt": now,
            "updatedAt": now
        }
        
        # Insert session into collection
        result = await session_collection.insert_one(session_data)
        
        # Store the first query as a message
       
        await addMessage(session_id,query,"user")
        
        
        return {
            "id": str(result.inserted_id),
            "sessionId": session_id,
            "sessionName": session_name,
            "createdAt": now,
            "updatedAt": now
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


# Define the input payload schema
class GeminiRequest(BaseModel):
    text: str

@router.post("/getResponseFromGemini")
async def getResponseFromGemini(payload: GeminiRequest):
    try:
        response = getResponse(payload.text)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/getAllSessions")
async def fetch_Sessions():
    sessions_cursor = session_collection.find()
    sessions = await sessions_cursor.to_list(length=None)
    return getAllSessions(sessions)


