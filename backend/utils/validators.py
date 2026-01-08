import re
from typing import Optional
from pydantic import EmailStr, ValidationError

def validate_email(email: str) -> bool:
    """Validate email format"""
    try:
        EmailStr._validate(email)
        return True
    except ValidationError:
        return False

def validate_file_type(filename: str, allowed_extensions: list) -> bool:
    """Validate file extension"""
    if not filename:
        return False
    ext = filename.lower().split('.')[-1]
    return ext in allowed_extensions

def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    """Validate file size in MB"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if len(password) > 100:
        return False, "Password is too long"
    
    return True, None

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal"""
    # Remove any path components
    filename = filename.split('/')[-1].split('\\')[-1]
    # Remove special characters except dots, dashes, underscores
    filename = re.sub(r'[^\w\s.-]', '', filename)
    return filename.strip()
