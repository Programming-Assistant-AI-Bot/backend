from database.db import message_collection ,session_collection
from models.chatMessages import Message
from bson import ObjectId
import uuid
from fastapi import HTTPException

async def getMessage(sessionId: str, userId: str):
    try:
        session_filter = None

        # Case 1: Try to parse as ObjectId
        if len(sessionId) == 24:
            try:
                obj_id = ObjectId(sessionId)
                sess = await session_collection.find_one({"_id": obj_id, "userId": userId})
                if sess:
                    sessionId = sess["sessionId"]  # update to actual UUID string
                    session_filter = {"sessionId": sessionId}
            except Exception:
                pass  # Not a valid ObjectId even though it has 24 chars

        # Case 2: Try UUID format
        if session_filter is None:
            try:
                uuid_obj = uuid.UUID(sessionId)  # Validate format
                # Check if the session belongs to this user
                sess = await session_collection.find_one({"sessionId": str(uuid_obj), "userId": userId})
                if not sess:
                    raise HTTPException(status_code=403, detail="Access denied to this session")
                    
                session_filter = {"sessionId": str(uuid_obj)}
            except ValueError:
                raise ValueError("Invalid sessionId format")

        # Now get messages
        result = message_collection.find(session_filter, {"role": 1, "content": 1, "_id": 0}).sort("timestamp", 1)
        messages = [document async for document in result]
        return messages if messages else []

    except Exception as e:
        print(f"Error retrieving messages: {str(e)}")
        return []


async def insertMessage(msg: Message):
    try:
        message_dict = msg.model_dump(by_alias=True)  
        result = await message_collection.insert_one(message_dict)
        return result.inserted_id
    except Exception as e:
        print(f"Error inserting message: {str(e)}")
        return None



