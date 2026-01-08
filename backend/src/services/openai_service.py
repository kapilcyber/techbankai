"""OpenAI service for AI-powered parsing and matching."""
import json
from openai import AsyncOpenAI
from typing import Dict, List
from src.utils.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)

# OpenAI Configuration from settings
OPENAI_API_KEY = settings.openai_api_key
OPENAI_MODEL = settings.openai_model
OPENAI_MAX_TOKENS = settings.openai_max_tokens

# Initialize OpenAI client lazily to avoid import-time errors
_client = None


def get_openai_client():
    """Get or create OpenAI client (lazy initialization)."""
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
    Use GPT-4 to extract structured data from resume text.
    Returns: Structured resume data as dictionary matching ParsedResume schema.
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
        
        logger.info(f"Parsing resume. Text length: {len(resume_text)}")
        user_prompt = f"""Extract Resume Data (JSON only):
{resume_text[:4000]}

Fields:
"resume_candidate_name", 
"resume_contact_info" (email), 
"resume_role", 
"resume_location", 
"resume_degree", 
"resume_university", 
"resume_experience" (float), 
"resume_technical_skills" (list), 
"resume_projects" (list), 
"resume_achievements" (list), 
"resume_certificates" (list), 
"all_skills" (list), 
"notice_period" (days), 
"ready_to_relocate" (bool),
"work_history": [
  {{
    "company": "...",
    "role": "...",
    "location": "...",
    "start_date": "...",
    "end_date": "...",
    "is_current": 0 | 1,
    "description": "Brief summary of responsibilities and achievements in this role"
  }}
]
"""
        
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=min(OPENAI_MAX_TOKENS, 4096),
            temperature=0.1 # High precision
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
    Use GPT-4 to analyze job description and extract requirements.
    Returns: Structured JD requirements.
    """
    client = get_openai_client()
    if not client:
        logger.error("OpenAI client not initialized - API key missing or invalid")
        raise ValueError("OpenAI API key not configured")
    
    try:
        system_prompt = """You are an enterprise-grade Job Description (JD) Decomposition Engine.

Your ONLY task is to analyze a Job Description (JD) and convert it into a
structured, weighted requirement model suitable for strict resume matching.

You MUST NOT:
- Score resumes
- Mention candidates
- Infer skills not stated or strongly implied
- Add explanations outside the JSON output

You MUST:
- Decompose the JD into EXACTLY the categories listed below
- Assign weights based on importance implied by the JD
- Ensure total weight = 100
- Return VALID JSON ONLY (no markdown, no commentary)

MANDATORY JD CATEGORIES:
1. Experience & Seniority
2. Core Technical Skills
3. Networking & Protocols
4. Security Technologies
5. Cloud & Architecture
6. Incident & Operations
7. Compliance & Governance
8. Certifications

RULES:
- Prefer explicit requirements over nice-to-haves
- If a category is weakly mentioned, assign a lower weight (minimum 5)
- Do NOT invent certifications or tools
- Seniority must be inferred from role title and responsibilities
- Use concise, normalized skill names (e.g., "NGFW", "IDS/IPS", "BGP")

return JSON in the following structure ONLY:

{
  "experience_seniority": {
    "required_years": <number>,
    "role_level": "<Engineer | Senior | Lead | Manager | Architect>",
    "weight": <number>
  },
  "core_technical_skills": {
    "items": [ "<skill>", "<skill>" ],
    "weight": <number>
  },
  "networking_protocols": {
    "items": [ "<protocol>", "<protocol>" ],
    "weight": <number>
  },
  "security_technologies": {
    "items": [ "<tool_or_tech>", "<tool_or_tech>" ],
    "weight": <number>
  },
  "cloud_architecture": {
    "items": [ "<cloud_or_architecture>" ],
    "weight": <number>
  },
  "incident_operations": {
    "items": [ "<incident_or_ops_requirement>" ],
    "weight": <number>
  },
  "compliance_governance": {
    "items": [ "<standard_or_framework>" ],
    "weight": <number>
  },
  "certifications": {
    "items": [ "<certification>" ],
    "weight": <number>
  }
}
"""
        
        user_prompt = f"""Analyze this job description:

{jd_text[:3500]}

Decompose into the strict JSON format required.
"""
        
        # Use a safe maximum for tokens
        max_tokens = min(OPENAI_MAX_TOKENS, 4096)
        
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
            temperature=0.2 # Low temperature for consistency
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Backward compatibility mapping for `jd_analysis.py` which expects flat structure
        # We perform this mapping here so the rest of the app continues to work while we transition
        flattened_result = {
            "job_level": (result.get("experience_seniority") or {}).get("role_level", "Experienced"),
            "min_experience_years": (result.get("experience_seniority") or {}).get("required_years") or 0,
            "required_skills": (
                result.get("core_technical_skills", {}).get("items", []) + 
                result.get("networking_protocols", {}).get("items", []) +
                result.get("security_technologies", {}).get("items", []) +
                result.get("cloud_architecture", {}).get("items", [])
            ),
            "keywords": (
                result.get("compliance_governance", {}).get("items", []) +
                result.get("incident_operations", {}).get("items", [])
            ),
            # Store the full structured decomposition for the matcher
            "structured_requirements": result,
            "weights": {k: v.get("weight", 0) for k, v in result.items() if isinstance(v, dict)}
        }
        
        logger.info(f"Successfully extracted JD requirements with GPT-4")
        return flattened_result
    
    except Exception as e:
        logger.error(f"GPT-4 JD extraction failed: {e}")
        raise


async def calculate_intelligent_match(resume_data: Dict, jd_requirements: Dict) -> Dict:
    """
    Use GPT-4 to perform intelligent semantic matching.
    Returns: Match score and detailed analysis.
    """
    client = get_openai_client()
    if not client:
        logger.error("OpenAI client not initialized - API key missing or invalid")
        raise ValueError("OpenAI API key not configured")
    
    try:
        system_prompt = """You are an enterprise-grade Resume Analysis Engine.

Your task is to provide QUALITATIVE JUDGMENTS ONLY for each JD category.

DO NOT:
- Return numeric scores
- Return percentages
- Calculate final scores
- Apply penalties or bonuses

DO:
- Assess match level (HIGH, MEDIUM, LOW, NO)
- Assess ownership level (LED, OWNED, CONTRIBUTED, ASSISTED, NONE)
- Provide evidence from resume
- Indicate if experience is recent (last 5 years)

MATCH LEVEL DEFINITIONS:
- HIGH: Candidate has deep, proven expertise with strong evidence
- MEDIUM: Candidate has relevant experience but limited depth
- LOW: Candidate has minimal or tangential experience
- NO: No evidence of this skill/experience

OWNERSHIP LEVEL DEFINITIONS:
- LED: Led teams, projects, or initiatives (leadership verbs: led, managed, directed, architected)
- OWNED: Owned outcomes, systems, or processes (ownership verbs: owned, designed, built, implemented)
- CONTRIBUTED: Contributed to team efforts (contribution verbs: contributed, developed, worked on)
- ASSISTED: Assisted or supported (support verbs: assisted, supported, helped)
- NONE: No evidence

STRICT RULES:
- Prioritize recent experience (last 5 years)
- Look for ownership verbs over participation verbs
- Require explicit evidence, not assumptions
- Be brutally honest

OUTPUT FORMAT (JSON ONLY):
{
  "experience_seniority": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Specific evidence from resume",
    "recent": true|false
  },
  "core_technical_skills": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Specific skills mentioned"
  },
  "networking_protocols": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Specific protocols/technologies"
  },
  "security_technologies": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Specific security tools/technologies"
  },
  "cloud_architecture": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Specific cloud platforms/architectures"
  },
  "incident_operations": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Incident handling experience"
  },
  "compliance_governance": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "LED|OWNED|CONTRIBUTED|ASSISTED|NONE",
    "evidence": "Compliance standards/frameworks"
  },
  "certifications": {
    "match_level": "HIGH|MEDIUM|LOW|NO",
    "ownership": "OWNED|NONE",
    "evidence": "Certifications held"
  }
}
"""
        
        # Prepare structured inputs for the prompt
        structured_jd = jd_requirements.get('structured_requirements', jd_requirements)
        
        user_prompt = f"""ANALYZE THIS RESUME AGAINST JD REQUIREMENTS:

[JD REQUIREMENTS BY CATEGORY]
{json.dumps(structured_jd, indent=2)}

[CANDIDATE RESUME]
Name: {resume_data.get('resume_candidate_name', 'Unknown')}
Current Role: {resume_data.get('role', 'N/A')}
Total Experience: {resume_data.get('experience_years', 0)} years
Skills: {', '.join(resume_data.get('skills', [])[:20])}
Certifications: {', '.join(resume_data.get('certifications', []))}

Resume Summary:
{resume_data.get('summary', '')[:2000]}

Resume Text (Recent Experience):
{resume_data.get('raw_text', '')[:3500]}

For EACH JD category above, provide:
1. Match level (HIGH/MEDIUM/LOW/NO)
2. Ownership level (LED/OWNED/CONTRIBUTED/ASSISTED/NONE)
3. Specific evidence from resume
4. Whether experience is recent (last 5 years)

Return ONLY the JSON structure specified in the system prompt.
"""
        
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=min(OPENAI_MAX_TOKENS, 4096),
            temperature=0.1 # Very low temperature for deterministic scoring
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Successfully calculated intelligent match with GPT-4")
        return result
    
    except Exception as e:
        logger.error(f"GPT-4 matching failed: {e}")
        raise
