"""File upload API endpoints."""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Annotated
import logging

from ..models.bug_model import FileUploadResponse
from .dependencies import Services

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["uploads"])


@router.post("", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    services: Services,
    file: Annotated[UploadFile, File(description="Image file to upload (.png, .jpg, .jpeg)")]
) -> FileUploadResponse:
    """Upload a file to Cloudinary.
    
    Handles file validation for supported image formats.
    Uploads files to Cloudinary with proper error handling.
    Returns Cloudinary URLs for frontend use.
    
    Args:
        services: Injected service container
        file: Image file to upload (UploadFile object)
        
    Returns:
        File upload response with Cloudinary URL
        
    Raises:
        HTTPException: If validation fails or upload fails
    """
    try:
        # Validate file has a filename
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="File must have a filename"
            )
        
        # Get file size
        file_content = await file.read()
        file_size = len(file_content)
        
        # Reset file pointer for upload
        await file.seek(0)
        
        # Upload to Cloudinary (validation handled internally)
        try:
            upload_result = await services.image_storage.upload_image(
                file=file.file,
                filename=file.filename,
                folder="bugtrackr/attachments"
            )
        except ValueError as e:
            # Validation error from Cloudinary service
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to upload file {file.filename}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file: {str(e)}"
            )
        
        logger.info(
            f"File uploaded successfully: {file.filename} -> {upload_result['public_id']}"
        )
        
        return FileUploadResponse(
            url=upload_result["url"],
            filename=file.filename,
            size=file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")
