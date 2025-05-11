from pydantic import BaseModel
from datetime import datetime

class File(BaseModel):
    fileId:str
    fileName:str
    uploadedAt:datetime
    fileLocationLink:str
    
    
