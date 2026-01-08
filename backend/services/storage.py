import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile
from utils.validators import sanitize_filename, validate_file_size
from utils.logger import get_logger
from services.google_drive import upload_file_to_gdrive, USE_GOOGLE_DRIVE

logger = get_logger(__name__)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

class StorageService:
    """Unified storage service with Google Drive and local fallback"""
    
    @staticmethod
    async def upload(file: UploadFile, subfolder: str = "resumes") -> tuple[str, str]:
        """
        Upload file to storage (Google Drive if configured, otherwise local)
        Returns: (file_path, file_url)
        """
        # Read file content
        content = await file.read()
        
        # Validate file size
        if not validate_file_size(len(content), MAX_FILE_SIZE_MB):
            raise ValueError(f"File size exceeds {MAX_FILE_SIZE_MB}MB limit")
        
        # Try Google Drive first if enabled
        if USE_GOOGLE_DRIVE:
            try:
                original_filename = sanitize_filename(file.filename)
                file_id, web_view_link = await upload_file_to_gdrive(
                    content,
                    original_filename
                )
                logger.info(f"Uploaded to Google Drive: {web_view_link}")
                # Return Google Drive link as file_url, file_id as file_path for reference
                return file_id, web_view_link
            except Exception as e:
                logger.warning(f"Google Drive upload failed, falling back to local: {e}")
        
        # Fallback to local storage
        return await StorageService._save_local(file, content, subfolder)
    
    @staticmethod
    async def _save_local(file: UploadFile, content: bytes, subfolder: str) -> tuple[str, str]:
        """Save file to local disk"""
        try:
            # Create upload directory if it doesn't exist
            upload_path = Path(UPLOAD_DIR) / subfolder
            upload_path.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            original_filename = sanitize_filename(file.filename)
            file_extension = original_filename.split('.')[-1]
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = upload_path / unique_filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Generate file URL (relative path)
            file_url = f"/{UPLOAD_DIR}/{subfolder}/{unique_filename}"
            
            logger.info(f"Saved file locally: {file_path}")
            return str(file_path), file_url
        
        except Exception as e:
            logger.error(f"Failed to save file locally: {e}")
            raise

# Backward compatibility function
async def save_uploaded_file(file: UploadFile, subfolder: str = "resumes") -> tuple[str, str]:
    """Save uploaded file (uses StorageService)"""
    return await StorageService.upload(file, subfolder)

def delete_file(file_path: str) -> bool:
    """Delete file from disk"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        return False
