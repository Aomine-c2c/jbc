from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse
from typing import Optional

from app.core.storage import storage_manager, STORAGE_CATEGORIES
from app.modules.iam.models import User

storage_router = APIRouter(prefix="/api/v1/storage", tags=["storage"])


def _get_current_user():
    from app.main import get_current_user as _gcu
    return _gcu


@storage_router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form("job_cards"),
    current_user: User = Depends(_get_current_user()),
):
    """Authenticated file upload endpoint for maintenance attachments and reports."""
    if category not in STORAGE_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid storage category. Permitted: {STORAGE_CATEGORIES}",
        )

    try:
        content = await file.read()
        metadata = storage_manager.save_file(
            category=category,
            filename=file.filename or "attachment",
            content=content,
            content_type=file.content_type,
        )
        return {"status": "success", "file": metadata}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File storage failed: {str(e)}",
        )


@storage_router.get("/download/{category}/{filename}")
async def download_file(
    category: str,
    filename: str,
    current_user: User = Depends(_get_current_user()),
):
    """Downloads or streams an attached document file."""
    try:
        file_path = storage_manager.get_file_path(category, filename)
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream",
        )
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@storage_router.delete("/{category}/{filename}")
async def delete_attachment(
    category: str,
    filename: str,
    current_user: User = Depends(_get_current_user()),
):
    """Deletes an attached document file."""
    success = storage_manager.delete_file(category, filename)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found or deletion failed.")
    return {"status": "deleted", "filename": filename}
