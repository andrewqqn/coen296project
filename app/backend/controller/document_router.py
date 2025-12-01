from fastapi import APIRouter, UploadFile
from services import document_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document_endpoint(file: UploadFile):
    file_bytes = await file.read()
    file_path = f"documents/{file.filename}"
    stored_path = document_service.upload_document(file_path, file_bytes)
    return {"path": stored_path}


@router.get("/url")
def get_document_url(path: str):
    """
    Generate a (signed) URL to access a document.
    """
    return {"path": path, "url": document_service.generate_document_url(path)}


@router.get("/download")
def download_document(path: str):
    """
    Directly download a document (useful for backend preview or internal use).
    """
    data = document_service.download_document(path)
    return {"path": path, "size": len(data)}


@router.delete("/delete")
def delete_document(path: str):
    """
    Delete a document.
    """
    document_service.delete_document(path)
    return {"success": True, "path": path}


@router.get("/local/{file_path:path}")
def serve_local_file(file_path: str):
    """
    Serve a local file (for development/emulator mode).
    This endpoint handles files stored locally with local:// prefix.
    """
    from fastapi.responses import FileResponse
    import os
    
    # Construct full path
    full_path = os.path.join(os.getcwd(), file_path)
    
    # Security check: ensure the file is within the expected directory
    if not os.path.exists(full_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on file extension
    import mimetypes
    media_type = mimetypes.guess_type(full_path)[0] or "application/octet-stream"
    
    return FileResponse(full_path, media_type=media_type)
