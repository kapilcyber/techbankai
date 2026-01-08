import re
from typing import Dict, List, Optional
from services.file_processor import extract_text_from_file
from services import openai_service
from schemas.resume import ParsedResume
from utils.logger import get_logger

logger = get_logger(__name__)

def normalize_skills(skills: List[str]) -> List[str]:
    """Normalize skills: lowercase, strip, deduplicate"""
    if not skills:
        return []
    normalized = [s.lower().strip() for s in skills if s and s.strip()]
    return list(set(normalized))

def merge_skills(resume_skills: List[str], form_skills: Optional[str] = None) -> List[str]:
    """Merge resume skills and form skills, deduplicate"""
    all_skills = list(resume_skills) if resume_skills else []
    
    if form_skills:
        form_skill_list = [s.strip() for s in form_skills.split(',') if s.strip()]
        all_skills.extend(form_skill_list)
    
    return normalize_skills(all_skills)

async def parse_resume(
    file_path: str, 
    file_extension: str,
    form_data: Optional[Dict] = None
) -> Dict:
    """
    Parse resume and extract structured data
    Uses OpenAI GPT-4 as primary method with fallback to traditional parsing
    Returns: Dict matching ParsedResume schema
    
    Args:
        file_path: Path to resume file
        file_extension: File extension (pdf, docx)
        form_data: Optional form data to merge (name, email, phone, skills)
    """
    # Step 1: Extract raw text from file
    raw_text = extract_text_from_file(file_path, file_extension)
    
    if not raw_text:
        raise ValueError("Failed to extract text from resume")
    
    # Step 2: Try OpenAI parsing first
    try:
        parsed_data = await openai_service.parse_resume_with_gpt(raw_text)
        parsed_data['raw_text'] = raw_text
        parsed_data['parsing_method'] = 'openai'
    except Exception as e:
        logger.warning(f"OpenAI parsing failed: {e}, falling back to traditional parsing")
        # Step 3: Fallback to traditional parsing
        parsed_data = fallback_parse_resume(raw_text)
        parsed_data['raw_text'] = raw_text
        parsed_data['parsing_method'] = 'fallback'
    
    # Step 4: Merge form data (resume data takes priority, form as fallback)
    if form_data:
        # Only use form data if resume data is missing or empty
        if form_data.get('fullName') and (not parsed_data.get('resume_candidate_name') or parsed_data.get('resume_candidate_name') == 'Not mentioned'):
            parsed_data['resume_candidate_name'] = form_data['fullName']
        elif form_data.get('fullName'):
            logger.info(f"Resume has name '{parsed_data.get('resume_candidate_name')}', form name '{form_data.get('fullName')}' stored in metadata only")
        
        if form_data.get('email') and (not parsed_data.get('resume_contact_info') or parsed_data.get('resume_contact_info') == 'Not mentioned'):
            parsed_data['resume_contact_info'] = form_data['email']
        elif form_data.get('email'):
            logger.info(f"Resume has email '{parsed_data.get('resume_contact_info')}', form email '{form_data.get('email')}' stored in metadata only")
        
        if form_data.get('phone'):
            # Store phone in parsed_data for reference (not in strict schema but useful)
            parsed_data['phone'] = form_data['phone']
        
        # Merge form skills with resume skills
        form_skills_str = form_data.get('form_skills') or form_data.get('skills')
        if form_skills_str:
            resume_skills = parsed_data.get('resume_technical_skills', [])
            merged_skills = merge_skills(resume_skills, form_skills_str)
            parsed_data['resume_technical_skills'] = merged_skills
            parsed_data['all_skills'] = merged_skills
    
    # Step 5: Ensure all_skills is populated (merge resume_technical_skills if not already merged)
    if not parsed_data.get('all_skills'):
        parsed_data['all_skills'] = normalize_skills(parsed_data.get('resume_technical_skills', []))
    
    # Step 6: Validate against ParsedResume schema
    try:
        validated = ParsedResume(**parsed_data)
        return validated.model_dump()
    except Exception as e:
        logger.warning(f"Schema validation failed, using parsed data as-is: {e}")
        return parsed_data

def fallback_parse_resume(text: str) -> Dict:
    """
    Traditional resume parsing using regex and pattern matching
    Used as fallback when OpenAI is unavailable
    Returns: Dict matching ParsedResume schema
    """
    logger.info("Using fallback resume parsing")
    
    name = extract_name(text)
    email = extract_email(text)
    skills = extract_skills(text)
    experience = extract_experience_years(text)
    
    result = {
        "resume_candidate_name": name if name else "Not mentioned",
        "resume_contact_info": email if email else "Not mentioned",
        "resume_role": "Not mentioned",  # Fallback can't reliably extract this
        "resume_location": "Not mentioned",
        "resume_degree": "Not mentioned",
        "resume_university": "Not mentioned",
        "resume_experience": experience,
        "resume_technical_skills": normalize_skills(skills),
        "resume_projects": [],
        "resume_achievements": [],
        "resume_certificates": [],
        "all_skills": normalize_skills(skills)
    }
    
    return result

def extract_email(text: str) -> str:
    """Extract email using regex"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else ""

def extract_phone(text: str) -> str:
    """Extract phone number using regex"""
    phone_pattern = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}'
    matches = re.findall(phone_pattern, text)
    return matches[0] if matches else ""

def extract_name(text: str) -> str:
    """Extract name (usually first line or first few words)"""
    lines = text.strip().split('\n')
    if lines:
        # Take first non-empty line
        for line in lines:
            if line.strip() and len(line.strip()) < 50:
                return line.strip()
    return ""

def extract_summary(text: str) -> str:
    """Extract professional summary"""
    summary_keywords = ['summary', 'objective', 'profile', 'about']
    lines = text.lower().split('\n')
    
    for i, line in enumerate(lines):
        if any(keyword in line for keyword in summary_keywords):
            # Get next 3-5 lines as summary
            summary_lines = lines[i+1:i+6]
            return ' '.join([l.strip() for l in summary_lines if l.strip()])
    
    return ""

def extract_skills(text: str) -> List[str]:
    """Extract skills using common tech keywords (returns lowercase)"""
    common_skills = [
        'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin',
        'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'Spring', 'Express',
        'SQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'Cassandra',
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'Git',
        'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision',
        'HTML', 'CSS', 'TypeScript', 'REST', 'GraphQL', 'Microservices'
    ]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in common_skills:
        if skill.lower() in text_lower:
            found_skills.append(skill.lower())  # Return lowercase
    
    return list(set(found_skills))  # Remove duplicates

def extract_experience_years(text: str) -> float:
    """Extract years of experience using pattern matching"""
    # Look for patterns like "5 years", "5+ years", "3-5 years"
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'experience\s*:?\s*(\d+)\+?\s*years?',
        r'(\d+)\+?\s*yrs'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            try:
                return float(matches[0])
            except:
                pass
    
    return 0.0
