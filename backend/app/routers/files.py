"""File upload/download routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.file import File
from app.schemas.file import FileRead
from app.services.storage_service import storage_service

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=FileRead)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file."""
    try:
        contents = await file.read()
        if not contents:
            raise ValueError("Empty file")

        # Generate unique filename with user scope
        file_id = str(uuid.uuid4())
        filename = f"{current_user.id}/{file_id}_{file.filename}"

        # Upload file (saves locally, optionally uploads to Azure)
        local_path, blob_path = await storage_service.upload_file(contents, filename)

        # Create file record
        file_record = File(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            original_name=file.filename,
            blob_path=blob_path,
            content_type=file.content_type or "application/octet-stream",
            size_bytes=len(contents)
        )
        db.add(file_record)
        db.commit()
        db.refresh(file_record)

        return file_record

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{file_id}", response_model=FileRead)
async def get_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get file info."""
    file = db.query(File).filter(File.id == file_id).first()
    if not file or file.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get download URL for a file."""
    file = db.query(File).filter(File.id == file_id).first()
    if not file or file.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        url = await storage_service.get_download_url(file.blob_path)
        return {"download_url": url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a file."""
    file = db.query(File).filter(File.id == file_id).first()
    if not file or file.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete from storage (Azure and/or local)
    try:
        await storage_service.delete_file(file.blob_path)
    except Exception as e:
        # Log error but continue with database cleanup
        import logging
        logging.error(f"Error deleting file from storage: {e}")

    db.delete(file)
    db.commit()
    return {"message": "File deleted"}
