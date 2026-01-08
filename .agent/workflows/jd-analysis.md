---
description: How to perform JD analysis and match candidates
---

# JD Analysis Workflow

This workflow explains how to use the Job Description (JD) Analysis feature to find the best matching candidates from your resume bank.

## Overview

The JD Analysis system uses a **Universal Fit Score** algorithm that evaluates candidates across 6 weighted factors:
- **Skill Evidence** (35%) - Technical skills + depth
- **Execution/Responsibility** (25%) - Project complexity, leadership, impact
- **Complexity & Depth** (15%) - Problem-solving sophistication
- **Learning Agility** (10%) - Adaptability, continuous learning
- **Domain Context** (10%) - Industry/domain relevance
- **Communication Clarity** (5%) - Resume quality, clarity

## Visual Workflow

For a complete visual representation of the JD analysis process, see the [Visual Workflow Diagram](file:///C:/Users/Admin/.gemini/antigravity/brain/d5cac718-cc13-4f26-bbf2-2de0683e05d9/jd_workflow_visual.md).

---

## Prerequisites

1. **Backend running**: Ensure the FastAPI backend is running on port 8000
   ```bash
   cd backend
   python -m src.main
   ```

2. **Frontend running**: Ensure the React frontend is running
   ```bash
   cd frontend
   npm run dev
   ```

3. **Authentication**: You must be logged in as an **admin user** to perform JD analysis

4. **Resume Bank**: Have resumes uploaded in the system (via the resume upload feature)

## Method 1: Using the Web Interface (Recommended)

### 1. Access the JD Analysis Feature

1. **Login as Admin**: Navigate to `http://localhost:5173` (or your frontend URL)
2. **Go to Admin Dashboard**: Click on the admin menu
3. **Select "Search Using JD"**: Find the JD analysis feature in the navigation

### 2. Upload Job Description

1. **Drag & Drop or Browse**:
   - Drag your JD PDF file into the upload zone, OR
   - Click "Browse Files" to select from your computer

2. **File Requirements**:
   - Format: PDF only
   - Maximum size: 10MB
   - Should contain clear job requirements, skills, and qualifications

3. **Click "Find Matching Candidates"**: The system will analyze the JD and match candidates

### 3. Review Results

The results page shows:

- **Analysis Summary**:
  - Total matches found
  - Number of visible candidates (based on filters)
  
- **Job Requirements Identified**:
  - Required skills (highlighted tags)
  - Preferred skills (secondary tags)

- **Filter Candidates**:
  - Company Employee
  - Freelancer
  - Hired Forces
  - Guest
  - Admin Uploads

- **Candidate Cards** displaying:
  - Match score percentage
  - Candidate name and initials
  - User type badge
  - Skill match % and Experience match %
  - Role, experience years, location, email
  - Top matched skills
  - Link to view full resume

### 4. Analyze Match Quality

- **Premium Match** badge: Candidates with 80%+ match score
- **Score indicators**:
  - 🟢 Green dot: 70%+ (High match)
  - 🟡 Yellow dot: 40-69% (Medium match)
  - 🔴 Red dot: Below 40% (Low match)

---

## Method 2: Using the API Directly

### 1. Prepare Your Job Description File

- **Supported formats**: PDF, DOC, DOCX
- **Content should include**:
  - Required skills and technologies
  - Preferred skills
  - Minimum experience requirements
  - Education requirements
  - Job level (entry/mid/senior)
  - Job responsibilities and requirements

### 2. Upload JD via API

**Endpoint**: `POST /api/jd/analyze`

**Parameters**:
- `file` (required): The JD file to upload
- `min_score` (optional, default: 80): Minimum match score threshold (0-100)
- `top_n` (optional, default: 10): Number of top candidates to return (1-50)
- `user_types` (optional): Filter by candidate source types (e.g., ["fresher", "experienced"])

**Example using cURL**:
```bash
curl -X POST "http://localhost:8000/api/jd/analyze?min_score=80&top_n=10" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/job_description.pdf"
```

**Example using Python**:
```python
import requests

url = "http://localhost:8000/api/jd/analyze"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
files = {"file": open("job_description.pdf", "rb")}
params = {"min_score": 80, "top_n": 10}

response = requests.post(url, headers=headers, files=files, params=params)
result = response.json()
```

### 3. Understanding the Response

The API returns:
```json
{
  "job_id": "JOB-ABC12345",
  "jd_filename": "job_description.pdf",
  "total_resumes_analyzed": 150,
  "total_matches": 25,
  "min_score_threshold": 80,
  "jd_requirements": {
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "preferred_skills": ["Docker", "AWS"],
    "min_experience_years": 3,
    "education": "Bachelor's in Computer Science",
    "job_level": "mid"
  },
  "top_matches": [
    {
      "resume_id": 123,
      "candidate_name": "John Doe",
      "match_score": 92.5,
      "universal_fit_score": 92.5,
      "skill_evidence_score": 95.0,
      "execution_score": 90.0,
      "complexity_score": 88.0,
      "learning_agility_score": 92.0,
      "domain_context_score": 94.0,
      "communication_score": 96.0,
      "matched_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
      "missing_skills": ["AWS"],
      "match_explanation": "Strong technical match with relevant experience...",
      "factor_breakdown": {
        "skill_evidence": "Demonstrates deep expertise in...",
        "execution": "Led multiple complex projects...",
        ...
      }
    }
  ]
}
```

### 4. Retrieve Saved Results

**Endpoint**: `GET /api/jd/results/{job_id}`

```bash
curl -X GET "http://localhost:8000/api/jd/results/JOB-ABC12345" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

This returns the same match results that were saved during the initial analysis.

### 5. View JD Analysis History

**Endpoint**: `GET /api/jd/history`

**Parameters**:
- `skip` (optional, default: 0): Number of records to skip
- `limit` (optional, default: 20): Number of records to return (1-100)

```bash
curl -X GET "http://localhost:8000/api/jd/history?skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Returns a list of all previous JD analyses with summary information.

## How the Matching Algorithm Works

### Phase 1: Traditional Scoring (Fast)
- Calculates a preliminary score for ALL resumes in the database
- Uses keyword matching, experience comparison, and basic skill overlap
- Filters out candidates below the `min_score` threshold
- **Purpose**: Quickly narrow down the candidate pool

### Phase 2: AI-Enhanced Scoring (Detailed)
- Uses OpenAI GPT-4 to perform deep semantic analysis
- Evaluates the 6 Universal Fit Score factors
- Generates detailed match explanations
- **Caching**: Results are saved to avoid re-computation
- **Concurrency**: Processes up to 5 resumes simultaneously for speed

### Score Calculation
Each factor is scored 0-100, then weighted:
```
Universal Fit Score = 
  (Skill Evidence × 0.35) +
  (Execution × 0.25) +
  (Complexity × 0.15) +
  (Learning Agility × 0.10) +
  (Domain Context × 0.10) +
  (Communication × 0.05)
```

## Tips for Best Results

1. **Detailed JDs**: The more detailed your job description, the better the matching accuracy
2. **Adjust min_score**: Start with 70-75 for broader results, 85+ for highly selective matching
3. **Use filters**: Apply `user_types` filters to narrow down by candidate experience level
4. **Review explanations**: Read the `match_explanation` and `factor_breakdown` for insights
5. **Check missing_skills**: Use this to identify candidates who need training in specific areas

## Troubleshooting

**No matches found**:
- Lower the `min_score` threshold
- Check that resumes are properly uploaded and parsed
- Verify JD file contains clear requirements

**Slow performance**:
- Reduce `top_n` parameter
- The first run is slower due to AI analysis; subsequent runs use cached results

**Authentication errors**:
- Ensure you're logged in as an admin user
- Check that your JWT token is valid

## Database Tables

The system uses two main tables:

1. **jd_analysis**: Stores JD metadata and extracted requirements
2. **match_results**: Stores detailed match scores for each candidate-JD pair

Results are persisted for future retrieval and analysis.
