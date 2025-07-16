from fastapi import APIRouter, HTTPException
from schemas.errorSchemas import CodeCheckRequest
from utils.gemini import get_code_errors

# Create a new router for error-related endpoints
router = APIRouter()

@router.post("/checkErrors/")
async def check_code_for_errors(request: CodeCheckRequest):
    """
    This endpoint receives Perl code, uses the Gemini service to find errors,
    and returns them.
    """
    try:
        # Call the service function that does the heavy lifting
        errors = await get_code_errors(request.code)
        
        # Return the list of errors in a JSON response.
        # The VS Code extension expects a JSON object with an "errors" key.
        return {"errors": errors}
    except Exception as e:
        # If something unexpected happens, send back a server error.
        raise HTTPException(status_code=500, detail=str(e))

