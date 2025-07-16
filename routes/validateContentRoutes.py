from fastapi import APIRouter, UploadFile, Form, File, Depends
from schemas.url import UrlInput
from Controllers.UrlController import validateUrl, validateGithubUrl
from Controllers.FileController import addDocument
from utils.auth_utils import get_current_user

router = APIRouter(prefix="/Contents", tags=["content"])

@router.post("/addFile")
async def add_file(
    file: UploadFile = File(...), 
    doc_name: str = Form(...),
    session_id: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    # Pass the current user to addDocument
    return await addDocument(file, doc_name, session_id, current_user)

@router.post("/validateWebUrl")
async def validate_web_url(
    data: UrlInput,
    current_user: dict = Depends(get_current_user)
):
    # Pass the user ID to validateUrl
    return await validateUrl(data, current_user["id"])

@router.post("/validateGithubUrl")
async def validate_github_url(
    data: UrlInput,
    current_user: dict = Depends(get_current_user)
):
    # Pass the user ID to validateGithubUrl
    result = await validateGithubUrl(str(data.link), data.session_id, current_user["id"])
    return result