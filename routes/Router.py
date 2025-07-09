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





router=APIRouter(prefix="/session",tags=["session"])



@router.put("/rename/{sessionId}/{newName}")
async def rename_Session(sessionId: str, newName: str):
    return await updateSessionName(sessionId, newName)


@router.delete("/deleteSession/{sessionId}")
async def delete_Session(sessionId:str):
    return await deleteSession(sessionId)


class QueryInput(BaseModel):
    query: str
    
@router.post("/createSession")
async def create_session(input: QueryInput):
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
            "sessionName": session_name,
            "createdAt": now,
            "updatedAt": now
        }
        
        # Insert session into collection
        result = await session_collection.insert_one(session_data)
        
     
        
        # Generate and save assistant response
        chain = make_conversational_chain(session_id=session_id)
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

@router.get("/getAllSessions")
async def fetch_Sessions():
    sessions_cursor = session_collection.find()
    sessions = await sessions_cursor.to_list(length=None)
    return getAllSessions(sessions)


