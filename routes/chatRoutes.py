from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
from schemas.message import MessageRequest
from services.chatHistory.llm import llm_chain, get_callback_handler , conversational_chain
from models.chatMessages import Message
from services.chatHistory.chatMessageServices import insertMessage
import json


router = APIRouter()

@router.post("/{sessionId}")
async def stream_chat_response(sessionId: str, request: MessageRequest):
    async def event_generator():
        try:
         
            # Create a new callback handler for this request
            callback_handler = get_callback_handler()
            
            # Create a task with the new callback handler
            print("Starting LLM invocation")
            task = asyncio.create_task(
                conversational_chain.ainvoke(
                    
                    {"input":request.message},  # Use the actual question rather than "Test message"
                    config={"configurable": {"session_id": sessionId},"callbacks": [callback_handler]}
                )
            )
            print("LLM invocation started.")
            
            # Collect the full response
            full_response = ""
            
            # Stream the tokens as they come in
            counter = 0
            async for token in callback_handler.aiter():
                full_response += token
                
                # Package the token in a structured JSON format
                json_data = json.dumps({"content": token, "formatted": True})
                yield f"id: {counter}\nevent: message\ndata: {json_data}\n\n"
                counter += 1
            
            # Wait for the task to complete
            result = await task
            
        except Exception as e:
            print(f"Error in event generator: {str(e)}")
            yield f"data: Error generating response: {str(e)}\n\n"
            yield f"data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Content-Type-Options": "nosniff"
        }
    )