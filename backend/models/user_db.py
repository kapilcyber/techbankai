from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from config.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    dob = Column(String(50))
    state = Column(String(100))
    city = Column(String(100))
    pincode = Column(String(10))
    mode = Column(String(20), default="user")  # user or admin
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

