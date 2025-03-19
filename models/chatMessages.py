from pydantic import BaseModel,Field
from bson import ObjectId
from typing import Optional,Literal
from datetime import datetime,timezone

class Message(BaseModel):
    sessionId : str
    role : Literal["assistant","user"]
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class config:
        json_encoders = {
            datetime: lambda v:v.isoformat()
        }