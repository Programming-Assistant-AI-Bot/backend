from pydantic import BaseModel, Field
from datetime import datetime

class Session(BaseModel):
    sessionId: str 
    sessionName: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
