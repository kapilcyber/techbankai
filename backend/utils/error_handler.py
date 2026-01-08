"""Error handling utilities for consistent error responses"""

from typing import Dict, Any, Optional


def format_error_response(status_code: int, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format error response for frontend"""
    return {
        'error': True,
        'status_code': status_code,
        'message': message,
        'details': details or {}
    }


def format_validation_error(field: str, message: str) -> Dict[str, Any]:
    """Format validation error response"""
    return format_error_response(
        status_code=422,
        message=f"Validation error: {message}",
        details={'field': field}
    )


def format_not_found_error(resource: str, identifier: Any = None) -> Dict[str, Any]:
    """Format not found error response"""
    message = f"{resource} not found"
    if identifier:
        message += f" with id: {identifier}"
    return format_error_response(
        status_code=404,
        message=message,
        details={'resource': resource, 'identifier': identifier}
    )


