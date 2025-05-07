from database.db import session_collection,message_collection
from models.session import Session
from fastapi import HTTPException
from datetime import datetime


async def insertSession(session:Session):
    session_dict=dict(session)
    result = await session_collection.insert_one(session_dict)
    if result:
        return{"id":str(result.inserted_id)}
    else:
        return{"error":"Error occured"}
    

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