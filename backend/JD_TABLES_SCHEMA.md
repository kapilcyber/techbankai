# JD Analysis and Match Results Tables Schema

## ✅ Tables Verified and Configured

### 1. JD Analysis Table (`jd_analysis`)

**Structure:**
```sql
CREATE TABLE jd_analysis (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) UNIQUE NOT NULL,
    jd_filename VARCHAR(255),
    jd_text TEXT,
    extracted_keywords TEXT[],
    required_skills TEXT[],
    preferred_skills TEXT[],
    required_experience FLOAT DEFAULT 0,
    education VARCHAR(500),
    job_level VARCHAR(50),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_by VARCHAR(100)
);
```

**Indexes:**
- ✅ `idx_job_id` - On `job_id` (unique index)
- ✅ `idx_submitted_at` - On `submitted_at DESC`

**SQLAlchemy Model:** `backend/src/models/jd_analysis.py::JDAnalysis`

### 2. Match Results Table (`match_results`)

**Structure:**
```sql
CREATE TABLE match_results (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL,
    resume_id INTEGER NOT NULL,
    source_type VARCHAR(50),
    source_id VARCHAR(100),
    match_score FLOAT,
    skill_match_score FLOAT,
    experience_match_score FLOAT,
    semantic_score FLOAT,
    keyword_matches JSONB,
    match_explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jd_analysis(job_id),
    FOREIGN KEY (resume_id) REFERENCES resumes(id)
);
```

**Indexes:**
- ✅ `idx_job_id` - On `job_id`
- ✅ `idx_resume_id` - On `resume_id`
- ✅ `idx_match_score` - On `match_score DESC`
- ✅ `idx_source_type` - On `source_type`

**Foreign Keys:**
- ✅ `job_id` → `jd_analysis.job_id`
- ✅ `resume_id` → `resumes.id`

**SQLAlchemy Model:** `backend/src/models/jd_analysis.py::MatchResult`

## Verification

Run the verification script to check table structure:
```bash
cd backend
python verify_jd_tables.py
```

## Index Creation

All indexes are automatically created when the backend starts via `backend/src/config/database.py::init_postgres_db()`.

If indexes are missing, run:
```bash
cd backend
python add_missing_indexes.py
```

## Usage

### Creating JD Analysis
```python
from src.models.jd_analysis import JDAnalysis
from src.config.database import get_postgres_db

async def create_jd_analysis(jd_data):
    async for db in get_postgres_db():
        jd = JDAnalysis(
            job_id="JOB-001",
            jd_filename="job_description.pdf",
            jd_text="Full job description text...",
            extracted_keywords=["python", "react", "aws"],
            required_skills=["python", "javascript"],
            preferred_skills=["react", "node.js"],
            required_experience=3.0,
            education="Bachelor's in Computer Science",
            job_level="mid",
            submitted_by="admin@example.com"
        )
        db.add(jd)
        await db.commit()
        return jd
```

### Creating Match Result
```python
from src.models.jd_analysis import MatchResult

async def create_match_result(match_data):
    async for db in get_postgres_db():
        match = MatchResult(
            job_id="JOB-001",
            resume_id=123,
            source_type="company_employee",
            source_id="EMP-456",
            match_score=85.5,
            skill_match_score=90.0,
            experience_match_score=80.0,
            semantic_score=88.0,
            keyword_matches={"python": 1.0, "react": 0.9},
            match_explanation="Strong match with required skills..."
        )
        db.add(match)
        await db.commit()
        return match
```

## Status

✅ Tables created
✅ Indexes configured
✅ Foreign keys established
✅ Default values set
✅ Models match SQL schema


