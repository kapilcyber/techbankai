"""Google Drive integration service."""
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from typing import Optional, Tuple
from src.utils.logger import get_logger
from src.config.settings import settings
import io

logger = get_logger(__name__)

# Google Drive API Configuration from settings
GOOGLE_DRIVE_CREDENTIALS_PATH = settings.google_drive_credentials_path
GOOGLE_DRIVE_FOLDER_ID = settings.google_drive_folder_id
USE_GOOGLE_DRIVE = settings.use_google_drive

_service = None


def get_google_drive_service():
    """Get or create Google Drive API service."""
    global _service
    if _service is None and USE_GOOGLE_DRIVE and GOOGLE_DRIVE_CREDENTIALS_PATH:
        try:
            if os.path.exists(GOOGLE_DRIVE_CREDENTIALS_PATH):
                credentials = service_account.Credentials.from_service_account_file(
                    GOOGLE_DRIVE_CREDENTIALS_PATH,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
                _service = build('drive', 'v3', credentials=credentials)
                logger.info("Google Drive service initialized")
            else:
                logger.warning(f"Google Drive credentials file not found: {GOOGLE_DRIVE_CREDENTIALS_PATH}")
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            _service = None
    return _service


async def upload_file_to_gdrive(
    file_bytes: bytes,
    filename: str,
    folder_id: Optional[str] = None
) -> Tuple[str, str]:
    """
    Upload file to Google Drive.
    Returns: (file_id, web_view_link)
    """
    service = get_google_drive_service()
    if not service:
        raise ValueError("Google Drive service not available")
    
    try:
        folder_id = folder_id or GOOGLE_DRIVE_FOLDER_ID
        
        file_metadata = {
            'name': filename
        }
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        media = MediaIoBaseUpload(
            io.BytesIO(file_bytes),
            mimetype='application/pdf' if filename.endswith('.pdf') else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = file.get('id')
        web_view_link = file.get('webViewLink')
        
        logger.info(f"Uploaded file to Google Drive: {filename} (file_id: {file_id})")
        return file_id, web_view_link
    
    except HttpError as e:
        logger.error(f"Google Drive upload error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading to Google Drive: {e}")
        raise


async def move_file_in_gdrive(
    file_id: str,
    destination_folder_id: str
) -> bool:
    """Move file to a different folder in Google Drive."""
    service = get_google_drive_service()
    if not service:
        raise ValueError("Google Drive service not available")
    
    try:
        # Get current parents
        file = service.files().get(
            fileId=file_id,
            fields='parents'
        ).execute()
        
        previous_parents = ",".join(file.get('parents', []))
        
        # Move file to new folder
        service.files().update(
            fileId=file_id,
            addParents=destination_folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        
        logger.info(f"Moved file {file_id} to folder {destination_folder_id}")
        return True
    
    except HttpError as e:
        logger.error(f"Google Drive move error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error moving file in Google Drive: {e}")
        return False


async def list_files_in_gdrive_folder(folder_id: str) -> list:
    """List all files in a Google Drive folder."""
    service = get_google_drive_service()
    if not service:
        raise ValueError("Google Drive service not available")
    
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, mimeType, createdTime)"
        ).execute()
        
        files = results.get('files', [])
        logger.info(f"Found {len(files)} files in folder {folder_id}")
        return files
    
    except HttpError as e:
        logger.error(f"Google Drive list error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error listing files in Google Drive: {e}")
        return []

