from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from schemas.message import MessageRequest
from services.chatHistory.llm import make_conversational_chain
from models.chatMessages import Message
from datetime import datetime
import json
from database.db import message_collection,session_collection
from Controllers.Controller import addMessage
from bson import ObjectId


router = APIRouter(prefix="/chat", tags=["chat"])


async def getSessionId(object_id: str):
    try:
        obj_id = ObjectId(object_id)  # Validate and convert to ObjectId
        session_data = await session_collection.find_one({"_id": obj_id})
        
        if not session_data:
            return None
        
        return session_data.get("sessionId")
    except Exception as e:
        raise ValueError(f"Error retrieving session: {str(e)}")



async def addMessage(sessionId: str, content: str, role: str):
    try:
        now = datetime.utcnow()
        message_data = {
            "sessionId": sessionId,  # Store as string, consistent with Message model
            "role": role,
            "content": content,
            "timestamp": now
        }
        result = await message_collection.insert_one(message_data)
        print(f"Inserted message: {message_data}, ID: {result.inserted_id}")
        return {"id": str(result.inserted_id)}
    except Exception as e:
        print(f"Failed to insert message: {message_data}, Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save message: {str(e)}")

@router.post("/{sessionId}")
async def simple_stream_chat_response(sessionId: str, request: MessageRequest):
    # Save the user's message to the session
    savingSId = await getSessionId(sessionId)
    try:
        await addMessage(savingSId, request.message, "user")
    except Exception as e:
        print(f"Error saving user message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save user message: {str(e)}")

    async def event_generator():
        try:
            chain = make_conversational_chain(session_id=sessionId)
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
            # Save the full assistant message
            if assistant_full_message:
                await addMessage(savingSId, assistant_full_message, "assistant")
            else:
                print("No assistant message to save.")

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