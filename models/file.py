from pydantic import BaseModel
from datetime import datetime

class File(BaseModel):
    fileId:str
    fileName:str
    userId: str
    sessionId: str
    uploadedAt:datetime
    fileLocationLink:str
    
    
