from pydantic import BaseModel,Field
from bson import ObjectId
from typing import Optional,Literal
from datetime import datetime,timezone

class Message(BaseModel):
    sessionId : str
    role : Literal["assistant","user"]
    content: str
    timestamp: datetime 
