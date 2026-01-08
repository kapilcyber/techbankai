"""
Deterministic Scoring Engine - Backend-Controlled Numeric Calculations

RULE: GPT reasons. Backend decides. Numbers never come from the model.

This module contains all hard-coded scoring logic to ensure:
- Consistency (same resume → same score)
- No score inflation
- Full auditability
- Deterministic behavior
"""

from typing import Dict, List, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# HARD-CODED SCORE MAPS (NEVER CHANGE WITHOUT APPROVAL)
# ============================================================================

# Match Level + Ownership → Score Multiplier
MATCH_SCORE_MAP = {
    ("HIGH", "LED"): 0.90,
    ("HIGH", "OWNED"): 0.85,
    ("HIGH", "CONTRIBUTED"): 0.75,
    ("MEDIUM", "LED"): 0.75,
    ("MEDIUM", "OWNED"): 0.70,
    ("MEDIUM", "CONTRIBUTED"): 0.60,
    ("MEDIUM", "ASSISTED"): 0.50,
    ("LOW", "OWNED"): 0.50,
    ("LOW", "CONTRIBUTED"): 0.40,
    ("LOW", "ASSISTED"): 0.30,
    ("NO", "NONE"): 0.00,
    ("NONE", "NONE"): 0.00,
}

# Fallback for unknown combinations
DEFAULT_MULTIPLIER = 0.40

# ============================================================================
# SECTION SCORE CALCULATION
# ============================================================================

def calculate_section_score(
    match_level: str,
    ownership: str,
    weight: float,
    recent: bool = True
) -> float:
    """
    Calculate score for a single JD category.
    
    Args:
        match_level: HIGH, MEDIUM, LOW, NO, NONE
        ownership: LED, OWNED, CONTRIBUTED, ASSISTED, NONE
        weight: Category weight from JD (e.g., 20 for 20%)
        recent: Whether experience is from last 5 years
        
    Returns:
        Section score (0 to weight)
    """
    # Normalize inputs
    match_level = match_level.upper().strip()
    ownership = ownership.upper().strip()
    
    # Get multiplier from map
    multiplier = MATCH_SCORE_MAP.get(
        (match_level, ownership),
        DEFAULT_MULTIPLIER
    )
    
    # Calculate base score
    score = weight * multiplier
    
    # Apply recency adjustment
    if not recent:
        score *= 0.85  # 15% penalty for old experience
    
    return round(score, 2)


# ============================================================================
# PENALTY SYSTEM (ANTI-INFLATION)
# ============================================================================

def calculate_penalties(resume_data: Dict, jd_requirements: Dict) -> Tuple[int, List[str]]:
    """
    Calculate penalties based on resume quality issues.
    
    Returns:
        (total_penalty, penalty_reasons)
    """
    penalty = 0
    reasons = []
    
    # 1. Resume Length Penalty
    resume_pages = resume_data.get('resume_pages', 0)
    if resume_pages > 4:
        penalty -= 2
        reasons.append(f"Resume too long ({resume_pages} pages > 4 pages)")
    
    # 2. Missing Mandatory Certifications
    required_certs = jd_requirements.get('structured_requirements', {}).get('certifications', {}).get('items', [])
    candidate_certs = resume_data.get('certifications', [])
    
    # Normalize for comparison
    required_certs_lower = [c.lower() for c in required_certs]
    candidate_certs_lower = [c.lower() for c in candidate_certs]
    
    missing_mandatory = []
    for req_cert in required_certs_lower:
        # Check if any candidate cert contains the required cert
        if not any(req_cert in cand_cert or cand_cert in req_cert for cand_cert in candidate_certs_lower):
            missing_mandatory.append(req_cert)
    
    if missing_mandatory and len(missing_mandatory) > 0:
        penalty -= min(len(missing_mandatory), 3)  # Max -3 for missing certs
        reasons.append(f"Missing certifications: {', '.join(missing_mandatory[:2])}")
    
    # 3. Career Drift Detection (simplified)
    # Check if resume has irrelevant keywords
    raw_text = resume_data.get('raw_text', '').lower()
    irrelevant_keywords = ['sales', 'marketing', 'hr', 'finance', 'accounting']
    
    jd_domain_keywords = []
    for cat in ['core_technical_skills', 'security_technologies', 'networking_protocols']:
        items = jd_requirements.get('structured_requirements', {}).get(cat, {}).get('items', [])
        jd_domain_keywords.extend([item.lower() for item in items])
    
    # If resume has many irrelevant keywords and few domain keywords
    irrelevant_count = sum(1 for kw in irrelevant_keywords if kw in raw_text)
    domain_count = sum(1 for kw in jd_domain_keywords[:10] if kw in raw_text)
    
    if irrelevant_count > 3 and domain_count < 3:
        penalty -= 1
        reasons.append("Career drift detected (irrelevant experience)")
    
    return penalty, reasons


# ============================================================================
# BONUS SYSTEM (LIMITED & CAPPED)
# ============================================================================

def calculate_bonuses(resume_data: Dict, qualitative_judgments: Dict) -> Tuple[int, List[str]]:
    """
    Calculate bonuses for exceptional qualifications.
    
    Returns:
        (total_bonus, bonus_reasons)
    """
    bonus = 0
    reasons = []
    
    # 1. Regulated Domain Experience (Banking, Finance, Healthcare)
    raw_text = resume_data.get('raw_text', '').lower()
    regulated_keywords = ['banking', 'finance', 'healthcare', 'fintech', 'payment', 'pci-dss', 'sox', 'hipaa']
    
    if any(kw in raw_text for kw in regulated_keywords):
        bonus += 1
        reasons.append("Regulated industry experience (Banking/Finance/Healthcare)")
    
    # 2. Global/Enterprise Scale Ownership
    # Check if multiple categories show "LED" ownership
    led_count = sum(
        1 for cat_data in qualitative_judgments.values()
        if isinstance(cat_data, dict) and cat_data.get('ownership', '').upper() == 'LED'
    )
    
    if led_count >= 3:  # Led in 3+ categories
        bonus += 1
        reasons.append("Enterprise-scale leadership across multiple domains")
    
    # Cap bonus at +2
    bonus = min(bonus, 2)
    
    return bonus, reasons


# ============================================================================
# FINAL SCORE CALCULATION
# ============================================================================

def calculate_final_score(
    qualitative_judgments: Dict,
    jd_weights: Dict,
    resume_data: Dict,
    jd_requirements: Dict
) -> Dict:
    """
    Calculate final score using deterministic backend logic.
    
    Args:
        qualitative_judgments: GPT's qualitative output (match_level, ownership, evidence)
        jd_weights: Category weights from JD decomposition
        resume_data: Resume metadata
        jd_requirements: Full JD requirements
        
    Returns:
        Complete scoring result with breakdown
    """
    section_scores = {}
    section_details = {}
    
    # Calculate each section score
    for category, judgment in qualitative_judgments.items():
        if not isinstance(judgment, dict):
            continue
            
        match_level = judgment.get('match_level', 'NO')
        ownership = judgment.get('ownership', 'NONE')
        evidence = judgment.get('evidence', '')
        recent = judgment.get('recent', True)
        
        # Get weight for this category
        weight = jd_weights.get(category, 0)
        
        # Calculate section score
        score = calculate_section_score(match_level, ownership, weight, recent)
        
        section_scores[category] = score
        section_details[category] = {
            'score': score,
            'max': weight,
            'match_level': match_level,
            'ownership': ownership,
            'evidence': evidence,
            'recent': recent
        }
    
    # Calculate penalties
    penalty, penalty_reasons = calculate_penalties(resume_data, jd_requirements)
    
    # Calculate bonuses
    bonus, bonus_reasons = calculate_bonuses(resume_data, qualitative_judgments)
    
    # Calculate overall score
    base_score = sum(section_scores.values())
    overall_score = base_score + bonus + penalty
    overall_score = max(0, min(100, round(overall_score)))
    
    # Determine role fit
    if overall_score >= 80:
        role_fit = "Strong Fit"
    elif overall_score >= 60:
        role_fit = "Partial Fit"
    else:
        role_fit = "Weak Fit"
    
    # Extract strengths and gaps from evidence
    strengths = []
    gaps = []
    
    for category, details in section_details.items():
        if details['match_level'] in ['HIGH', 'MEDIUM'] and details['score'] > 0:
            if details['evidence']:
                strengths.append(f"{category.replace('_', ' ').title()}: {details['evidence']}")
        elif details['match_level'] in ['LOW', 'NO', 'NONE']:
            gaps.append(f"Limited {category.replace('_', ' ')}")
    
    # Add penalty reasons to gaps
    gaps.extend(penalty_reasons)
    
    # Build "why this score" explanation
    why_this_score = []
    for category, details in section_details.items():
        if details['score'] > 0:
            why_this_score.append(
                f"{category.replace('_', ' ').title()}: {details['match_level']} ({details['ownership']}) - {details['evidence'][:80]}"
            )
    
    # Add bonus/penalty summary
    if bonus > 0:
        why_this_score.extend(bonus_reasons)
    if penalty < 0:
        why_this_score.extend([f"Penalty: {reason}" for reason in penalty_reasons])
    
    return {
        'overall_score': overall_score,
        'base_score': round(base_score, 2),
        'role_fit': role_fit,
        'section_scores': section_details,
        'bonuses_penalties': {
            'bonus': bonus,
            'bonus_reasons': bonus_reasons,
            'penalty': penalty,
            'penalty_reasons': penalty_reasons
        },
        'key_strengths': strengths[:5],  # Top 5
        'key_gaps': gaps[:5],  # Top 5
        'why_this_score': why_this_score[:7],  # Top 7
        'recommended_role': _determine_recommended_role(section_details, overall_score)
    }


def _determine_recommended_role(section_details: Dict, overall_score: int) -> str:
    """Determine recommended role based on section strengths."""
    # Find strongest category
    strongest_cat = max(
        section_details.items(),
        key=lambda x: x[1]['score'] if isinstance(x[1], dict) else 0
    )
    
    category_name = strongest_cat[0].replace('_', ' ').title()
    
    if overall_score >= 80:
        return f"Senior {category_name} Lead"
    elif overall_score >= 60:
        return f"{category_name} Specialist"
    else:
        return f"Junior {category_name} Role"
