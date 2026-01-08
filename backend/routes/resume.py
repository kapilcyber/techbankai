from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Security, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_, func
from sqlalchemy.dialects.postgresql import ARRAY
from src.models.resume import Resume
from src.config.database import get_postgres_db
from src.middleware.auth_middleware import get_admin_user, get_current_user, decode_access_token, is_token_blacklisted
from src.services.storage import save_uploaded_file, delete_file
from src.services.resume_parser import parse_resume
from src.utils.validators import validate_file_type
from src.utils.logger import get_logger
from src.utils.response_formatter import format_resume_response, format_resume_list_response
from src.utils.user_type_mapper import normalize_user_type, get_source_type_from_user_type

security = HTTPBearer(auto_error=False)
logger = get_logger(__name__)
router = APIRouter(prefix="/api/resumes", tags=["Resumes"])

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

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Get current user if authenticated, otherwise return None"""
    # If no credentials provided, allow access (guest mode)
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        if not token:
            return None
        
        if await is_token_blacklisted(token, db):
            return None
        
        payload = decode_access_token(token)
        if payload is None:
            return None
        
        user_email = payload.get("sub")
        user_mode = payload.get("mode", "user")
        if user_email is None:
            return None
        
        return {
            "email": user_email,
            "mode": user_mode,
            "user_id": payload.get("user_id")
        }
    except Exception as e:
        # Log error but don't block access
        logger.debug(f"Optional auth error (allowing guest access): {e}")
        return None

@router.get("/search")
async def search_resumes(
    skills: str | None = Query(None, description="Comma-separated skills"),
    q: str | None = Query(None, description="Free-text search"),
    user_types: Optional[List[str]] = Query(None, description="Filter by user types"),
    min_experience: Optional[float] = Query(None, ge=0, description="Minimum years of experience"),
    locations: Optional[List[str]] = Query(None, description="Filter by locations"),
    roles: Optional[List[str]] = Query(None, description="Filter by roles"),
    current_user: Optional[dict] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Search resumes by skills, free-text query, and advanced filters"""
    try:
        import time
        start_time = time.time()
        
        query = select(Resume)
        skill_list = None
        
        # Filter by skills
        if skills:
            skill_list = [s.strip() for s in skills.split(',') if s.strip()]
            if skill_list:
                # For PostgreSQL ARRAY, convert to string and search (case-insensitive)
                # Handle NULL/empty arrays by using COALESCE
                for skill in skill_list:
                    # Use COALESCE to handle NULL arrays, convert to empty string if NULL
                    query = query.where(
                        func.lower(
                            func.coalesce(
                                func.array_to_string(Resume.skills, ','),
                                ''
                            )
                        ).like(f'%{skill.lower()}%')
                    )
        
        # Free-text search
        if q:
            like = f"%{q}%"
            query = query.where(
                or_(
                    Resume.raw_text.ilike(like),
                    Resume.filename.ilike(like)
                )
            )
        
        # Filter by user types
        if user_types:
            normalized_user_types = [normalize_user_type(ut) for ut in user_types]
            source_types = [get_source_type_from_user_type(ut) for ut in normalized_user_types]
            
            conditions = []
            for source_type in source_types:
                conditions.append(Resume.source_type == source_type)
            
            for user_type in normalized_user_types:
                # Use JSONB operator for meta_data.user_type (PostgreSQL -> operator)
                conditions.append(
                    Resume.meta_data['user_type'].astext == user_type
                )
            
            if conditions:
                query = query.where(or_(*conditions))
        
        # Filter by minimum experience
        if min_experience is not None:
            query = query.where(Resume.experience_years >= min_experience)
        
        # Execute query
        query = query.order_by(Resume.uploaded_at.desc()).limit(500)  # Increased limit for search
        result = await db.execute(query)
        results = result.scalars().all()
        
        # Apply client-side filters for locations and roles (JSONB filtering is complex)
        filtered_results = []
        for r in results:
            # Filter by locations
            if locations:
                parsed = r.parsed_data or {}
                location = parsed.get('resume_location', parsed.get('location', ''))
                if not location or location == 'Not mentioned':
                    continue
                if not any(loc.lower() in location.lower() for loc in locations):
                    continue
            
            # Filter by roles
            if roles:
                parsed = r.parsed_data or {}
                role = parsed.get('resume_role', parsed.get('role', ''))
                if not role or role == 'Not mentioned':
                    continue
                if not any(role_filter.lower() in role.lower() for role_filter in roles):
                    continue
            
            filtered_results.append(r)
        
        # Format responses
        formatted_resumes = [format_resume_response(r) for r in filtered_results]
        
        # Calculate matched skills for each resume
        for i, r in enumerate(filtered_results):
            if skill_list and r.skills:
                formatted_resumes[i]['matched_skills'] = list(set(r.skills) & set(skill_list))
            else:
                formatted_resumes[i]['matched_skills'] = []
        
        search_time = round((time.time() - start_time) * 1000, 2)  # milliseconds
        
        return {
            'total': len(formatted_resumes),
            'search_skills': skill_list or [],
            'query': q or "",
            'search_time_ms': search_time,
            'resumes': formatted_resumes
        }
    except Exception as e:
        logger.error(f"Search resumes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_resumes(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Upload multiple resume files (Admin only)
    Parses resumes and stores in database
    """
    try:
        uploaded_resumes = []
        errors = []
        
        for file in files:
            try:
                # Validate file type
                if not validate_file_type(file.filename, ALLOWED_EXTENSIONS):
                    errors.append(f"{file.filename}: Invalid file type. Only PDF and DOCX allowed.")
                    continue
                
                # Save file to disk
                file_path, file_url = await save_uploaded_file(file, subfolder="resumes")
                file_extension = file.filename.split('.')[-1]
                
                # Parse resume
                logger.info(f"Parsing resume: {file.filename}")
                parsed_data = await parse_resume(file_path, file_extension)
                
                # Clean null bytes from parsed data
                parsed_data = clean_dict_values(parsed_data)
                
                # Create resume record
                from src.utils.user_type_mapper import get_user_type_from_source_type
                resume = Resume(
                    filename=file.filename,
                    file_url=file_url,
                    source_type='admin',
                    source_id=None,
                    raw_text=clean_null_bytes(parsed_data.get('raw_text', '')),
                    parsed_data=parsed_data,
                    skills=parsed_data.get('resume_technical_skills', parsed_data.get('all_skills', [])),
                    experience_years=parsed_data.get('resume_experience', parsed_data.get('experience_years', 0)),
                    uploaded_by=current_user['email'],
                    meta_data={
                        'parsing_method': parsed_data.get('parsing_method', 'unknown'),
                        'file_size': file.size if hasattr(file, 'size') else 0,
                        'user_type': get_user_type_from_source_type('admin')  # Always set normalized user_type
                    }
                )
                
                db.add(resume)
                await db.commit()
                await db.refresh(resume)
                
                uploaded_resumes.append({
                    'id': resume.id,
                    'filename': resume.filename,
                    'candidate_name': parsed_data.get('resume_candidate_name', 'Unknown'),
                    'skills': resume.skills,
                    'experience_years': resume.experience_years
                })
                
                logger.info(f"Successfully uploaded resume: {file.filename}")
            
            except Exception as e:
                logger.error(f"Failed to process {file.filename}: {e}")
                errors.append(f"{file.filename}: {str(e)}")
        
        return {
            'success': len(uploaded_resumes),
            'failed': len(errors),
            'uploaded_resumes': uploaded_resumes,
            'errors': errors
        }
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def list_resumes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=5000),  # Increased max limit for dashboard
    user_types: Optional[List[str]] = Query(None, description="Filter by user types (Guest, Company Employee, Freelancer, Hired Force, Admin Uploads)"),
    current_user: Optional[dict] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """List all resumes with pagination and optional user type filtering"""
    try:
        # Build base query
        query = select(Resume)
        count_query = select(func.count(Resume.id))
        
        # Filter by user types if provided
        if user_types:
            # Normalize user types
            normalized_user_types = [normalize_user_type(ut) for ut in user_types]
            # Convert to source_types for filtering
            source_types = [get_source_type_from_user_type(ut) for ut in normalized_user_types]
            
            # Filter by source_type or meta_data.user_type
            conditions = []
            for source_type in source_types:
                conditions.append(Resume.source_type == source_type)
            
            # Also check meta_data.user_type for backward compatibility
            for user_type in normalized_user_types:
                # Use JSONB operator for meta_data.user_type (PostgreSQL -> operator)
                conditions.append(
                    Resume.meta_data['user_type'].astext == user_type
                )
            
            if conditions:
                query = query.where(or_(*conditions))
                count_query = count_query.where(or_(*conditions))
        
        # Count total
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # Get resumes
        query = query.order_by(Resume.uploaded_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        resumes = result.scalars().all()
        
        # Format responses
        return format_resume_list_response(resumes, total, skip, limit)
    
    except Exception as e:
        logger.error(f"List resumes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{resume_id}")
async def get_resume(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Get specific resume details"""
    try:
        query = select(Resume).where(Resume.id == resume_id)
        result = await db.execute(query)
        resume = result.scalar_one_or_none()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Format response using formatter
        response = format_resume_response(resume)
        # Add raw_text preview
        response['raw_text'] = resume.raw_text[:500] + '...' if resume.raw_text and len(resume.raw_text) > 500 else resume.raw_text
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get resume error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Delete resume (Admin only)"""
    try:
        query = select(Resume).where(Resume.id == resume_id)
        result = await db.execute(query)
        resume = result.scalar_one_or_none()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Delete file from disk
        file_path = resume.file_url.replace('/', '\\').lstrip('\\')
        delete_file(file_path)
        
        # Delete from database
        await db.execute(delete(Resume).where(Resume.id == resume_id))
        await db.commit()
        
        logger.info(f"Deleted resume: {resume_id}")
        return {"message": "Resume deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete resume error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/by-skills")
async def search_resumes_by_skills(
    skills: str = Query(..., description="Comma-separated skills"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Search resumes by skills"""
    try:
        skill_list = [s.strip() for s in skills.split(',')]
        
        # Query resumes that have any of the specified skills
        # Use array_to_string for PostgreSQL ARRAY search (case-insensitive)
        # Handle NULL/empty arrays by using COALESCE
        query = select(Resume)
        for skill in skill_list:
            query = query.where(
                func.lower(
                    func.coalesce(
                        func.array_to_string(Resume.skills, ','),
                        ''
                    )
                ).like(f'%{skill.lower()}%')
            )
        query = query.order_by(Resume.uploaded_at.desc())
        result = await db.execute(query)
        resumes = result.scalars().all()
        
        return {
            'total': len(resumes),
            'search_skills': skill_list,
            'resumes': [
                {
                    'id': r.id,
                    'filename': r.filename,
                    'candidate_name': r.parsed_data.get('resume_candidate_name', r.parsed_data.get('name', 'Unknown')) if r.parsed_data else 'Unknown',
                    'email': r.parsed_data.get('resume_contact_info', r.parsed_data.get('email', '')) if r.parsed_data else '',
                    'skills': r.skills,
                    'matched_skills': list(set(r.skills or []) & set(skill_list)),
                    'experience_years': r.experience_years,
                    'file_url': r.file_url
                }
                for r in resumes
            ]
        }
    
    except Exception as e:
        logger.error(f"Search resumes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/user-profile")
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
        
        # Map user type to source_type
        source_type_map = {
            'Guest User': 'guest',
            'Guest': 'guest',
            'Hired Forces': 'hired_force',
            'Hired Force': 'hired_force',
            'Company Employee': 'company_employee',
            'Freelancer': 'freelancer'
        }
        source_type = source_type_map.get(userType, 'guest')
        
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
                'user_type': userType or 'Guest',
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
