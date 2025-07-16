from database.db import session_collection,message_collection
from models.session import Session
from models.chatMessages import Message
from fastapi import HTTPException
from datetime import datetime
from utils.gemini import generate_session_title
from bson import ObjectId
from vectordb.persistentFaiss import PersistentSessionStorage

vectordb = PersistentSessionStorage()



async def addMessage(sessionId: str, content: str, role: str, userId: str = None):
    now = datetime.utcnow()
    message_data = {
        "sessionId": sessionId,
        "userId": userId,  # Add user ID
        "role": role,
        "content": content,
        "timestamp": now
    }
    result = await message_collection.insert_one(message_data)
    print(message_data)
    return {"id": str(result.inserted_id)}



def getTitleFromContent(content: str) -> str:
    """Generate a title from the user's message content."""
    # Clean up the content
    content = content.strip()
    
    # Handle empty content
    if not content:
        return "New Session"
        
    # Handle content for attachments
    if "[Repository Link]" in content:
        url = content.replace("[Repository Link]", "").strip()
        # Extract repo name from URL
        repo_parts = url.strip("/").split("/")
        if len(repo_parts) >= 2:
            return f"Repository: {repo_parts[-2]}/{repo_parts[-1]}"
        return f"Repository Analysis"
        
    if "[Website URL]" in content:
        url = content.replace("[Website URL]", "").strip()
        # Extract domain from URL
        from urllib.parse import urlparse
        try:
            domain = urlparse(url).netloc
            return f"Website: {domain}"
        except:
            return "Website Analysis"
            
    if "[Attachment]" in content:
        file_name = content.replace("[Attachment]", "").strip()
        return f"Document: {file_name}"
        
    # For regular text messages, use the first ~40 chars
    title = generate_session_title(content)
    return title



async def generateNewSessionId(userId: str = None) -> str:
    # If userId is provided, make session IDs unique per user
    if userId:
        last_session = await session_collection.find({"userId": userId}).sort("sessionId", -1).limit(1).to_list(1)
        
        if last_session:
            # Extract just the numeric part from the user's last session
            last_id_str = last_session[0]["sessionId"]
            if last_id_str.startswith("s"):
                number = int(last_id_str[1:])
                new_number = number + 1
                return f"s{new_number:04d}"
    
    # Default session ID format (can be used if userId is not provided)
    last_session = await session_collection.find().sort("sessionId", -1).limit(1).to_list(1)
    if last_session:
        last_id_str = last_session[0]["sessionId"]
        if last_id_str.startswith("s"):
            number = int(last_id_str[1:])
            new_number = number + 1
            return f"s{new_number:04d}"
    
    return "s0001"  # Default if no sessions exist yet




async def addSession(content: str, userId: str):
    session_Id = await generateNewSessionId()
    title = getTitleFromContent(content)
    now = datetime.utcnow()
    session_data = Session(
        sessionId=session_Id,
        sessionName=generate_session_title(content),
        userId=userId,
        createdAt=now,
        updatedAt=now
    )
    await session_collection.insert_one(session_data.dict())
    await addMessage(session_Id, content, "user", userId)  # Pass userId
    return {
        "sessionId": session_Id,
        "sessionName": title,
    }

   
async def updateSessionName(sessionId: str, newName: str, userId: str = None):
    # Build the query based on whether userId is provided
    query = {"sessionId": sessionId}
    if userId:
        query["userId"] = userId
    
    result = await session_collection.update_one(
        query,
        {
            "$set": {
                "sessionName": newName,
                "updatedAt": datetime.utcnow()
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Session not found or name unchanged")

    return {"message": "Session name updated"}




async def deleteSession(sessionId: str, userId: str):
    try:
        
        # Build the query based on whether userId is provided
        query = {"sessionId": sessionId}
        if userId:
            query["userId"] = userId
            
        result = await session_collection.delete_one(query)
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")

        # Delete all messages related to this session (also filtered by userId if provided)
        message_query = {"sessionId": sessionId}
        if userId:
            message_query["userId"] = userId
        await message_collection.delete_many(message_query)

        vectordb.delete_session(user_id=userId,session_id=sessionId)
        
        return {"message": "Session and all related messages deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting session {sessionId}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting session")

