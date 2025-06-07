from database.db import message_collection
from models.chatMessages import Message


async def getMessage(sessionId:str):
    try:
        result = message_collection.find({"sessionId":sessionId},{"role":1,"content":1,"_id":0}).sort("timestamp",1)
        messages = [document async for document in result]
        if messages:
            return messages
        else:
            return []
        
    except Exception as e:
        print(f"Error retrieving messages:{str(e)}")
        return []

async def insertMessage(msg: Message):
    try:
        message_dict = msg.model_dump(by_alias=True)  
        result = await message_collection.insert_one(message_dict)
        return result.inserted_id
    except Exception as e:
        print(f"Error inserting message: {str(e)}")
        return None



