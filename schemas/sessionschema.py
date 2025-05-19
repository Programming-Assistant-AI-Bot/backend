from bson import ObjectId
from pymongo import ASCENDING
from database.db import message_collection

#Mesages
def getIndividualMessage(message) -> dict:
    return {
        "id": str(message["_id"]),
        "sessionId": message["sessionId"],
        "role": message["role"],
        "content": message["content"],
        "timestamp": message["timestamp"]
    }

async def getAllMessages(messages) -> list:
    message_list = await messages.to_list(length=100)
    return [getIndividualMessage(m) for m in message_list]



async def getFirstMessageBySessionId(session_id: str):
    pipeline = [
        {"$match": {"sessionId": session_id, "role": "user"}},
        {"$sort": {"timestamp": 1}},
        {"$limit": 1}
    ]

    cursor = message_collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    if result:
        return getIndividualMessage(result[0])
    else:
        return {"error": "No message found for this sessionId"}

#Sessions
# Convert a single session document to dictionary
# def getIndividualSession(session) -> dict:
#     return {
#         "id": str(session["_id"]),
#         "sessionId": session["sessionId"],
#         "sessionName": session["sessionName"],
#         "createdAt": session["createdAt"],
#         "updatedAt": session["updatedAt"]
#     }

def getIndividualSession(session: dict) -> dict:
    return {
        "id": str(session.get("_id", "")),
        "sessionId": session.get("sessionId", ""),
        "sessionName": session.get("sessionName", ""),
        "userId": str(session.get("userId", "")),
        "createdAt": session.get("createdAt"),
        "updatedAt": session.get("updatedAt"),
    }


# Convert a list of session documents to a list of dictionaries
def getAllSessions(sessions) -> list:
    return [getIndividualSession(session) for session in sessions]
