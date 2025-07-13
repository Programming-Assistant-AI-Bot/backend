from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from schemas.message import MessageRequest
from services.chatHistory.llm import make_conversational_chain
from utils.auth_utils import get_current_user
import json

router = APIRouter()

@router.post("/{sessionId}")
async def simple_stream_chat_response(sessionId: str, request: MessageRequest, current_user: dict = Depends(get_current_user)):
    async def event_generator():
        try:
            # Pass both session_id and user_id to the chain
            chain = make_conversational_chain(session_id=sessionId, user_id=current_user["id"])
            
            counter = 0
            async for chunk in chain.astream(
                {"input": request.message},
                config={"configurable": {"session_id": sessionId}}
            ):
                # Extract only the 'answer' content for streaming
                if isinstance(chunk, dict) and 'answer' in chunk:
                    token = chunk['answer']
                    if token:  # Only send non-empty tokens
                        json_data = json.dumps({"content": token, "formatted": True})
                        yield f"id: {counter}\nevent: message\ndata: {json_data}\n\n"
                        counter += 1
                
        except Exception as e:
            print(f"Error: {str(e)}")
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