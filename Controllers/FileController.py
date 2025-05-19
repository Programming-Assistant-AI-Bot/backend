from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google.oauth2 import service_account
from googleapiclient.discovery import build
from fastapi.responses import StreamingResponse, RedirectResponse,JSONResponse
from pathlib import Path
from fastapi import HTTPException, File, UploadFile, Form
from datetime import datetime
import io
from database.db import file_collection
import fitz 

folder_id = "1n0BSpH4q3u0Zxeagk8Yl5ocHtK3AVCh7"
current_user = "Sample User"
SERVICE_ACCOUNT = Path(__file__).resolve().parent / '..' / "Config" / "googlecloud.json"
SERVICE_ACCOUNT = SERVICE_ACCOUNT.resolve()
SCOPES = ['https://www.googleapis.com/auth/drive.file']
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

if not drive_service:
    print("Failed to initialize Google Drive service")
else:
    print("Google Drive service initialized successfully")
    
async def addDocument(file: UploadFile = File(...), doc_name: str = Form(...)):
    """Upload a document to Google Drive and store metadata in MongoDB"""
    
    content = await file.read()
    
    # Get PDF page count
    with fitz.open(filetype="pdf", stream=content) as doc:
        page_count = doc.page_count

    # Upload to Google Drive
    try:
        file_stream = io.BytesIO(content)
        media = MediaIoBaseUpload(
            file_stream, 
            mimetype=file.content_type,
            resumable=True
        )

        drive_response = drive_service.files().create(
            body={
                "name": file.filename,
                "parents": [folder_id]
            },
            media_body=media,
            fields="id"
        ).execute()

        file_id = drive_response["id"]
        file_link = f"https://drive.google.com/file/d/{file_id}/view"

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google Drive upload failed: {str(e)}"
        )

    # Create MongoDB document
    file_document = {
        "fileId": file_id,
        "fileName": doc_name,
        "uploadedAt": datetime.now(),
        "fileLocationLink": file_link,
    }

    # Store in MongoDB
    try:
        result = await file_collection.insert_one(file_document)
        return {
            "fileId": file_id,
            "fileName": doc_name,
            "uploadedAt": file_document["uploadedAt"].isoformat(),
            "fileLocationLink": file_link,
            "mongoId": str(result.inserted_id)
        }
        
    except Exception as e:
        # Cleanup from Drive if MongoDB insert failed
        try:
            drive_service.files().delete(fileId=file_id).execute()
        except Exception as drive_error:
            print(f"Drive cleanup failed: {drive_error}")
            
        raise HTTPException(    
            status_code=500,
            detail=f"Database insertion failed: {str(e)}"
        )


    