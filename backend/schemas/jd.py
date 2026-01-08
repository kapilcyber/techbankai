from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class JDRequirements(BaseModel):
    """Schema for extracted JD requirements"""
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_experience_years: float = Field(default=0.0, ge=0.0)
    education: str = Field(default="Not mentioned")
    keywords: List[str] = Field(default_factory=list)
    job_level: str = Field(default="Not mentioned", description="entry, mid, senior")
    key_responsibilities: List[str] = Field(default_factory=list)

class JDAnalysisCreate(BaseModel):
    """Schema for creating JD analysis"""
    jd_filename: str
    jd_text: str
    extracted_keywords: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    required_experience: float = 0.0
    education: str = ""
    job_level: str = ""
    submitted_by: str

class MatchResultResponse(BaseModel):
    """Schema for match result response"""
    resume_id: int
    source_type: str
    source_id: Optional[str]
    candidate_name: str
    match_score: float
    skill_match_score: float
    experience_match_score: float
    semantic_score: float
    match_explanation: str
    keyword_matches: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


