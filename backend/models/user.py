from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# User Registration Model
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    dob: str
    state: str
    city: str
    pincode: str
    mode: Optional[str] = "user"  # user or admin

# User Login Model
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# User Response Model
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    mode: str
    created_at: Optional[datetime] = None

# User in Database (MongoDB Document)
class UserInDB(BaseModel):
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
