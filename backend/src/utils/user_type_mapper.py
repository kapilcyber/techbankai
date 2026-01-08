"""User type mapping utilities for source_type and user_type conversion."""

# Mapping from source_type to user_type (for frontend display)
SOURCE_TO_USER_TYPE = {
    'company_employee': 'Company Employee',
    'freelancer': 'Freelancer',
    'guest': 'Guest User',
    'admin': 'Admin Uploads',
    'gmail': 'Gmail Resume'
}

# Reverse mapping from user_type to source_type
USER_TYPE_TO_SOURCE = {v: k for k, v in SOURCE_TO_USER_TYPE.items()}


def normalize_user_type(user_type: str) -> str:
    """Normalize user type names for consistency."""
    if not user_type:
        return 'Admin Uploads'
    
    normalization_map = {
        'Guest': 'Guest User',
        'Guest User': 'Guest User',
        'Company Employee': 'Company Employee',
        'Freelancer': 'Freelancer',
        'Admin Uploads': 'Admin Uploads',
        'Admin': 'Admin Uploads',
        'Gmail Resume': 'Gmail Resume'
    }
    return normalization_map.get(user_type, user_type)


def get_source_type_from_user_type(user_type: str) -> str:
    """Convert normalized user_type to source_type."""
    normalized = normalize_user_type(user_type)
    return USER_TYPE_TO_SOURCE.get(normalized, 'admin')


def get_user_type_from_source_type(source_type: str) -> str:
    """Convert source_type to normalized user_type."""
    return SOURCE_TO_USER_TYPE.get(source_type, 'Admin Uploads')

