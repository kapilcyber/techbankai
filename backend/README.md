# TechBank.ai Backend - Python FastAPI

AI-Powered Resume Management and Job Description Analysis System

## Features

✅ **User Authentication** - JWT-based authentication with role-based access (user/admin)  
✅ **Resume Upload & Parsing** - AI-powered resume parsing using GPT-4  
✅ **JD Analysis** - Intelligent job description analysis and keyword extraction  
✅ **Smart Matching** - Hybrid matching algorithm (Traditional + AI semantic matching)  
✅ **Candidate Scoring** - Score candidates 0-100 based on skills, experience, and semantic fit  
✅ **Admin Dashboard** - Statistics, user management, and bulk operations  

## Tech Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - All data storage (users, resumes, JD analysis)
- **OpenAI GPT-4** - AI-powered parsing and matching
- **JWT** - Secure authentication
- **SQLAlchemy** - PostgreSQL ORM
- **Pydantic** - Data validation

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (running on localhost:5432)
- OpenAI API Key

## Installation

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create `.env` file in `backend/` directory:

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=techbank
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Server
HOST=0.0.0.0
PORT=8000

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OpenAI
OPENAI_API_KEY=your-openai-api-key
```

### 4. Setup Database

**Using Docker:**
```bash
docker-compose up -d postgres
```

**Local PostgreSQL:**
```sql
CREATE DATABASE techbank;
```

### 5. Run the Server

```bash
python -m src.main
```

Or using uvicorn directly:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Server will start on: **http://localhost:8000**

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - Logout

### Resume Management
- `POST /api/resumes/upload` - Upload resumes (Admin only)
- `POST /api/resumes/upload/user-profile` - Upload user profile resume
- `GET /api/resumes` - List all resumes
- `GET /api/resumes/{id}` - Get resume details
- `DELETE /api/resumes/{id}` - Delete resume (Admin only)
- `GET /api/resumes/search/by-skills` - Search by skills

### JD Analysis (Core Feature)
- `POST /api/jd/analyze` - Upload JD and get top matches
- `GET /api/jd/results/{job_id}` - Get saved results
- `GET /api/jd/history` - Get analysis history

### Admin
- `GET /api/admin/stats` - Dashboard statistics
- `GET /api/admin/users` - List all users
- `DELETE /api/admin/users/{id}` - Delete user

## Project Structure

```
backend/
├── src/                       # Main source code (package-safe imports)
│   ├── main.py                # Main FastAPI application
│   ├── config/
│   │   ├── database.py        # PostgreSQL connection & initialization
│   │   ├── settings.py        # Centralized settings (Pydantic)
│   │   └── celery_config.py   # Celery configuration
│   ├── models/
│   │   ├── user_db.py         # User model (PostgreSQL)
│   │   ├── token_blacklist.py # JWT blacklist model
│   │   ├── resume.py          # Resume model
│   │   ├── jd_analysis.py     # JD analysis models
│   │   └── user.py            # Pydantic schemas
│   ├── routes/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── resume.py          # Resume endpoints
│   │   ├── jd_analysis.py     # JD analysis endpoints
│   │   ├── admin.py           # Admin endpoints
│   │   └── resumes/           # Resume sub-routes
│   │       ├── company.py
│   │       ├── admin.py
│   │       ├── user_profile.py
│   │       └── gmail.py
│   ├── services/
│   │   ├── openai_service.py  # OpenAI GPT-4 integration
│   │   ├── resume_parser.py    # Resume parsing
│   │   ├── jd_extractor.py    # JD extraction
│   │   ├── matching_engine.py # Candidate matching
│   │   ├── file_processor.py  # File handling
│   │   ├── storage.py          # File storage
│   │   └── google_drive.py     # Google Drive integration
│   ├── middleware/
│   │   ├── auth_middleware.py  # JWT authentication
│   │   └── error_middleware.py # Error handling with trace IDs
│   ├── utils/
│   │   ├── logger.py          # Logging config
│   │   ├── validators.py       # Input validation
│   │   ├── error_handler.py    # Error formatting
│   │   ├── response_formatter.py # Response formatting
│   │   └── user_type_mapper.py # User type mapping
│   ├── workers/
│   │   ├── celery_app.py      # Celery configuration
│   │   └── tasks.py            # Background tasks
│   └── migrations/             # Migration scripts
├── tests/                      # Test suite
│   ├── conftest.py            # Pytest configuration
│   ├── test_auth.py           # Auth tests
│   └── test_resume.py         # Resume tests
├── alembic/                    # Database migrations (Alembic)
│   ├── versions/              # Migration versions
│   └── env.py                 # Alembic environment
├── uploads/                    # File storage
│   ├── resumes/
│   └── jd/
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
└── .env.example                # Environment variables template
```

## Import Patterns

All imports use the `src.` prefix for package-safe imports:

```python
from src.models.user import User
from src.config.database import get_postgres_db
from src.services.resume_parser import parse_resume
from src.utils.logger import get_logger
```

This ensures the code can be run with `python -m src.main` and follows Python best practices.

## How JD Analysis Works

1. **Upload JD File** - Admin uploads PDF/DOC job description
2. **Text Extraction** - Extract text using pdfplumber/python-docx
3. **AI Analysis** - GPT-4 extracts:
   - Required skills
   - Preferred skills
   - Experience requirements
   - Education requirements
   - Keywords
4. **Resume Matching** - Compare against all stored resumes:
   - **Phase 1**: Quick traditional scoring (skill overlap, experience, keywords)
   - **Phase 2**: AI semantic matching for top candidates (GPT-4)
5. **Scoring** - Hybrid score (0-100):
   - Skill match: 40%
   - Experience match: 30%
   - Keyword/Semantic match: 30%
6. **Results** - Return top N candidates above threshold (e.g., 80%)

## OpenAI Integration

The system uses GPT-4 for:
- **Resume Parsing**: Extract name, email, skills, experience, education
- **JD Analysis**: Extract requirements and keywords intelligently
- **Semantic Matching**: Understand context beyond keyword matching

**Cost Optimization:**
- Traditional scoring filters candidates first (fast, free)
- AI analysis only on promising candidates (>70% traditional score)
- Typical cost: ~$0.01-0.05 per JD analysis with 100 resumes

## Troubleshooting

### PostgreSQL Connection Error
```bash
# Check PostgreSQL is running
docker ps  # If using Docker
psql -U postgres -d techbank  # If using local PostgreSQL
```

### Database Table Errors
- Ensure PostgreSQL is running
- Check `.env` file has correct credentials
- Restart backend to create tables automatically

### OpenAI API Error
- Verify API key in `.env` file
- Check API key has credits
- Ensure model name is correct (`gpt-4-turbo-preview`)

### File Upload Error
- Check `uploads/resumes/` and `uploads/jd/` directories exist
- Verify file size is under 10MB
- Only PDF and DOCX files are supported

## Development

### Run in Development Mode
```bash
python -m src.main
```

### Run Tests
```bash
pytest
```

### Run Linting
```bash
ruff check src/
```

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### View Logs
Logs are written to console

## Database Schema

- **users** - User accounts (authentication)
- **resumes** - Resume data and parsed information
- **jd_analysis** - Job description analyses
- **match_results** - Candidate matching results
- **token_blacklist** - Revoked JWT tokens

All tables are created automatically on first run.
