from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ARRAY, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from config.database import Base

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Polymorphic source identification
    source_type = Column(String(50), nullable=False, index=True)  # 'company_employee', 'gmail', 'admin', 'freelancer', 'guest', 'hired_force'
    source_id = Column(String(100), nullable=True)  # employee_id, message_id, etc.
    source_metadata = Column(JSONB)  # Source-specific metadata (employee_id, department, gmail metadata, etc.)
    
    # Common resume fields
    filename = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    raw_text = Column(Text)  # Extracted text from PDF/DOC
    parsed_data = Column(JSONB)  # Structured data: name, email, phone, skills, etc.
    skills = Column(ARRAY(String))  # Array of extracted skills
    experience_years = Column(Float)  # Years of experience
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String(100))  # Admin email who uploaded
    meta_data = Column(JSONB)  # Additional metadata (renamed from 'metadata' - reserved in SQLAlchemy)
    
    # Unique constraint: (source_type, source_id) for idempotent uploads
    __table_args__ = (
        UniqueConstraint('source_type', 'source_id', name='uq_resume_source'),
    )
    
    def ensure_user_type(self):
        """Ensure meta_data.user_type is set from source_type if missing"""
        if not self.meta_data:
            self.meta_data = {}
        
        if 'user_type' not in self.meta_data or not self.meta_data.get('user_type'):
            # Import here to avoid circular dependency
            from utils.user_type_mapper import get_user_type_from_source_type
            self.meta_data['user_type'] = get_user_type_from_source_type(self.source_type)
    
    def get_user_type(self):
        """Get normalized user_type from meta_data or derive from source_type"""
        if self.meta_data and self.meta_data.get('user_type'):
            from utils.user_type_mapper import normalize_user_type
            return normalize_user_type(self.meta_data['user_type'])
        else:
            from utils.user_type_mapper import get_user_type_from_source_type
            return get_user_type_from_source_type(self.source_type)
    
    def __repr__(self):
        return f"<Resume(id={self.id}, source_type='{self.source_type}', filename='{self.filename}')>"
