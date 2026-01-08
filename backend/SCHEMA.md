# PostgreSQL Database Schema Documentation

Complete schema documentation for TechBank.ai PostgreSQL database.

**Database Name:** `techbank`  
**Database Engine:** PostgreSQL 15+  
**ORM:** SQLAlchemy (Async)

---

## Table of Contents

1. [Users Table](#1-users-table)
2. [Resumes Table](#2-resumes-table)
3. [JD Analysis Table](#3-jd-analysis-table)
4. [Match Results Table](#4-match-results-table)
5. [Token Blacklist Table](#5-token-blacklist-table)
6. [Indexes](#indexes)
7. [Foreign Keys](#foreign-keys)
8. [Constraints](#constraints)

---

## 1. Users Table

**Table Name:** `users`  
**Purpose:** Stores user account information including authentication and profile data.

### SQL Schema

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    dob VARCHAR(50),
    state VARCHAR(100),
    city VARCHAR(100),
    pincode VARCHAR(10),
    mode VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Column Descriptions

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | SERIAL | NO | Auto-increment | Primary key, unique identifier |
| `name` | VARCHAR(100) | NO | - | User's full name |
| `email` | VARCHAR(255) | NO | - | User's email address (unique) |
| `password_hash` | VARCHAR(255) | NO | - | Bcrypt hashed password |
| `dob` | VARCHAR(50) | YES | - | Date of birth (stored as string) |
| `state` | VARCHAR(100) | YES | - | User's state/province |
| `city` | VARCHAR(100) | YES | - | User's city |
| `pincode` | VARCHAR(10) | YES | - | Postal/ZIP code |
| `mode` | VARCHAR(20) | YES | 'user' | User role: 'user' or 'admin' |
| `created_at` | TIMESTAMP | YES | CURRENT_TIMESTAMP | Account creation timestamp |
| `updated_at` | TIMESTAMP | YES | CURRENT_TIMESTAMP | Last update timestamp (auto-updated) |

### Indexes

- `users_pkey` (Primary Key on `id`)
- `ix_users_id` (on `id`)
- `idx_users_email` (on `email`)

### Constraints

- **Primary Key:** `id`
- **Unique:** `email`

---

## 2. Resumes Table

**Table Name:** `resumes`  
**Purpose:** Stores resume files and parsed data from multiple sources (company employees, Gmail, admin uploads, freelancers, guests, hired force).

### SQL Schema

```sql
CREATE TABLE resumes (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(100),
    source_metadata JSONB,
    filename VARCHAR(255) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    raw_text TEXT,
    parsed_data JSONB,
    skills TEXT[],
    experience_years FLOAT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by VARCHAR(100),
    meta_data JSONB,
    CONSTRAINT uq_resume_source UNIQUE (source_type, source_id)
);
```

### Column Descriptions

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | SERIAL | NO | Auto-increment | Primary key, unique identifier |
| `source_type` | VARCHAR(50) | NO | - | Source type: 'company_employee', 'gmail', 'admin', 'freelancer', 'guest', 'hired_force' |
| `source_id` | VARCHAR(100) | YES | - | Source-specific identifier (employee_id, message_id, etc.) |
| `source_metadata` | JSONB | YES | - | Source-specific metadata (employee_id, department, gmail metadata, etc.) |
| `filename` | VARCHAR(255) | NO | - | Original filename of uploaded resume |
| `file_url` | VARCHAR(500) | NO | - | URL/path to stored resume file |
| `raw_text` | TEXT | YES | - | Extracted raw text from PDF/DOC file |
| `parsed_data` | JSONB | YES | - | Structured parsed data: name, email, phone, skills, experience, etc. |
| `skills` | TEXT[] | YES | - | Array of extracted skills |
| `experience_years` | FLOAT | YES | - | Years of experience (extracted or calculated) |
| `uploaded_at` | TIMESTAMP | YES | CURRENT_TIMESTAMP | Upload timestamp |
| `uploaded_by` | VARCHAR(100) | YES | - | Admin email who uploaded (for admin uploads) |
| `meta_data` | JSONB | YES | - | Additional metadata including user_type, form data, etc. |

### Indexes

- `resumes_pkey` (Primary Key on `id`)
- `ix_resumes_id` (on `id`)
- `idx_resumes_skills` (GIN index on `skills` array)
- `idx_resumes_uploaded_at` (on `uploaded_at DESC`)
- `idx_resumes_source_type` (on `source_type`)

### Constraints

- **Primary Key:** `id`
- **Unique:** `(source_type, source_id)` - Ensures idempotent uploads per source

### Source Types

- `company_employee` - Company employee resumes
- `gmail` - Resumes received via Gmail
- `admin` - Admin bulk uploads
- `freelancer` - Freelancer profiles
- `guest` - Guest user uploads
- `hired_force` - HiredForce platform resumes

---

## 3. JD Analysis Table

**Table Name:** `jd_analysis`  
**Purpose:** Stores job description analysis results including extracted keywords, skills, and requirements.

### SQL Schema

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

### Column Descriptions

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | SERIAL | NO | Auto-increment | Primary key, unique identifier |
| `job_id` | VARCHAR(100) | NO | - | Unique job identifier (e.g., JOB-001) |
| `jd_filename` | VARCHAR(255) | YES | - | Original filename of job description file |
| `jd_text` | TEXT | YES | - | Full text content of job description |
| `extracted_keywords` | TEXT[] | YES | - | Array of extracted keywords from JD |
| `required_skills` | TEXT[] | YES | - | Array of required skills |
| `preferred_skills` | TEXT[] | YES | - | Array of preferred/nice-to-have skills |
| `required_experience` | FLOAT | YES | 0 | Required years of experience |
| `education` | VARCHAR(500) | YES | - | Education requirements |
| `job_level` | VARCHAR(50) | YES | - | Job level: 'entry', 'mid', 'senior' |
| `submitted_at` | TIMESTAMP | YES | CURRENT_TIMESTAMP | JD submission timestamp |
| `submitted_by` | VARCHAR(100) | YES | - | Admin email who submitted the JD |

### Indexes

- `jd_analysis_pkey` (Primary Key on `id`)
- `ix_jd_analysis_id` (on `id`)
- `ix_jd_analysis_job_id` (on `job_id`)
- `idx_job_id` (on `job_id`)
- `idx_submitted_at` (on `submitted_at DESC`)

### Constraints

- **Primary Key:** `id`
- **Unique:** `job_id`

---

## 4. Match Results Table

**Table Name:** `match_results`  
**Purpose:** Stores matching results between job descriptions and resumes with scoring details.

### SQL Schema

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

### Column Descriptions

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | SERIAL | NO | Auto-increment | Primary key, unique identifier |
| `job_id` | VARCHAR(100) | NO | - | Foreign key to `jd_analysis.job_id` |
| `resume_id` | INTEGER | NO | - | Foreign key to `resumes.id` |
| `source_type` | VARCHAR(50) | YES | - | Resume source type (denormalized for quick filtering) |
| `source_id` | VARCHAR(100) | YES | - | Resume source ID (denormalized) |
| `match_score` | FLOAT | YES | - | Overall match score (0-100) |
| `skill_match_score` | FLOAT | YES | - | Skill matching score (0-100) |
| `experience_match_score` | FLOAT | YES | - | Experience matching score (0-100) |
| `semantic_score` | FLOAT | YES | - | AI semantic matching score (0-100) |
| `keyword_matches` | JSONB | YES | - | Detailed keyword match information |
| `match_explanation` | TEXT | YES | - | AI-generated explanation of the match |
| `created_at` | TIMESTAMP | YES | CURRENT_TIMESTAMP | Match result creation timestamp |

### Indexes

- `match_results_pkey` (Primary Key on `id`)
- `ix_match_results_id` (on `id`)
- `ix_match_results_job_id` (on `job_id`)
- `ix_match_results_source_type` (on `source_type`)
- `idx_match_results_job_id` (on `job_id`)
- `idx_match_results_resume_id` (on `resume_id`)
- `idx_match_results_score` (on `match_score DESC`)
- `idx_match_results_source_type` (on `source_type`)

### Constraints

- **Primary Key:** `id`
- **Foreign Key:** `job_id` → `jd_analysis.job_id`
- **Foreign Key:** `resume_id` → `resumes.id`

---

## 5. Token Blacklist Table

**Table Name:** `token_blacklist`  
**Purpose:** Stores blacklisted JWT tokens for logout functionality.

### SQL Schema

```sql
CREATE TABLE token_blacklist (
    id SERIAL PRIMARY KEY,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Column Descriptions

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | SERIAL | NO | Auto-increment | Primary key, unique identifier |
| `token` | VARCHAR(500) | NO | - | JWT token string (unique) |
| `expires_at` | TIMESTAMP | NO | - | Token expiration timestamp |
| `created_at` | TIMESTAMP | YES | CURRENT_TIMESTAMP | Blacklist entry creation timestamp |

### Indexes

- `token_blacklist_pkey` (Primary Key on `id`)
- `ix_token_blacklist_id` (on `id`)
- `ix_token_blacklist_token` (on `token`)
- `idx_token_blacklist_token` (on `token`)

### Constraints

- **Primary Key:** `id`
- **Unique:** `token`

---

## Indexes

### Summary of All Indexes

| Table | Index Name | Columns | Type | Purpose |
|-------|------------|---------|------|---------|
| `users` | `users_pkey` | `id` | Primary Key | Unique identifier |
| `users` | `ix_users_id` | `id` | B-tree | Fast ID lookups |
| `users` | `idx_users_email` | `email` | B-tree | Fast email lookups |
| `resumes` | `resumes_pkey` | `id` | Primary Key | Unique identifier |
| `resumes` | `ix_resumes_id` | `id` | B-tree | Fast ID lookups |
| `resumes` | `idx_resumes_skills` | `skills` | GIN | Array search (skills) |
| `resumes` | `idx_resumes_uploaded_at` | `uploaded_at DESC` | B-tree | Recent uploads |
| `resumes` | `idx_resumes_source_type` | `source_type` | B-tree | Filter by source |
| `jd_analysis` | `jd_analysis_pkey` | `id` | Primary Key | Unique identifier |
| `jd_analysis` | `ix_jd_analysis_id` | `id` | B-tree | Fast ID lookups |
| `jd_analysis` | `ix_jd_analysis_job_id` | `job_id` | B-tree | Fast job_id lookups |
| `jd_analysis` | `idx_job_id` | `job_id` | B-tree | Job ID lookups |
| `jd_analysis` | `idx_submitted_at` | `submitted_at DESC` | B-tree | Recent submissions |
| `match_results` | `match_results_pkey` | `id` | Primary Key | Unique identifier |
| `match_results` | `ix_match_results_id` | `id` | B-tree | Fast ID lookups |
| `match_results` | `ix_match_results_job_id` | `job_id` | B-tree | Job ID lookups |
| `match_results` | `idx_match_results_job_id` | `job_id` | B-tree | Job ID joins |
| `match_results` | `idx_match_results_resume_id` | `resume_id` | B-tree | Resume ID joins |
| `match_results` | `idx_match_results_score` | `match_score DESC` | B-tree | Top matches |
| `match_results` | `idx_match_results_source_type` | `source_type` | B-tree | Filter by source |
| `token_blacklist` | `token_blacklist_pkey` | `id` | Primary Key | Unique identifier |
| `token_blacklist` | `ix_token_blacklist_id` | `id` | B-tree | Fast ID lookups |
| `token_blacklist` | `ix_token_blacklist_token` | `token` | B-tree | Token lookups |
| `token_blacklist` | `idx_token_blacklist_token` | `token` | B-tree | Token validation |

### Index Types

- **B-tree:** Standard index for equality and range queries
- **GIN (Generalized Inverted Index):** Used for array columns (`skills`) to enable fast array containment queries

---

## Foreign Keys

### Foreign Key Relationships

| From Table | From Column | To Table | To Column | On Delete | On Update |
|------------|-------------|----------|-----------|-----------|-----------|
| `match_results` | `job_id` | `jd_analysis` | `job_id` | RESTRICT | CASCADE |
| `match_results` | `resume_id` | `resumes` | `id` | RESTRICT | CASCADE |

### Relationship Diagram

```
jd_analysis (job_id)
    ↑
    │ (1:N)
    │
match_results (job_id, resume_id)
    │
    │ (N:1)
    ↓
resumes (id)
```

---

## Constraints

### Primary Keys

- `users.id` → SERIAL PRIMARY KEY
- `resumes.id` → SERIAL PRIMARY KEY
- `jd_analysis.id` → SERIAL PRIMARY KEY
- `match_results.id` → SERIAL PRIMARY KEY
- `token_blacklist.id` → SERIAL PRIMARY KEY

### Unique Constraints

- `users.email` → UNIQUE
- `resumes(source_type, source_id)` → UNIQUE (composite)
- `jd_analysis.job_id` → UNIQUE
- `token_blacklist.token` → UNIQUE

### Not Null Constraints

- `users.name`, `users.email`, `users.password_hash` → NOT NULL
- `resumes.source_type`, `resumes.filename`, `resumes.file_url` → NOT NULL
- `jd_analysis.job_id` → NOT NULL
- `match_results.job_id`, `match_results.resume_id` → NOT NULL
- `token_blacklist.token`, `token_blacklist.expires_at` → NOT NULL

### Default Values

- `users.mode` → DEFAULT 'user'
- `users.created_at`, `users.updated_at` → DEFAULT CURRENT_TIMESTAMP
- `resumes.uploaded_at` → DEFAULT CURRENT_TIMESTAMP
- `jd_analysis.required_experience` → DEFAULT 0
- `jd_analysis.submitted_at` → DEFAULT CURRENT_TIMESTAMP
- `match_results.created_at` → DEFAULT CURRENT_TIMESTAMP
- `token_blacklist.created_at` → DEFAULT CURRENT_TIMESTAMP

---

## Data Types Reference

### PostgreSQL Types Used

| Type | Usage | Description |
|------|-------|-------------|
| `SERIAL` | Primary keys | Auto-incrementing integer |
| `VARCHAR(n)` | Text fields | Variable-length string with max length |
| `TEXT` | Long text | Unlimited length text |
| `INTEGER` | Foreign keys | 32-bit integer |
| `FLOAT` | Numeric values | Floating-point number |
| `TIMESTAMP` | Date/time | Date and time without timezone |
| `TEXT[]` | Arrays | Array of text values |
| `JSONB` | JSON data | Binary JSON for structured data |

### JSONB Fields

**`resumes.source_metadata`** - Example structure:
```json
{
  "employee_id": "EMP-001",
  "department": "Engineering",
  "company_name": "TechCorp"
}
```

**`resumes.parsed_data`** - Example structure:
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "skills": ["Python", "React", "AWS"],
  "experience": 5,
  "education": "BS Computer Science"
}
```

**`resumes.meta_data`** - Example structure:
```json
{
  "user_type": "freelancer",
  "fullName": "John Doe",
  "phone": "+1234567890",
  "form_skills": "Python, React, AWS"
}
```

**`match_results.keyword_matches`** - Example structure:
```json
{
  "python": 1.0,
  "react": 0.9,
  "aws": 0.8,
  "total_matches": 15,
  "total_keywords": 20
}
```

---

## Database Initialization

Tables and indexes are automatically created when the backend starts via:

```python
# backend/src/config/database.py
async def init_postgres_db():
    # Creates all tables
    await conn.run_sync(Base.metadata.create_all)
    
    # Creates additional indexes
    # (see database.py for full list)
```

---

## Migration Notes

- All tables use `SERIAL` for auto-incrementing IDs
- Timestamps use `TIMESTAMP` (without timezone) - defaults to UTC
- JSONB fields allow flexible schema evolution
- Array fields (`TEXT[]`) use GIN indexes for fast searches
- Foreign keys use RESTRICT on delete to prevent orphaned records

---

## Verification

To verify the schema, run:

```bash
cd backend
python verify_jd_tables.py
```

Or connect to PostgreSQL:

```sql
-- List all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- List all indexes
SELECT tablename, indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'public';

-- List all foreign keys
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'public';
```

---

**Last Updated:** 2024-12-26  
**Schema Version:** 1.0.0  
**ORM Models:** `backend/src/models/`

