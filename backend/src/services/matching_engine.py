"""Matching engine for resume-JD matching."""
from typing import Dict, List
from src.services import openai_service
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def calculate_match_score(resume_data: Dict, jd_requirements: Dict) -> Dict:
    """
    Calculate match score using Deterministic Scoring Architecture.
    
    RULE: GPT reasons. Backend decides. Numbers never come from the model.
    
    Flow:
    1. GPT-4o → Qualitative judgments (match level, ownership, evidence)
    2. Backend → Numeric calculations (deterministic, auditable)
    """
    from src.services import deterministic_scorer
    
    try:
        # Step 1: Get qualitative judgments from GPT-4o
        qualitative_judgments = await openai_service.calculate_intelligent_match(resume_data, jd_requirements)
        
        logger.info(f"GPT qualitative analysis complete for {resume_data.get('resume_candidate_name', 'Unknown')}")
        
        # Step 2: Extract JD weights from structured requirements
        structured_jd = jd_requirements.get('structured_requirements', {})
        jd_weights = {}
        for category, data in structured_jd.items():
            if isinstance(data, dict) and 'weight' in data:
                jd_weights[category] = data.get('weight', 0)
        
        # Step 3: Calculate final score using deterministic backend logic
        scoring_result = deterministic_scorer.calculate_final_score(
            qualitative_judgments=qualitative_judgments,
            jd_weights=jd_weights,
            resume_data=resume_data,
            jd_requirements=jd_requirements
        )
        
        # Step 4: Map to expected response format (for backward compatibility)
        section_scores = scoring_result.get('section_scores', {})
        
        # Helper to safely get score
        def get_score(category):
            return section_scores.get(category, {}).get('score', 0) if isinstance(section_scores.get(category), dict) else 0

        # Map to legacy fields
        return {
            'total_score': scoring_result.get('overall_score', 0),
            # Map legacy scores to relevant sections (approximate aggregation)
            'skill_match': get_score('core_technical_skills') + get_score('security_technologies') + get_score('networking_protocols'),
            'experience_match': get_score('experience_seniority') + get_score('incident_operations'),
            'semantic_score': get_score('compliance_governance') + get_score('cloud_architecture'),
            
            # Universal Fit Score fields
            'universal_fit_score': scoring_result.get('overall_score', 0),
            'skill_evidence_score': get_score('core_technical_skills'),
            'execution_score': get_score('experience_seniority'),
            'complexity_score': get_score('cloud_architecture'),
            'learning_agility_score': get_score('certifications'),
            'domain_context_score': get_score('compliance_governance'),
            'communication_score': 0.0, 
            
            # Detailed breakdown (NEW - deterministic)
            'matched_skills': scoring_result.get('key_strengths', []),
            'missing_skills': scoring_result.get('key_gaps', []),
            'match_explanation': " | ".join(scoring_result.get('why_this_score', [])),
            'factor_breakdown': {
                'section_scores': section_scores,
                'role_fit': scoring_result.get('role_fit'),
                'key_strengths': scoring_result.get('key_strengths', []),
                'key_gaps': scoring_result.get('key_gaps', []),
                'recommended_role': scoring_result.get('recommended_role'),
                'why_this_score': scoring_result.get('why_this_score', []),
                'bonuses_penalties': scoring_result.get('bonuses_penalties', {}),
                'base_score': scoring_result.get('base_score', 0)
            },
            'method': 'deterministic_scoring_v1'
        }
    except Exception as e:
        logger.error(f"Deterministic scoring failed: {e}")
        import traceback
        traceback.print_exc()
        return _calculate_traditional_fallback(resume_data, jd_requirements)
    except Exception as e:
        logger.error(f"Universal Fit Score calculation failed, using fallback: {e}")
        # Fallback to traditional scoring if Universal Fit Scorer fails
        return _calculate_traditional_fallback(resume_data, jd_requirements)


def _calculate_traditional_fallback(resume_data: Dict, jd_requirements: Dict) -> Dict:
    """
    Fallback to traditional scoring if Universal Fit Scorer fails.
    This is the old 3-factor model for emergency use only.
    """
    skill_match = calculate_skill_match(
        resume_data.get('skills', []),
        jd_requirements.get('required_skills', [])
    )
    
    exp_match = calculate_experience_match(
        resume_data.get('experience_years', 0),
        jd_requirements.get('min_experience_years', 0)
    )
    
    keyword_match = calculate_keyword_match(
        resume_data.get('raw_text', ''),
        jd_requirements.get('keywords', [])
    )
    
    traditional_score = (skill_match * 0.4) + (exp_match * 0.3) + (keyword_match * 0.3)
    
    return {
        'total_score': round(traditional_score, 2),
        'skill_match': round(skill_match, 2),
        'experience_match': round(exp_match, 2),
        'semantic_score': round(keyword_match, 2),
        'learning_agility_score': 0.0,
        'domain_context_score': 0.0,
        'communication_score': 0.0,
        'matched_skills': [],
        'missing_skills': [],
        'match_explanation': 'Fallback traditional scoring used',
        'factor_breakdown': {},
        'method': 'traditional_fallback'
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
    """Calculate skill overlap percentage with smart substring support."""
    if not required_skills:
        return 70.0  # Be optimistic if no requirements are set
    
    # Normalize skills to lowercase for comparison
    resume_skills_lower = [s.lower().strip() for s in resume_skills if s and len(s) > 1]
    required_skills_lower = [s.lower().strip() for s in required_skills if s and len(s) > 1]
    
    if not required_skills_lower:
        return 70.0

    matched_count = 0
    for req_skill in required_skills_lower:
        is_matched = False
        # 1. Exact or simple substring match
        for res_skill in resume_skills_lower:
            if req_skill == res_skill or req_skill in res_skill or res_skill in req_skill:
                is_matched = True
                break
        
        # 2. Smart overlap for multi-word skills (e.g. "Palo Alto Threat Protection" matches "Palo Alto")
        if not is_matched and " " in req_skill:
            req_parts = set(req_skill.split())
            if len(req_parts) > 1:
                for res_skill in resume_skills_lower:
                    res_parts = set(res_skill.split())
                    # If 50% of the words in the required skill are present in the resume skill
                    overlap = req_parts.intersection(res_parts)
                    if len(overlap) >= max(1, len(req_parts) // 2):
                        is_matched = True
                        break
        
        if is_matched:
            matched_count += 1
            
    match_percentage = (matched_count / len(required_skills_lower)) * 100
    return min(match_percentage, 100.0)


def calculate_experience_match(resume_exp: float, required_exp: float) -> float:
    """Calculate experience match score with more generous thresholds for Phase 1."""
    # Harden against NoneType
    if resume_exp is None: resume_exp = 0
    if required_exp is None: required_exp = 0

    if required_exp == 0:
        return 100.0
    
    if resume_exp >= required_exp:
        return 100.0
    
    # More generous scaling for Phase 1 (to let GPT-4o decide in Phase 3)
    ratio = resume_exp / required_exp
    return (ratio * 80) + 20 # Minimum 20 points if they have ANY experience


def calculate_keyword_match(resume_text: str, keywords: List[str]) -> float:
    """Calculate keyword match percentage with boundary checks."""
    if not keywords:
        return 70.0
    
    resume_text_lower = resume_text.lower()
    matched = 0
    for keyword in keywords:
        kw_lower = keyword.lower().strip()
        if not kw_lower: continue
        
        # Check if keyword is in text
        if kw_lower in resume_text_lower:
            matched += 1
        # Smart check for multi-word keywords
        elif " " in kw_lower:
            parts = kw_lower.split()
            if all(p in resume_text_lower for p in parts if len(p) > 2):
                matched += 1
                
    match_percentage = (matched / len(keywords)) * 100
    return min(match_percentage, 100.0)

