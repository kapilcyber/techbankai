"""
UniversalFitScorer - Strict ATS Candidate-JD Matching System

This service implements a rigorous matching algorithm following these priorities:
1. Key Responsibilities (Semantic Match)
2. Experience (Strict Year Thresholds)
3. Skillsets & Certifications
"""
from typing import Dict, List
import json
from src.services import openai_service
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UniversalFitScorer:
    """Calculate Universal Fit Score with strict ATS rules and dynamic weighting."""
    
    def __init__(self):
        """Initialize the Universal Fit Scorer."""
        pass
    
    async def calculate_universal_fit(
        self,
        resume_data: Dict,
        jd_requirements: Dict
    ) -> Dict:
        """
        Calculate comprehensive Universal Fit Score using GPT-4o deep analysis.
        Follows strict priority: Responsibilities > Experience > Skills.
        """
        try:
            # Analyze candidate vs JD with GPT-4o
            analysis = await self._analyze_with_gpt4o(resume_data, jd_requirements)
            
            logger.info(f"Universal Fit Score calculated for {resume_data.get('resume_candidate_name')}: {analysis['universal_fit_score']}")
            return analysis
            
        except Exception as e:
            logger.error(f"Universal Fit Score calculation failed: {e}")
            # Fallback to basic scoring if GPT-4o fails
            return self._fallback_scoring(resume_data, jd_requirements)
    
    async def _analyze_with_gpt4o(self, candidate_data: Dict, jd_requirements: Dict) -> Dict:
        """
        Use GPT-4o to perform deep ATS analysis with role classification and dynamic weighting.
        """
        client = openai_service.get_openai_client()
        if not client:
            raise ValueError("OpenAI client not initialized")
        
        system_prompt = """You are an ADVANCED ATS and Job Description-Resume Matching Engine.
Your objective is to generate an accurate ATS score (0-100) by STRICTLY following the priority order:
1. Key Responsibilities (Highest Importance)
2. Experience (Years & Seniority)
3. Skillsets & Certificates (Lowest Importance)

CLASSIFICATION RULES:
- Fresher: keywords: fresher, trainee, graduate, junior, or 0-1 year exp.
- Experienced: 2-5 years exp, independent role ownership.
- Senior: 6+ years exp, leadership/strategic responsibilities.

DYNAMIC WEIGHTING (PRIORITY PRESERVED):
- If role is Fresher: Responsibilities 50%, Experience 30%, Skills 20%
- If role is Experienced: Responsibilities 45%, Experience 35%, Skills 20%
- If role is Senior: Responsibilities 40%, Experience 40%, Skills 20%

SCORING RULES:
- STRICT EXPERIENCE RULE: If JD requires X years, and candidate has < X, penalize experience_match significantly. (Example: Requires 8y, candidate has 6y -> Score < 50 for experience).
- Match responsibilities by meaning, scope, and impact (Semantic matching).
- Skills without applied context in work history receive lower scores.
- DO NOT be generous. High scores (80%+) are reserved for near-perfect alignment.
"""

        user_prompt = f"""EVALUATE CANDIDATE FIT:

[JD REQUIREMENTS]
- Job Title/Level: {jd_requirements.get('job_level', 'Experienced')}
- Min Experience: {jd_requirements.get('min_experience_years', 0)} years
- Required Skills: {', '.join(jd_requirements.get('required_skills', []))}
- Key Responsibilities: {json.dumps(jd_requirements.get('key_responsibilities', []), indent=2)}

[CANDIDATE PROFILE]
- Name: {candidate_data.get('resume_candidate_name', 'Not mentioned')}
- Current Role: {candidate_data.get('resume_role', 'Not mentioned')}
- Experience: {candidate_data.get('resume_experience', candidate_data.get('experience_years', 0))} years
- Skills: {', '.join(candidate_data.get('resume_technical_skills', candidate_data.get('skills', [])))}
- Summary/Key Responsibilities: {candidate_data.get('summary', '')[:2000]}
- Certificates: {json.dumps(candidate_data.get('resume_certificates', []), indent=2)}

Analyze carefully. Apply strict logic for year thresholds.

RETURN JSON:
{{
  "role_classification": "Fresher" | "Experienced" | "Senior",
  "responsibility_match_score": 0.0-100.0,
  "experience_match_score": 0.0-100.0,
  "skill_match_score": 0.0-100.0,
  "universal_fit_score": 0.0-100.0,
  "explanation": "Brief reasoning focusing on priority criteria.",
  "matched_skills": [...],
  "missing_skills": [...]
}}
"""

        try:
            response = await client.chat.completions.create(
                model=openai_service.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=2048,
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Map back to internal storage structure
            mapped_result = {
                "universal_fit_score": result.get("universal_fit_score", 0),
                "skill_evidence_score": result.get("skill_match_score", 0),
                "execution_score": result.get("experience_match_score", 0),
                "complexity_score": result.get("responsibility_match_score", 0),
                "learning_agility_score": 0.0, 
                "domain_context_score": 0.0,
                "communication_score": 0.0,
                "overall_explanation": result.get("explanation", "Strict ATS Analysis complete."),
                "factor_breakdown": {
                    "role_classification": result.get("role_classification"),
                    "matched_skills": result.get("matched_skills", []),
                    "missing_skills": result.get("missing_skills", []),
                    "responsibility_alignment": result.get("responsibility_match_score", 0),
                    "experience_alignment": result.get("experience_match_score", 0)
                }
            }

            return mapped_result
        except Exception as e:
            logger.error(f"GPT-4o analysis failed: {e}")
            raise

    def _fallback_scoring(self, resume_data: Dict, jd_requirements: Dict) -> Dict:
        """
        Fallback scoring if GPT-4o is unavailable.
        """
        logger.warning("Using fallback scoring for Universal Fit Score")
        
        resume_skills = set([s.lower() for s in resume_data.get('resume_technical_skills', resume_data.get('skills', []))])
        required_skills = set([s.lower() for s in jd_requirements.get('required_skills', [])])
        
        if required_skills:
            skill_match = (len(resume_skills & required_skills) / len(required_skills)) * 100
        else:
            skill_match = 50.0
        
        resume_exp = resume_data.get('resume_experience', resume_data.get('experience_years', 0))
        required_exp = jd_requirements.get('min_experience_years', 0)
        
        if required_exp > 0:
            exp_match = min((resume_exp / required_exp) * 100, 100)
            if resume_exp < required_exp:
                exp_match *= 0.7 # Penalty
        else:
            exp_match = 100.0
        
        return {
            'universal_fit_score': round((skill_match * 0.20 + exp_match * 0.40 + 50 * 0.40), 2),
            'skill_evidence_score': round(skill_match, 2),
            'execution_score': round(exp_match, 2),
            'complexity_score': 50.0,
            'learning_agility_score': 0.0,
            'domain_context_score': 0.0,
            'communication_score': 0.0,
            'factor_breakdown': {
                'matched_skills': list(resume_skills & required_skills),
                'missing_skills': list(required_skills - resume_skills)
            },
            'overall_explanation': 'Fallback scoring used due to GPT-4o unavailability'
        }
