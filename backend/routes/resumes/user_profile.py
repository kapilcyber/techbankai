from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from src.models.resume import Resume
from src.config.database import get_postgres_db
from src.middleware.auth_middleware import decode_access_token
from src.services.storage import save_uploaded_file
from src.services.resume_parser import parse_resume
from src.utils.validators import validate_file_type
from src.utils.logger import get_logger
from src.utils.user_type_mapper import normalize_user_type, get_source_type_from_user_type

security = HTTPBearer(auto_error=False)
logger = get_logger(__name__)
router = APIRouter(prefix="/api/resumes/upload", tags=["User Profile Resumes"])

ALLOWED_EXTENSIONS = ['pdf', 'docx']

def clean_null_bytes(text: str) -> str:
    """Remove null bytes from text to prevent PostgreSQL errors"""
    if text is None:
        return ""
    if isinstance(text, str):
        return text.replace('\x00', '').replace('\0', '')
    return str(text).replace('\x00', '').replace('\0', '')

def clean_dict_values(data: dict) -> dict:
    """Recursively clean null bytes from dictionary values"""
    if not isinstance(data, dict):
        return data
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, str):
            cleaned[key] = clean_null_bytes(value)
        elif isinstance(value, dict):
            cleaned[key] = clean_dict_values(value)
        elif isinstance(value, list):
            cleaned[key] = [clean_null_bytes(str(v)) if isinstance(v, str) else v for v in value]
        else:
            cleaned[key] = value
    return cleaned

@router.post("/user-profile")
async def upload_user_profile_resume(
    file: UploadFile = File(...),
    userType: str = Form(None),
    fullName: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Upload resume with user profile data (for regular users)
    Works with or without authentication (for guest users)
    Stores resume in PostgreSQL and profile data in metadata
    """
    try:
        # Get user email from token if authenticated, otherwise use provided email
        user_email = None
        if credentials:
            payload = decode_access_token(credentials.credentials)
            if payload:
                user_email = payload.get('sub')
        
        # Use provided email or authenticated user email
        uploader_email = email or user_email or 'guest@unknown.com'
        
        # Normalize user type and map to source_type
        normalized_user_type = normalize_user_type(userType) if userType else 'Guest'
        source_type = get_source_type_from_user_type(normalized_user_type)
        
        # Validate file type
        if not validate_file_type(file.filename, ALLOWED_EXTENSIONS):
            raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and DOCX allowed.")
        
        # Save file to disk
        file_path, file_url = await save_uploaded_file(file, subfolder="resumes")
        file_extension = file.filename.split('.')[-1]
        
        # Prepare form data for parser
        form_data = {
            'fullName': fullName,
            'email': email,
            'phone': phone
        }
        
        # Parse resume
        logger.info(f"Parsing user resume: {file.filename}")
        parsed_data = await parse_resume(file_path, file_extension, form_data=form_data)
        
        # Clean null bytes from parsed data
        parsed_data = clean_dict_values(parsed_data)
        
        # Create resume record with user profile metadata
        resume = Resume(
            filename=file.filename,
            file_url=file_url,
            source_type=source_type,
            source_id=None,  # Can be set if we have unique identifier
            source_metadata={
                'user_type': userType,
                'form_data': {
                    'fullName': clean_null_bytes(fullName) if fullName else None,
                    'email': clean_null_bytes(email) if email else uploader_email,
                    'phone': clean_null_bytes(phone) if phone else None
                }
            },
            raw_text=clean_null_bytes(parsed_data.get('raw_text', '')),
            parsed_data=parsed_data,
            skills=parsed_data.get('all_skills', parsed_data.get('resume_technical_skills', [])),
            experience_years=parsed_data.get('resume_experience', 0),
            uploaded_by=uploader_email,
            meta_data={
                'parsing_method': parsed_data.get('parsing_method', 'unknown'),
                'file_size': file.size if hasattr(file, 'size') else 0,
                'user_type': normalized_user_type,  # Always use normalized user_type
                'user_profile': {
                    'fullName': clean_null_bytes(fullName) if fullName else None,
                    'email': clean_null_bytes(email) if email else uploader_email,
                    'phone': clean_null_bytes(phone) if phone else None
                }
            }
        )
        
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        
        logger.info(f"Successfully uploaded user profile resume: {file.filename}")
        
        return {
            'success': True,
            'message': 'Resume uploaded successfully',
            'resume_id': resume.id,
            'filename': resume.filename,
            'candidate_name': parsed_data.get('resume_candidate_name', 'Unknown'),
            'skills': resume.skills
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload user profile resume error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


