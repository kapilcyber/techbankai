"""User Pydantic schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# User Registration Model
class UserCreate(BaseModel):
    """User registration schema."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    dob: str
    state: str
    city: str
    pincode: str
    mode: Optional[str] = "user"  # user or admin
    employment_type: str = "Guest User"
    employee_id: Optional[str] = None
    ready_to_relocate: Optional[bool] = False
    preferred_location: Optional[str] = None
    notice_period: Optional[int] = 0


# User Login Model
class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str


# User Response Model
class UserResponse(BaseModel):
    """User response schema."""
    id: int
    name: str
    email: str
    mode: str
    employment_type: Optional[str] = None
    employee_id: Optional[str] = None
    freelancer_id: Optional[str] = None
    ready_to_relocate: Optional[bool] = False
    preferred_location: Optional[str] = None
    notice_period: Optional[int] = 0
    created_at: Optional[datetime] = None


# User in Database (MongoDB Document)
class UserInDB(BaseModel):
    """User database schema."""
    name: str
    email: str
    password_hash: str
    dob: str
    state: str
    city: str
    pincode: str
    mode: str = "user"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

