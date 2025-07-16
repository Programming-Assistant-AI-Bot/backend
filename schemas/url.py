from pydantic import BaseModel
from typing import Optional

class UrlInput(BaseModel):
    link: str
    session_id: Optional[str] = None