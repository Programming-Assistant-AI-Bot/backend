from fastapi import APIRouter, UploadFile, Form, File
from schemas.url import UrlInput
from Controllers.UrlController import validateUrl,validateGithubUrl
from Controllers.FileController import addDocument

router = APIRouter(prefix="/Contents",tags=["content"])

@router.post("/addFile")
async def add_file(file: UploadFile = File(...), doc_name: str = Form(...)):
    return await addDocument(file,doc_name)

@router.post("/validateWebUrl")
async def validate_web_url(data: UrlInput):
    return await validateUrl(data)

@router.post("/validateGithubUrl")
async def validate_github_url(data: UrlInput):
    result = await validateGithubUrl(str(data.link), data.session_id)
    return result