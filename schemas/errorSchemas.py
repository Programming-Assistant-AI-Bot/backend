from pydantic import BaseModel

# This model defines the structure of the JSON that your
# VS Code extension will send to this endpoint.
# It expects a JSON object like: { "code": "..." }
class CodeCheckRequest(BaseModel):
    code: str
