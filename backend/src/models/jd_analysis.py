"""JD Analysis SQLAlchemy models."""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from src.config.database import Base


class JDAnalysis(Base):
    """Job Description Analysis database model."""
    __tablename__ = "jd_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, nullable=False, index=True)
    jd_filename = Column(String(255))
    jd_text = Column(Text)
    extracted_keywords = Column(ARRAY(String))
    required_skills = Column(ARRAY(String))
    preferred_skills = Column(ARRAY(String))
    required_experience = Column(Float, default=0.0)
    education = Column(String(500))
    job_level = Column(String(50))  # entry, mid, senior
    submitted_at = Column(DateTime, default=datetime.utcnow, index=True)
    submitted_by = Column(String(100))  # Admin email
    
    def __repr__(self):
        return f"<JDAnalysis(job_id='{self.job_id}')>"


class MatchResult(Base):
    """Match Result database model."""
    __tablename__ = "match_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), ForeignKey('jd_analysis.job_id', ondelete='CASCADE'), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False, index=True)
    source_type = Column(String(50), nullable=True, index=True)  # Track resume source type
    source_id = Column(String(100), nullable=True)  # Track resume source ID
    match_score = Column(Float)  # Overall score 0-100 (will be replaced by universal_fit_score)
    skill_match_score = Column(Float)  # Legacy - maps to skill_evidence_score
    experience_match_score = Column(Float)  # Legacy - maps to execution_score
    semantic_score = Column(Float)  # Legacy - maps to complexity_score
    keyword_matches = Column(JSONB)  # Detailed match information
    match_explanation = Column(Text)  # AI-generated explanation
    
    # Universal Fit Score - 6 Factor Breakdown
    universal_fit_score = Column(Float, default=0.0)  # Weighted total (0-100)
    skill_evidence_score = Column(Float, default=0.0)  # 35% - Technical skills + depth
    execution_score = Column(Float, default=0.0)  # 25% - Project complexity, leadership, impact
    complexity_score = Column(Float, default=0.0)  # 15% - Problem-solving sophistication
    learning_agility_score = Column(Float, default=0.0)  # 10% - Adaptability, continuous learning
    domain_context_score = Column(Float, default=0.0)  # 10% - Industry/domain relevance
    communication_score = Column(Float, default=0.0)  # 5% - Resume quality, clarity
    factor_breakdown = Column(JSONB, nullable=True)  # Detailed reasoning per factor
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MatchResult(job_id='{self.job_id}', resume_id={self.resume_id}, score={self.match_score})>"

