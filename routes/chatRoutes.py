from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
from schemas.message import MessageRequest
from services.llm import llm_chain,callback_handler
from langchain.callbacks import AsyncIteratorCallbackHandler


router = APIRouter()



@router.post("/{sessionId}")
async def stream_chat_response(sessionId: str, request: MessageRequest):
    async def event_generator():
        try:
            task = asyncio.create_task(llm_chain.ainvoke(request.message))
            
            # Stream the tokens as they come in
            counter = 0
            async for token in callback_handler.aiter():
                yield f"id: {counter}\nevent: message\ndata: {token}\n\n"
                counter += 1
            
            # Wait for the task to complete
            await task
            
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