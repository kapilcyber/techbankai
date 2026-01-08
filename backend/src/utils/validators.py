"""Validation utilities."""
import re
from typing import Optional
from pydantic import EmailStr, ValidationError


def validate_email(email: str) -> bool:
    """Validate email format."""
    try:
        EmailStr._validate(email)
        return True
    except ValidationError:
        return False


def validate_file_type(filename: str, allowed_extensions: list) -> bool:
    """Validate file extension."""
    if not filename:
        return False
    ext = filename.lower().split('.')[-1]
    return ext in allowed_extensions


def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    """Validate file size in MB."""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength.
    Returns: (is_valid, error_message)
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if len(password) > 100:
        return False, "Password is too long"
    
    return True, None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove any path components
    filename = filename.split('/')[-1].split('\\')[-1]
    # Remove special characters except dots, dashes, underscores
    filename = re.sub(r'[^\w\s.-]', '', filename)
    return filename.strip()


def validate_file_signature(content: bytes, extension: str) -> bool:
    """
    Validate file magic numbers (signatures) for security.
    Ensures that a file's content matches its claimed extension.
    """
    if not content:
        return False
        
    ext = extension.lower().replace('.', '')
    
    # PDF Signature: %PDF- (hex: 25 50 44 46)
    if ext == 'pdf':
        return content.startswith(b'\x25\x50\x44\x46')
        
    # DOCX/Office Signature: PK.. (hex: 50 4B 03 04)
    # Note: Many formats use ZIP (DOCX, XLSX, JAR, etc.)
    if ext == 'docx':
        return content.startswith(b'\x50\x4B\x03\x04')
        
    # Add other signatures if needed
    return False

