from pydantic import BaseModel, HttpUrl

class UrlInput(BaseModel):
    link: HttpUrl  # This field will only accept valid HTTP/HTTPS URLs
    session_id: str