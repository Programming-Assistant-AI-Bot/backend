from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pathlib import Path
from fastapi import HTTPException, File, UploadFile, Form
from datetime import datetime
import io
import tempfile
import os
from database.db import file_collection
import pymupdf as fitz

# Add imports for PDF processing and vector storage
from services.loaders.pdfLoader import get_split_chunks_from_pdf
from vectordb.persistentFaiss import PersistentSessionStorage


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
    
# Initialize vector storage
storage = PersistentSessionStorage(base_directory="./session_storage")

async def addDocument(file: UploadFile = File(...), doc_name: str = Form(...), session_id: str = Form(...)):
    """Upload a document to Google Drive, process it, and store in vector database"""
    
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

    # Process PDF content and add to vector database
    try:
        # Create a temporary file to process the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Extract and chunk the PDF content
        chunks = get_split_chunks_from_pdf(temp_file_path, chunk_size=1000, chunk_overlap=100)
        
        # Add metadata to chunks
        for chunk in chunks:
            chunk.metadata.update({
                "file_id": file_id,
                "file_name": doc_name,
                "upload_date": datetime.now().isoformat()
            })
        
        # Add chunks to the session's vector database
        storage.add_documents_to_session(session_id, chunks)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            
        # Cleanup from Drive if processing failed
        try:
            drive_service.files().delete(fileId=file_id).execute()
        except Exception as drive_error:
            print(f"Drive cleanup failed: {drive_error}")
            
        raise HTTPException(
            status_code=500,
            detail=f"PDF processing failed: {str(e)}"
        )

    # Create MongoDB document
    file_document = {
        "fileId": file_id,
        "fileName": doc_name,
        "uploadedAt": datetime.now(),
        "fileLocationLink": file_link,
        "sessionId": session_id,
        "pageCount": page_count,
        "chunksCount": len(chunks),
        "vectorized": True
    }

    # Store in MongoDB
    try:
        result = await file_collection.insert_one(file_document)
        return {
            "fileId": file_id,
            "fileName": doc_name,
            "uploadedAt": file_document["uploadedAt"].isoformat(),
            "fileLocationLink": file_link,
            "mongoId": str(result.inserted_id),
            "status": "Successfully uploaded and vectorized"
        }
        
    except Exception as e:
        # Comprehensive cleanup if MongoDB insert failed
        cleanup_errors = []
        
        # Remove from Google Drive
        if file_id:
            try:
                drive_service.files().delete(fileId=file_id).execute()
            except Exception as drive_error:
                cleanup_errors.append(f"Drive cleanup failed: {drive_error}")
        
        # Remove from vector database
        if file_id and chunks:
            try:
                removed_count = storage.remove_documents_by_file_id(session_id, file_id)
                print(f"Removed {removed_count} documents from vector DB")
            except Exception as vector_error:
                cleanup_errors.append(f"Vector DB cleanup failed: {vector_error}")
        
        # Log cleanup errors if any
        if cleanup_errors:
            print(f"Cleanup errors: {'; '.join(cleanup_errors)}")
            
        raise HTTPException(    
            status_code=500,
            detail=f"Database insertion failed: {str(e)}"
        )
    