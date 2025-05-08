from database.db import session_collection,message_collection
from models.session import Session
from models.chatMessages import Message
from fastapi import HTTPException
from datetime import datetime
from utils.gemini import generate_session_title



async def addMessage(sessionId: str, content: str):
    message_data = Message(
        sessionId=sessionId,
        content=content,
        role="user",
        timestamp= datetime.utcnow()
    )
    result = await message_collection.insert_one(message_data.dict())
    return {"id": str(result.inserted_id)}



def getTitleFromContent(content: str) -> str:
    title = generate_session_title(content)
    return title



async def generateNewSessionId() -> str:
    last_session = await session_collection.find().sort("sessionId", -1).limit(1).to_list(1)
    
    if last_session:
        last_id_str = last_session[0]["sessionId"]  # e.g., "s0004"
        number = int(last_id_str[1:])  # Strip the "s" and convert to int
        new_number = number + 1
        return f"s{new_number:04d}"  # Format back to "s0005"
    
    return "s0001"  # Default if no sessions exist yet




async def addSession(content: str):
    session_Id = await generateNewSessionId()
    title=getTitleFromContent(content)
    now = datetime.utcnow()
    session_data = Session(
        sessionId=session_Id,
        sessionName=generate_session_title(content),
        createdAt=now,
        updatedAt=now
    )
    await session_collection.insert_one(session_data.dict())
    await addMessage(session_Id, content)
    return{
        "sessionId": session_Id,
        "sessionName": title,
    }



    
async def updateSessionName(sessionId:str, newName:str):
    result = await session_collection.update_one(
        {"sessionId": sessionId},
        {"$set": {"sessionName": newName,
                  "updatedAt":datetime.utcnow()
                }
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Session not found or name unchanged")
    



async def deleteSession(sessionId:str):
    result = await session_collection.delete_one({"sessionId":sessionId})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found or name unchanged")
    await message_collection.delete_many({"sessionId":sessionId})


