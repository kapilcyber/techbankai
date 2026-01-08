from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from config.database import Base

class JDAnalysis(Base):
    __tablename__ = "jd_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, nullable=False, index=True)
    jd_filename = Column(String(255))
    jd_text = Column(Text)
    extracted_keywords = Column(ARRAY(String))
    required_skills = Column(ARRAY(String))
    preferred_skills = Column(ARRAY(String))
    required_experience = Column(Float)
    education = Column(String(500))
    job_level = Column(String(50))  # entry, mid, senior
    submitted_at = Column(DateTime, default=datetime.utcnow)
    submitted_by = Column(String(100))  # Admin email
    
    def __repr__(self):
        return f"<JDAnalysis(job_id='{self.job_id}')>"


class MatchResult(Base):
    __tablename__ = "match_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), ForeignKey('jd_analysis.job_id'), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'), nullable=False)
    source_type = Column(String(50), nullable=True, index=True)  # Track resume source type
    source_id = Column(String(100), nullable=True)  # Track resume source ID
    match_score = Column(Float)  # Overall score 0-100
    skill_match_score = Column(Float)
    experience_match_score = Column(Float)
    semantic_score = Column(Float)  # AI semantic matching score
    keyword_matches = Column(JSONB)  # Detailed match information
    match_explanation = Column(Text)  # AI-generated explanation
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MatchResult(job_id='{self.job_id}', resume_id={self.resume_id}, score={self.match_score})>"
