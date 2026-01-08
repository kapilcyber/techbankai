"""
Test script to verify deterministic scoring architecture.

This tests:
1. Consistency (same resume → same score)
2. Score range (0-100)
3. Penalties and bonuses
"""

import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.services import openai_service
from src.services.matching_engine import calculate_match_score
from src.config.settings import settings

async def test_deterministic_scoring():
    print("=" * 80)
    print("TESTING DETERMINISTIC SCORING ARCHITECTURE")
    print("=" * 80)
    
    # Check OpenAI Key
    if not settings.openai_api_key:
        print("❌ ERROR: OpenAI API Key not found")
        return

    # Sample JD (Network Security Lead - 8+ years)
    jd_text = """
    Job Title: Network Security Lead
    Experience: 8+ years required
    
    Responsibilities:
    - Lead enterprise security architecture and implementation
    - Manage Palo Alto NGFW, IDS/IPS, and DDoS mitigation (Arbor)
    - Handle P1/P2 incidents and escalation management
    - Ensure PCI-DSS and ISO 27001 compliance
    - Mentor junior security engineers
    
    Required Skills:
    - Palo Alto Networks, Fortinet, or similar NGFW
    - AWS/Azure cloud security
    - Python scripting for automation
    - SIEM (Splunk, QRadar)
    - BGP, OSPF, MPLS routing protocols
    
    Mandatory Certifications:
    - CISSP or CISM required
    - CCIE Security preferred
    """
    
    print("\n[1] Extracting JD Requirements...")
    try:
        jd_reqs = await openai_service.extract_jd_requirements(jd_text)
        print("✅ JD Requirements extracted")
        print(f"   Min Experience: {jd_reqs.get('min_experience_years')} years")
        print(f"   Role Level: {jd_reqs.get('job_level')}")
        
        if 'structured_requirements' in jd_reqs:
            print("✅ Structured requirements found")
            weights = {k: v.get('weight', 0) for k, v in jd_reqs['structured_requirements'].items() if isinstance(v, dict)}
            print(f"   Total Weight: {sum(weights.values())}")
    except Exception as e:
        print(f"❌ JD Extraction Failed: {e}")
        return

    # Sample Resume (Strong candidate - 9 years, banking experience)
    resume_data = {
        'resume_candidate_name': "Test Candidate",
        'role': "Senior Security Engineer",
        'experience_years': 9,
        'skills': ["Palo Alto", "AWS", "Python", "Splunk", "BGP", "MPLS", "Fortinet"],
        'certifications': ["CISSP", "AWS Certified Security"],
        'summary': "Senior security engineer with 9 years of experience in banking sector. Led security architecture for enterprise-scale deployments.",
        'raw_text': """
        Senior Security Engineer | ABC Bank | 2018-Present
        - Led implementation of Palo Alto NGFW across 50+ branches
        - Designed and owned AWS security architecture for cloud migration
        - Managed P1 incident response and escalation procedures
        - Ensured PCI-DSS compliance for payment processing systems
        - Mentored team of 5 junior security engineers
        
        Security Engineer | XYZ Finance | 2015-2018
        - Implemented Splunk SIEM for security monitoring
        - Configured BGP and MPLS routing for secure WAN
        - Assisted with ISO 27001 audit preparation
        """,
        'resume_pages': 3  # Within limit
    }
    
    print("\n[2] Testing Deterministic Scoring...")
    print("   Running analysis 3 times to verify consistency...")
    
    scores = []
    for run in range(3):
        try:
            result = await calculate_match_score(resume_data, jd_reqs)
            score = result['total_score']
            scores.append(score)
            
            if run == 0:
                # Print detailed breakdown on first run
                print(f"\n   Run {run + 1}: Score = {score}/100")
                print(f"   Method: {result.get('method')}")
                print(f"   Role Fit: {result['factor_breakdown'].get('role_fit')}")
                
                bonuses_penalties = result['factor_breakdown'].get('bonuses_penalties', {})
                print(f"\n   Bonuses: +{bonuses_penalties.get('bonus', 0)}")
                for reason in bonuses_penalties.get('bonus_reasons', []):
                    print(f"      • {reason}")
                
                print(f"   Penalties: {bonuses_penalties.get('penalty', 0)}")
                for reason in bonuses_penalties.get('penalty_reasons', []):
                    print(f"      • {reason}")
                
                print(f"\n   Key Strengths:")
                for strength in result.get('matched_skills', [])[:3]:
                    print(f"      ✓ {strength}")
                
                print(f"\n   Key Gaps:")
                for gap in result.get('missing_skills', [])[:3]:
                    print(f"      ✗ {gap}")
            else:
                print(f"   Run {run + 1}: Score = {score}/100")
                
        except Exception as e:
            print(f"❌ Scoring Failed (Run {run + 1}): {e}")
            import traceback
            traceback.print_exc()
            return
    
    # Verify consistency
    print("\n[3] Consistency Check...")
    if len(set(scores)) == 1:
        print(f"   ✅ PASS: All 3 runs returned same score ({scores[0]})")
    else:
        print(f"   ❌ FAIL: Scores varied: {scores}")
    
    # Verify score range
    print("\n[4] Score Range Check...")
    if all(0 <= s <= 100 for s in scores):
        print(f"   ✅ PASS: All scores within 0-100 range")
    else:
        print(f"   ❌ FAIL: Scores outside valid range")
    
    # Verify expected score range for this candidate
    print("\n[5] Expected Score Range Check...")
    avg_score = sum(scores) / len(scores)
    if 75 <= avg_score <= 95:
        print(f"   ✅ PASS: Score {avg_score} is in expected range (75-95) for strong candidate")
    else:
        print(f"   ⚠️  WARNING: Score {avg_score} outside expected range (75-95)")
        print(f"      This candidate should score high (9 years, banking, CISSP, led teams)")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_deterministic_scoring())
