"""Token Blacklist SQLAlchemy model."""
from sqlalchemy import Column, Integer, String, DateTime, Index
from datetime import datetime
from src.config.database import Base


class TokenBlacklist(Base):
    """Token Blacklist database model."""
    __tablename__ = "token_blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TokenBlacklist(id={self.id}, token='{self.token[:20]}...')>"

