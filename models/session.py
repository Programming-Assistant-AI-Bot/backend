# from pydantic import BaseModel, Field
# from datetime import datetime

# class Session(BaseModel):
#     sessionId: str 
#     sessionName: str
#     createdAt: datetime = Field(default_factory=datetime.utcnow)
#     updatedAt: datetime = Field(default_factory=datetime.utcnow)


from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class Session(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    sessionId: str
    sessionName: str
    userId: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: lambda oid: str(oid)
        }
