"""Resume Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ParsedResume(BaseModel):
    """Strict schema for AI-parsed resume data."""
    resume_candidate_name: str = Field(default="Not mentioned", description="Full name of the candidate")
    resume_contact_info: str = Field(default="Not mentioned", description="Email address only")
    resume_role: str = Field(default="Not mentioned", description="Current or most recent job role/position")
    resume_location: str = Field(default="Not mentioned", description="Location/address")
    resume_degree: str = Field(default="Not mentioned", description="Highest degree obtained")
    resume_university: str = Field(default="Not mentioned", description="University/institution name")
    resume_experience: float = Field(default=0.0, ge=0.0, description="Years of experience (calculated)")
    resume_technical_skills: List[str] = Field(default_factory=list, description="Technical skills list")
    resume_projects: List[str] = Field(default_factory=list, description="Projects mentioned")
    resume_achievements: List[str] = Field(default_factory=list, description="Achievements/awards")
    resume_certificates: List[str] = Field(default_factory=list, description="Certifications")
    all_skills: List[str] = Field(default_factory=list, description="All skills merged and deduplicated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "resume_candidate_name": "John Doe",
                "resume_contact_info": "john.doe@example.com",
                "resume_role": "Senior Software Engineer",
                "resume_location": "San Francisco, CA",
                "resume_degree": "Bachelor's in Computer Science",
                "resume_university": "MIT",
                "resume_experience": 5.5,
                "resume_technical_skills": ["Python", "JavaScript", "React"],
                "resume_projects": ["E-commerce Platform", "AI Chatbot"],
                "resume_achievements": ["Best Developer Award 2023"],
                "resume_certificates": ["AWS Certified Solutions Architect"],
                "all_skills": ["python", "javascript", "react", "aws"]
            }
        }


class ExperienceResponse(BaseModel):
    """Schema for individual work experience entry."""
    id: int
    company: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None

    class Config:
        from_attributes = True


class CertificationResponse(BaseModel):
    """Schema for individual certification entry."""
    id: int
    name: str
    issuer: Optional[str] = None
    date_obtained: Optional[str] = None
    expiry_date: Optional[str] = None

    class Config:
        from_attributes = True


class ResumeCreate(BaseModel):
    """Schema for creating a resume record."""
    filename: str
    file_url: str
    source_type: str = Field(..., description="Source type: company_employee, gmail, admin, freelancer, guest, hired_force")
    source_id: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = None
    parsed_data: Dict[str, Any]
    skills: List[str] = Field(default_factory=list)
    experience_years: float = 0.0
    uploaded_by: str
    meta_data: Optional[Dict[str, Any]] = None


class ResumeResponse(BaseModel):
    """Schema for resume API responses."""
    id: int
    filename: str
    file_url: str
    source_type: str
    user_type: Optional[str] = None
    source_id: Optional[str] = None
    name: str
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    role: Optional[str] = None
    skills: List[str]
    experience_years: float
    uploaded_at: datetime
    uploaded_by: str
    parsed_data: Dict[str, Any]
    meta_data: Optional[Dict[str, Any]] = None
    work_history: List[ExperienceResponse] = []
    certificates: List[CertificationResponse] = []
    
    class Config:
        from_attributes = True


class CompanyEmployeeUpload(BaseModel):
    """Schema for company employee upload request."""
    employee_id: str = Field(..., description="Unique employee ID")
    department: Optional[str] = None
    company_name: Optional[str] = None
    form_skills: Optional[str] = Field(None, description="Comma-separated skills from form")


class GmailResumeMetadata(BaseModel):
    """Schema for Gmail resume metadata."""
    message_id: str
    sender: str
    subject: str
    received_at: Optional[datetime] = None

