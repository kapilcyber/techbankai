from typing import Dict, List
from services import openai_service
from utils.logger import get_logger

logger = get_logger(__name__)

async def calculate_match_score(resume_data: Dict, jd_requirements: Dict) -> Dict:
    """
    Calculate match score using hybrid approach:
    Phase 1: Quick traditional scoring for filtering
    Phase 2: AI deep analysis for top candidates
    """
    # Phase 1: Traditional scoring (fast)
    traditional_score = calculate_traditional_score(resume_data, jd_requirements)
    
    # If score is too low, skip AI analysis (save API costs)
    if traditional_score < 70:
        return {
            'total_score': round(traditional_score, 2),
            'skill_match': 0,
            'experience_match': 0,
            'semantic_score': 0,
            'matched_skills': [],
            'missing_skills': [],
            'match_explanation': 'Low initial match score',
            'method': 'traditional'
        }
    
    # Phase 2: AI enhancement for promising candidates
    try:
        ai_analysis = await openai_service.calculate_intelligent_match(
            resume_data, jd_requirements
        )
        
        # Combine scores (70% traditional + 30% AI adjustment)
        final_score = (traditional_score * 0.7) + (ai_analysis.get('score', 0) * 0.3)
        
        return {
            'total_score': round(final_score, 2),
            'skill_match': ai_analysis.get('skill_match', 0),
            'experience_match': ai_analysis.get('experience_match', 0),
            'semantic_score': ai_analysis.get('semantic_score', 0),
            'matched_skills': ai_analysis.get('matched_skills', []),
            'missing_skills': ai_analysis.get('missing_skills', []),
            'match_explanation': ai_analysis.get('explanation', ''),
            'method': 'hybrid'
        }
    except Exception as e:
        logger.warning(f"AI matching failed, using traditional score: {e}")
        return {
            'total_score': round(traditional_score, 2),
            'skill_match': 0,
            'experience_match': 0,
            'semantic_score': 0,
            'matched_skills': [],
            'missing_skills': [],
            'match_explanation': 'AI analysis unavailable',
            'method': 'traditional'
        }

def calculate_traditional_score(resume_data: Dict, jd_requirements: Dict) -> float:
    """
    Traditional scoring algorithm:
    - Skill match: 40%
    - Experience match: 30%
    - Keyword match: 30%
    """
    skill_score = calculate_skill_match(
        resume_data.get('skills', []),
        jd_requirements.get('required_skills', [])
    ) * 0.4
    
    experience_score = calculate_experience_match(
        resume_data.get('experience_years', 0),
        jd_requirements.get('min_experience_years', 0)
    ) * 0.3
    
    keyword_score = calculate_keyword_match(
        resume_data.get('raw_text', ''),
        jd_requirements.get('keywords', [])
    ) * 0.3
    
    total_score = skill_score + experience_score + keyword_score
    return min(total_score, 100)  # Cap at 100

def calculate_skill_match(resume_skills: List[str], required_skills: List[str]) -> float:
    """Calculate skill overlap percentage"""
    if not required_skills:
        return 50.0  # Neutral score if no requirements
    
    # Normalize skills to lowercase for comparison
    resume_skills_lower = [s.lower() for s in resume_skills]
    required_skills_lower = [s.lower() for s in required_skills]
    
    matched = sum(1 for skill in required_skills_lower if skill in resume_skills_lower)
    match_percentage = (matched / len(required_skills)) * 100
    
    return match_percentage

def calculate_experience_match(resume_exp: float, required_exp: float) -> float:
    """Calculate experience match score"""
    if required_exp == 0:
        return 100.0  # No requirement
    
    if resume_exp >= required_exp:
        return 100.0  # Meets or exceeds requirement
    
    # Partial credit for close matches
    ratio = resume_exp / required_exp
    return ratio * 100

def calculate_keyword_match(resume_text: str, keywords: List[str]) -> float:
    """Calculate keyword match percentage"""
    if not keywords:
        return 50.0  # Neutral score
    
    resume_text_lower = resume_text.lower()
    matched = sum(1 for keyword in keywords if keyword.lower() in resume_text_lower)
    match_percentage = (matched / len(keywords)) * 100
    
    return match_percentage
