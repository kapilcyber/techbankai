from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from src.models.resume import Resume
from src.config.database import get_postgres_db
from src.middleware.auth_middleware import get_admin_user
from src.services.storage import save_uploaded_file
from src.services.resume_parser import parse_resume, merge_skills
from src.utils.validators import validate_file_type
from src.utils.logger import get_logger
from src.utils.user_type_mapper import get_user_type_from_source_type
from src.utils.resume_processor import save_structured_resume_data

logger = get_logger(__name__)
router = APIRouter(prefix="/api/resumes/company", tags=["Company Employee Resumes"])

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

@router.post("")
async def upload_company_employee_resume(
    file: UploadFile = File(...),
    employee_id: str = Form(..., description="Unique employee ID"),
    department: str = Form(None),
    company_name: str = Form(None),
    form_skills: str = Form(None, description="Comma-separated skills from form"),
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Upload company employee resume with upsert capability
    If employee_id already exists, updates the existing record
    """
    try:
        # Validate file type
        if not validate_file_type(file.filename, ALLOWED_EXTENSIONS):
            raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and DOCX allowed.")
        
        # Save file to disk (or Google Drive if configured)
        file_path, file_url = await save_uploaded_file(file, subfolder="resumes")
        file_extension = file.filename.split('.')[-1]
        
        # Prepare form data for parser
        form_data = {
            'form_skills': form_skills
        }
        
        # Parse resume
        logger.info(f"Parsing company employee resume: {file.filename} (employee_id: {employee_id})")
        parsed_data = await parse_resume(file_path, file_extension, form_data=form_data)
        
        # Clean null bytes from parsed data
        parsed_data = clean_dict_values(parsed_data)
        
        # Merge form skills with resume skills
        resume_skills = parsed_data.get('resume_technical_skills', [])
        all_skills = merge_skills(resume_skills, form_skills) if form_skills else resume_skills
        parsed_data['all_skills'] = all_skills
        
        # Check if resume with this employee_id already exists (upsert)
        query = select(Resume).where(
            Resume.source_type == 'company_employee',
            Resume.source_id == employee_id
        )
        result = await db.execute(query)
        existing_resume = result.scalar_one_or_none()
        
        if existing_resume:
            # Update existing record
            existing_resume.filename = file.filename
            existing_resume.file_url = file_url
            existing_resume.raw_text = clean_null_bytes(parsed_data.get('raw_text', ''))
            existing_resume.parsed_data = parsed_data
            existing_resume.skills = all_skills
            existing_resume.experience_years = parsed_data.get('resume_experience', 0)
            existing_resume.source_metadata = {
                'employee_id': employee_id,
                'department': clean_null_bytes(department) if department else None,
                'company_name': clean_null_bytes(company_name) if company_name else None
            }
            existing_resume.uploaded_by = current_user['email']
            existing_resume.meta_data = {
                'parsing_method': parsed_data.get('parsing_method', 'unknown'),
                'file_size': file.size if hasattr(file, 'size') else 0,
                'updated_at': str(datetime.utcnow()),
                'user_type': get_user_type_from_source_type('company_employee')  # Always set normalized user_type
            }
            
            await db.commit()
            await db.refresh(existing_resume)
            
            # Update structured child records
            await save_structured_resume_data(db, existing_resume.id, parsed_data, clear_existing=True)
            await db.commit()
            
            logger.info(f"Updated existing company employee resume: {employee_id}")
            
            return {
                'success': True,
                'message': 'Resume updated successfully',
                'resume_id': existing_resume.id,
                'filename': existing_resume.filename,
                'candidate_name': parsed_data.get('resume_candidate_name', 'Unknown'),
                'skills': existing_resume.skills,
                'updated': True
            }
        else:
            # Create new record
            resume = Resume(
                filename=file.filename,
                file_url=file_url,
                source_type='company_employee',
                source_id=employee_id,
                source_metadata={
                    'employee_id': employee_id,
                    'department': clean_null_bytes(department) if department else None,
                    'company_name': clean_null_bytes(company_name) if company_name else None
                },
                raw_text=clean_null_bytes(parsed_data.get('raw_text', '')),
                parsed_data=parsed_data,
                skills=all_skills,
                experience_years=parsed_data.get('resume_experience', 0),
                uploaded_by=current_user['email'],
                meta_data={
                    'parsing_method': parsed_data.get('parsing_method', 'unknown'),
                    'file_size': file.size if hasattr(file, 'size') else 0,
                    'user_type': get_user_type_from_source_type('company_employee')  # Always set normalized user_type
                }
            )
            
            db.add(resume)
            await db.commit()
            await db.refresh(resume)
            
            # Save structured child records
            await save_structured_resume_data(db, resume.id, parsed_data)
            await db.commit()
            
            logger.info(f"Successfully uploaded company employee resume: {employee_id}")
            
            return {
                'success': True,
                'message': 'Resume uploaded successfully',
                'resume_id': resume.id,
                'filename': resume.filename,
                'candidate_name': parsed_data.get('resume_candidate_name', 'Unknown'),
                'skills': resume.skills,
                'updated': False
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload company employee resume error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

