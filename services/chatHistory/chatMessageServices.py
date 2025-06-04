from database.db import message_collection ,session_collection
from models.chatMessages import Message
from bson import ObjectId
        

async def getMessage(sessionId:str):
    try:
        
        obj_id = ObjectId(sessionId)

        sess = await session_collection.find_one({"_id": obj_id})
        if not sess:
            return []
        session_id_str = sess["sessionId"]
        print(session_id_str)
        result = message_collection.find({"sessionId":session_id_str},{"role":1,"content":1,"_id":0}).sort("timestamp",1)
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



