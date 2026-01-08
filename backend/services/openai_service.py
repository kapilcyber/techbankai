import os
import json
from openai import AsyncOpenAI
from typing import Dict, List
from utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "10000"))

# Initialize OpenAI client lazily to avoid import-time errors
_client = None

def get_openai_client():
    """Get or create OpenAI client (lazy initialization)"""
    global _client
    if _client is None and OPENAI_API_KEY:
        try:
            _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
            _client = None
    return _client

async def parse_resume_with_gpt(resume_text: str) -> Dict:
    """
    Use GPT-4 to extract structured data from resume text
    Returns: Structured resume data as dictionary matching ParsedResume schema
    """
    client = get_openai_client()
    if not client:
        logger.error("OpenAI client not initialized - API key missing or invalid")
        raise ValueError("OpenAI API key not configured")
    
    try:
        system_prompt = """You are an expert resume parser and HR analyst. 
Extract structured information from resumes with high accuracy.
NEVER hallucinate or invent data. If information is not present, use "Not mentioned" for strings, 0.0 for numbers, or empty arrays.
Return data as valid JSON only, no additional text."""
        
        user_prompt = f"""Analyze this resume and extract the following information:

{resume_text[:4000]}  

Return a JSON object with EXACTLY these fields (use "Not mentioned" if not found, 0.0 for experience if not found):
{{
  "resume_candidate_name": "Full Name" or "Not mentioned",
  "resume_contact_info": "email@example.com" or "Not mentioned" (EMAIL ONLY, no phone),
  "resume_role": "Current/Recent Job Title" or "Not mentioned",
  "resume_location": "City, State/Country" or "Not mentioned",
  "resume_degree": "Highest Degree" or "Not mentioned",
  "resume_university": "University Name" or "Not mentioned",
  "resume_experience": 5.5 (calculated years, or 0.0 if not found),
  "resume_technical_skills": ["Python", "JavaScript", ...] (array, lowercase),
  "resume_projects": ["Project 1", "Project 2", ...] (array),
  "resume_achievements": ["Achievement 1", ...] (array),
  "resume_certificates": ["Cert 1", "Cert 2", ...] (array),
  "all_skills": ["python", "javascript", ...] (all skills merged, lowercase, deduplicated)
}}

CRITICAL RULES:
- Use "Not mentioned" for missing string fields, never null or empty string
- Use 0.0 for missing experience, never null
- Convert all skills to lowercase in resume_technical_skills and all_skills
- Deduplicate skills in all_skills
- Extract email only in resume_contact_info (no phone numbers)
- Calculate experience_years from work history if not explicitly stated
- If a field is truly not found, use the default value specified above"""
        
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Normalize skills to lowercase and deduplicate
        if "resume_technical_skills" in result:
            result["resume_technical_skills"] = list(set([s.lower().strip() for s in result["resume_technical_skills"] if s]))
        if "all_skills" in result:
            result["all_skills"] = list(set([s.lower().strip() for s in result["all_skills"] if s]))
        
        # Ensure all required fields have defaults
        result.setdefault("resume_candidate_name", "Not mentioned")
        result.setdefault("resume_contact_info", "Not mentioned")
        result.setdefault("resume_role", "Not mentioned")
        result.setdefault("resume_location", "Not mentioned")
        result.setdefault("resume_degree", "Not mentioned")
        result.setdefault("resume_university", "Not mentioned")
        result.setdefault("resume_experience", 0.0)
        result.setdefault("resume_technical_skills", [])
        result.setdefault("resume_projects", [])
        result.setdefault("resume_achievements", [])
        result.setdefault("resume_certificates", [])
        result.setdefault("all_skills", [])
        
        logger.info(f"Successfully parsed resume with GPT-4")
        return result
    
    except Exception as e:
        logger.error(f"GPT-4 resume parsing failed: {e}")
        raise

async def extract_jd_requirements(jd_text: str) -> Dict:
    """
    Use GPT-4 to analyze job description and extract requirements
    Returns: Structured JD requirements
    """
    client = get_openai_client()
    if not client:
        logger.error("OpenAI client not initialized - API key missing or invalid")
        raise ValueError("OpenAI API key not configured")
    
    try:
        system_prompt = """You are an expert HR analyst and technical recruiter. 
Analyze job descriptions and extract key requirements with precision.
Return data as valid JSON only."""
        
        user_prompt = f"""Analyze this job description:

{jd_text[:4000]}

Extract and return JSON with:
{{
  "required_skills": ["skill1", "skill2", ...],
  "preferred_skills": ["skill1", "skill2", ...],
  "min_experience_years": 5,
  "education": "Bachelor's in Computer Science or equivalent",
  "keywords": ["keyword1", "keyword2", ...],
  "job_level": "senior",
  "key_responsibilities": ["resp1", "resp2", ...]
}}

Be thorough and extract all relevant information."""
        
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Successfully extracted JD requirements with GPT-4")
        return result
    
    except Exception as e:
        logger.error(f"GPT-4 JD extraction failed: {e}")
        raise

async def calculate_intelligent_match(resume_data: Dict, jd_requirements: Dict) -> Dict:
    """
    Use GPT-4 to perform intelligent semantic matching
    Returns: Match score and detailed analysis
    """
    client = get_openai_client()
    if not client:
        logger.error("OpenAI client not initialized - API key missing or invalid")
        raise ValueError("OpenAI API key not configured")
    
    try:
        system_prompt = """You are an expert technical recruiter and talent matcher.
Analyze candidate-job fit with precision and provide detailed scoring.
Return data as valid JSON only."""
        
        user_prompt = f"""Compare this candidate's profile with job requirements:

CANDIDATE:
Skills: {resume_data.get('skills', [])}
Experience: {resume_data.get('experience_years', 0)} years
Summary: {resume_data.get('summary', 'N/A')}
Education: {resume_data.get('education', [])}

JOB REQUIREMENTS:
Required Skills: {jd_requirements.get('required_skills', [])}
Preferred Skills: {jd_requirements.get('preferred_skills', [])}
Experience: {jd_requirements.get('min_experience_years', 0)} years
Education: {jd_requirements.get('education', 'N/A')}

Analyze and return JSON:
{{
  "score": 85,
  "skill_match": 90,
  "experience_match": 80,
  "semantic_score": 85,
  "matched_skills": ["Python", "React", ...],
  "missing_skills": ["AWS", ...],
  "explanation": "Detailed explanation of why this is a good/poor match"
}}

Provide honest, accurate scoring (0-100)."""
        
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Successfully calculated intelligent match with GPT-4")
        return result
    
    except Exception as e:
        logger.error(f"GPT-4 matching failed: {e}")
        raise
