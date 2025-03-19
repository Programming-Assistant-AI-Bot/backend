from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
from schemas.message import MessageRequest
from services.llm import llm_chain, get_callback_handler
from models.chatMessages import Message
from services.chatMessageServices import insertMessage


router = APIRouter()

@router.post("/{sessionId}")
async def stream_chat_response(sessionId: str, request: MessageRequest):
    async def event_generator():
        try:
            # Create a new callback handler for this request
            callback_handler = get_callback_handler()
            
            # Create a task with the new callback handler
            task = asyncio.create_task(
                llm_chain.ainvoke(
                    request.message,
                    config={"callbacks": [callback_handler]}
                )
            )
            
            # Collect the full response
            full_response = ""
            
            # Stream the tokens as they come in
            counter = 0
            async for token in callback_handler.aiter():
                full_response += token
                yield f"id: {counter}\nevent: message\ndata: {token}\n\n"
                counter += 1
            
            # Wait for the task to complete
            result = await task
            
            # Save the user message too
            user_msg = Message(
                sessionId=sessionId,
                role="user",
                content=request.message
            )
            await insertMessage(user_msg)

             # Save the completed message to the database
            assistant_msg = Message(
                sessionId=sessionId,
                role="assistant",
                content=full_response
            )
            await insertMessage(assistant_msg)
            
            # Send the completion signal
            yield f"id: {counter}\nevent: message\ndata: [DONE]\n\n"
            
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