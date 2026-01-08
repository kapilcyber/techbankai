"""Enhanced error handling middleware with trace IDs."""
import uuid
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add trace IDs to requests for better error tracking."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Add trace ID to request and response."""
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        
        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response


def create_error_response(
    status_code: int,
    message: str,
    trace_id: str = None,
    details: dict = None
) -> JSONResponse:
    """Create structured error response with trace ID."""
    error_data = {
        "error": True,
        "status_code": status_code,
        "message": message,
    }
    
    if trace_id:
        error_data["trace_id"] = trace_id
    
    if details:
        error_data["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )

