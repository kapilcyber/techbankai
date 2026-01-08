"""Response formatting utilities for consistent API responses"""

from typing import Dict, Any, Optional
from models.resume import Resume


def map_source_type_to_user_type(source_type: str) -> str:
    """Map source_type to frontend user_type"""
    mapping = {
        'company_employee': 'Company Employee',
        'freelancer': 'Freelancer',
        'guest': 'Guest',
        'hired_force': 'Hired Force',
        'admin': 'Admin Uploads',
        'gmail': 'Gmail Resume'
    }
    return mapping.get(source_type, 'Admin Uploads')


def format_resume_response(resume: Resume) -> Dict[str, Any]:
    """Format resume for frontend consumption"""
    parsed = resume.parsed_data or {}
    meta = resume.meta_data or {}
    
    # Normalize user_type for frontend
    # First check if meta_data has user_type, otherwise derive from source_type
    user_type = meta.get('user_type')
    if not user_type:
        user_type = map_source_type_to_user_type(resume.source_type)
    
    # Ensure meta_data always has user_type
    formatted_meta = {
        **meta,
        'user_type': user_type
    }
    
    return {
        'id': resume.id,
        'filename': resume.filename,
        'file_url': resume.file_url,
        'source_type': resume.source_type,
        'source_id': resume.source_id,
        'parsed_data': parsed,
        'meta_data': formatted_meta,
        'skills': resume.skills or [],
        'experience_years': resume.experience_years or 0.0,
        'uploaded_at': resume.uploaded_at.isoformat() if resume.uploaded_at else None,
        'uploaded_by': resume.uploaded_by
    }


def format_resume_list_response(resumes: list, total: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Format list of resumes with pagination metadata"""
    return {
        'resumes': [format_resume_response(resume) for resume in resumes],
        'total': total,
        'skip': skip,
        'limit': limit,
        'count': len(resumes)
    }


