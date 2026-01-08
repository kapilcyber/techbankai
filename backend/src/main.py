"""Main FastAPI application entry point."""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from starlette.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Load environment variables
load_dotenv()

# Import database config
from src.config.database import init_postgres_db
from src.config.settings import settings

# Import routes
from src.routes import auth, resume, jd_analysis, admin
from src.routes.resumes import company, admin as resume_admin, user_profile, gmail
from src.routes import user_profile_api

# Import logger and middleware
from src.utils.logger import get_logger
from src.middleware.error_middleware import TraceIDMiddleware, create_error_response

logger = get_logger(__name__)

# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting TechBank.ai Backend...")
    
    # Initialize PostgreSQL tables (includes users, resumes, jd_analysis, etc.)
    await init_postgres_db()
    
    logger.info("PostgreSQL database initialized")
    logger.info(f"Server running on http://{settings.host}:{settings.port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down TechBank.ai Backend...")
    logger.info("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="TechBank.ai API",
    description="AI-Powered Resume Management and JD Analysis System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
# Use allow_origin_regex to allow all origins WITH credentials
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",  # Allows all origins
    allow_credentials=True,   # Allows cookies and auth headers
    allow_methods=["*"],      # Allows all methods
    allow_headers=["*"],      # Allows all headers
    max_age=3600,
)

# Add trace ID middleware after CORS
app.add_middleware(TraceIDMiddleware)

# Mount static files (for serving uploaded files)
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(resume.router)  # Main resume routes (search, list, get, delete)
app.include_router(company.router)  # Company employee uploads
app.include_router(resume_admin.router)  # Admin bulk uploads
app.include_router(user_profile.router)  # User profile uploads
app.include_router(gmail.router)  # Gmail webhook
app.include_router(jd_analysis.router)
app.include_router(admin.router)
app.include_router(user_profile_api.router)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    trace_id = getattr(request.state, 'trace_id', 'N/A')
    logger.info(f"{request.method} {request.url.path} [Trace: {trace_id}]")
    try:
        response = await call_next(request)
        logger.info(f"Completed {request.method} {request.url.path} -> {response.status_code} [Trace: {trace_id}]")
        return response
    except Exception as e:
        logger.error(f"Error handling {request.method} {request.url.path} [Trace: {trace_id}]: {e}")
        raise


# Centralized exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    trace_id = getattr(request.state, 'trace_id', None)
    return create_error_response(
        status_code=exc.status_code,
        message=exc.detail or "HTTP error",
        trace_id=trace_id
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, 'trace_id', None)
    logger.error(f"Unhandled error on {request.url.path} [Trace: {trace_id}]: {exc}")
    return create_error_response(
        status_code=500,
        message="Internal server error",
        trace_id=trace_id
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "TechBank.ai Backend",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to TechBank.ai API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "User Authentication (JWT)",
            "Resume Upload & Parsing (AI-Powered)",
            "JD Analysis & Matching (GPT-4)",
            "Intelligent Candidate Scoring",
            "Admin Dashboard"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,  # Enabled for dev
        log_level="info"
    )

