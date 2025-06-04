from fastapi import APIRouter,File, UploadFile, Form
from Controllers.Controller import updateSessionName,deleteSession,addMessage,addSession
from Controllers.UrlController import validateUrl,validateGithubUrl
from models.session import Session
from database.db import message_collection
from database.db import session_collection
from schemas.sessionschema import getFirstMessageBySessionId
from utils.gemini import generate_session_title
from datetime import datetime
from schemas.sessionschema import getAllSessions


router=APIRouter(prefix="/session",tags=["session"])


@router.get("/getFirstQuery{sessionId}")
async def fetch_First_User_Message(sessionId: str):
    return await getFirstMessageBySessionId(sessionId)


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


@router.get("/getAllSessions")
async def fetch_Sessions():
    sessions_cursor = session_collection.find()
    sessions = await sessions_cursor.to_list(length=None)
    return getAllSessions(sessions)


