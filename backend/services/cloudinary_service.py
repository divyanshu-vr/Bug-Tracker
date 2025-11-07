"""Cloudinary integration service for image storage and management."""

from typing import Optional, Dict, Any, BinaryIO
from abc import ABC, abstractmethod
import cloudinary
import cloudinary.uploader
import cloudinary.api
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ImageStorageService(ABC):
    """Abstract interface for image storage operations."""

    @abstractmethod
    def validate_file(self, filename: str, file_size: int) -> tuple[bool, Optional[str]]:
        """Validate file before upload."""
        pass

    @abstractmethod
    async def upload_image(
        self,
        file: BinaryIO,
        filename: str,
        folder: str
    ) -> Dict[str, Any]:
        """Upload image to storage."""
        pass

    @abstractmethod
    async def delete_image(self, public_id: str) -> bool:
        """Delete image from storage."""
        pass

    @abstractmethod
    def get_image_url(
        self,
        public_id: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: str = "fill"
    ) -> str:
        """Generate image URL with transformations."""
        pass


class CloudinaryService(ImageStorageService):
    """Manages Cloudinary image uploads and storage."""

    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(
        self,
        cloud_name: str,
        api_key: str,
        api_secret: str,
        max_file_size: Optional[int] = None
    ):
        """Initialize Cloudinary service.
        
        Args:
            cloud_name: Cloudinary cloud name
            api_key: Cloudinary API key
            api_secret: Cloudinary API secret
            max_file_size: Maximum file size in bytes (defaults to MAX_FILE_SIZE)
        """
        self._cloud_name = cloud_name
        self._max_file_size = max_file_size if max_file_size is not None else self.MAX_FILE_SIZE
        self._configure(cloud_name, api_key, api_secret)

    def _configure(self, cloud_name: str, api_key: str, api_secret: str) -> None:
        """Configure Cloudinary with credentials.
        
        Args:
            cloud_name: Cloudinary cloud name
            api_key: Cloudinary API key
            api_secret: Cloudinary API secret
        """
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        logger.info(f"Cloudinary configured for cloud: {cloud_name}")

    def validate_file(self, filename: str, file_size: int) -> tuple[bool, Optional[str]]:
        """Validate file before upload.
        
        Args:
            filename: Name of the file
            file_size: Size of the file in bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            return False, f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
        
        # Check file size
        if file_size > self._max_file_size:
            max_mb = self._max_file_size / (1024 * 1024)
            return False, f"File size exceeds maximum allowed size of {max_mb}MB"
        
        return True, None

    async def upload_image(
        self,
        file: BinaryIO,
        filename: str,
        folder: str = "bugtrackr/attachments"
    ) -> Dict[str, Any]:
        """Upload image to Cloudinary.
        
        Args:
            file: File object to upload
            filename: Original filename
            folder: Cloudinary folder path
            
        Returns:
            Dictionary containing upload result with 'url' and 'public_id'
            
        Raises:
            ValueError: If file validation fails or file is not seekable/readable
            Exception: If upload fails
        """
        # Validate file object
        if not hasattr(file, 'read') or not callable(file.read):
            raise ValueError("File object must be readable")
        
        if not hasattr(file, 'seek') or not callable(file.seek):
            raise ValueError("File object must be seekable")
        
        # Get file size
        try:
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
        except (OSError, IOError) as e:
            raise ValueError(f"Failed to read file: {e}")
        
        # Validate file before upload
        is_valid, error_message = self.validate_file(filename, file_size)
        if not is_valid:
            raise ValueError(error_message)
        
        try:
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type="image"
            )
            
            logger.info(f"Successfully uploaded image: {filename} -> {result['public_id']}")
            
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "format": result["format"],
                "width": result["width"],
                "height": result["height"],
                "bytes": result["bytes"]
            }
            
        except cloudinary.exceptions.Error as e:
            logger.error(f"Cloudinary upload failed for {filename}: {e}")
            raise Exception(f"Failed to upload image: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            raise

    async def delete_image(self, public_id: str) -> bool:
        """Delete image from Cloudinary.
        
        Args:
            public_id: Cloudinary public ID of the image
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            success = result.get("result") == "ok"
            
            if success:
                logger.info(f"Successfully deleted image: {public_id}")
            else:
                logger.warning(f"Failed to delete image: {public_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting image {public_id}: {e}")
            return False

    def get_image_url(
        self,
        public_id: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: str = "fill"
    ) -> str:
        """Generate transformed image URL.
        
        Args:
            public_id: Cloudinary public ID
            width: Optional width for transformation
            height: Optional height for transformation
            crop: Crop mode (fill, fit, scale, etc.)
            
        Returns:
            Transformed image URL
        """
        transformation = []
        
        if width or height:
            transform = {"crop": crop}
            if width:
                transform["width"] = width
            if height:
                transform["height"] = height
            transformation.append(transform)
        
        url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            transformation=transformation,
            secure=True
        )
        
        return url


def create_cloudinary_service(
    cloud_name: str,
    api_key: str,
    api_secret: str,
    max_file_size: Optional[int] = None
) -> CloudinaryService:
    """Factory function to create Cloudinary service instance.
    
    Args:
        cloud_name: Cloudinary cloud name
        api_key: Cloudinary API key
        api_secret: Cloudinary API secret
        max_file_size: Maximum file size in bytes (defaults to CloudinaryService.MAX_FILE_SIZE)
        
    Returns:
        CloudinaryService instance
    """
    return CloudinaryService(cloud_name, api_key, api_secret, max_file_size)
