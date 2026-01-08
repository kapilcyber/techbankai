from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from src.models.jd_analysis import JDAnalysis, MatchResult
from src.models.resume import Resume
from src.models.user_db import User
from src.config.database import get_postgres_db
from src.middleware.auth_middleware import get_admin_user, get_current_user
from src.services.storage import save_uploaded_file
from src.services.file_processor import extract_text_from_file
from src.services import openai_service
from src.services.matching_engine import calculate_match_score, calculate_traditional_score
from src.utils.validators import validate_file_type
from src.utils.logger import get_logger
from src.utils.user_type_mapper import normalize_user_type, get_user_type_from_source_type, get_source_type_from_user_type
from src.utils.response_formatter import format_resume_response
from src.config.settings import settings
import asyncio

logger = get_logger(__name__)
router = APIRouter(prefix="/api/jd", tags=["JD Analysis"])

ALLOWED_EXTENSIONS = ['pdf', 'docx']

def fix_file_url(url: str) -> str:
    """Helper to fix relative file URLs for frontend consumption."""
    if url and url.startswith('/'):
        # Use simple localhost construction as fallback
        return f"http://localhost:{settings.port}{url}"
    return url

@router.post("/analyze")
async def analyze_jd(
    file: Optional[UploadFile] = File(None),
    jd_text_manual: Optional[str] = Form(None),
    min_score: int = Query(10, ge=0, le=100, description="Minimum match score threshold"),
    top_n: int = Query(10, ge=1, le=50, description="Number of top candidates to return"),
    user_types: Optional[List[str]] = Query(None, description="Filter by source types"),
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Upload JD file or provide JD text and get top matching candidates
    """
    try:
        jd_text = ""
        jd_filename = "Manual Entry"
        
        if file and file.filename:
            # Step 1: Validate file type
            if not validate_file_type(file.filename, ALLOWED_EXTENSIONS):
                raise HTTPException(status_code=400, detail=f"Invalid file type. Only {', '.join([e.upper() for e in ALLOWED_EXTENSIONS])} allowed.")
            
            # Step 2: Save JD file
            logger.info(f"Saving JD file: {file.filename}")
            file_path, file_url = await save_uploaded_file(file, subfolder="jd")
            file_extension = file.filename.split('.')[-1]
            jd_filename = file.filename
            
            # Step 3: Extract text from JD
            logger.info("Extracting text from JD")
            jd_text = extract_text_from_file(file_path, file_extension)
        elif jd_text_manual:
            logger.info("Using manual JD text entry")
            jd_text = jd_text_manual.strip()
            jd_filename = "Manual Entry"
            
        if not jd_text:
            logger.error(f"No JD text found. manual_entry_len: {len(jd_text_manual) if jd_text_manual else 0}")
            raise HTTPException(status_code=400, detail="Please provide either a JD file or JD text")
        
        logger.info(f"Proceeding with JD text (length: {len(jd_text)})")
        
        # Step 4: Extract JD requirements using OpenAI
        logger.info("Analyzing JD with OpenAI GPT-4")
        jd_requirements = await openai_service.extract_jd_requirements(jd_text)
        
        # Step 5: Generate unique job ID
        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        
        # Step 6: Save JD analysis to database
        jd_analysis = JDAnalysis(
            job_id=job_id,
            jd_filename=jd_filename,
            jd_text=jd_text,
            extracted_keywords=jd_requirements.get('keywords', []),
            required_skills=jd_requirements.get('required_skills', []),
            preferred_skills=jd_requirements.get('preferred_skills', []),
            required_experience=jd_requirements.get('min_experience_years', 0),
            education=jd_requirements.get('education', ''),
            job_level=jd_requirements.get('job_level', ''),
            submitted_by=current_user['email']
        )
        
        db.add(jd_analysis)
        await db.commit()
        
        logger.info(f"JD analysis saved with job_id: {job_id}")
        
        # Step 7: Fetch all resumes from database (filter by source_type if provided)
        logger.info("Fetching all resumes for matching")
        query = select(Resume).options(
            selectinload(Resume.work_history),
            selectinload(Resume.certificates)
        )
        if user_types and len(user_types) > 0:
            # Map user_types to source_types
            source_types = [get_source_type_from_user_type(normalize_user_type(ut)) for ut in user_types]
            query = query.where(Resume.source_type.in_(source_types))
        result = await db.execute(query)
        all_resumes = result.scalars().all()
        total_resumes = len(all_resumes)
        
        logger.info(f"Found {total_resumes} resumes to match against.")
        logger.info(f"JD Requirements: Skills={len(jd_requirements.get('required_skills', []))}, Keywords={len(jd_requirements.get('keywords', []))}")
        
        # Step 8: Calculate match scores using two-phase concurrency and caching
        matches = []
        existing_results_query = select(MatchResult).where(MatchResult.job_id == job_id)
        existing_results_result = await db.execute(existing_results_query)
        existing_results_list = existing_results_result.scalars().all()
        existing_results = {mr.resume_id: mr for mr in existing_results_list}

        # Phase 1: Traditional scoring for all resumes (fast)
        prelim = []
        for resume in all_resumes:
            try:
                parsed = resume.parsed_data or {}
                # Fallback strategy: Clean skills
                extracted_skills = resume.skills or parsed.get('resume_technical_skills', []) or parsed.get('all_skills', [])
                if isinstance(extracted_skills, str):
                    extracted_skills = [s.strip() for s in extracted_skills.split(',') if s.strip()]
                    
                resume_data = {
                    'skills': extracted_skills,
                    'experience_years': resume.experience_years if resume.experience_years is not None else (parsed.get('resume_experience') or 0),
                    'raw_text': resume.raw_text or '',
                    'summary': parsed.get('summary', '') or (resume.raw_text[:500] if resume.raw_text else ''),
                    'education': f"{parsed.get('resume_degree', 'Not mentioned')} - {parsed.get('resume_university', 'Not mentioned')}",
                    'role': parsed.get('resume_role', getattr(resume, 'job_title', 'Not mentioned')), # Removed resume.role, checking job_title just in case
                    'certifications': parsed.get('resume_certificates', [])
                }
                
                # HARD FILTER: Check minimum experience requirement
                min_exp_required = jd_requirements.get('min_experience_years', 0)
                candidate_exp = resume_data['experience_years']
                
                if min_exp_required > 0 and candidate_exp < min_exp_required:
                    # Skip candidates who don't meet minimum experience
                    logger.debug(f"Resume {resume.id} filtered out: {candidate_exp} years < {min_exp_required} years required")
                    continue
            
                score = calculate_traditional_score(resume_data, jd_requirements)
                # LOGGING: Check why score might be low
                if score == 0:
                     logger.debug(f"Resume {resume.id} score 0. Data: Skills={len(resume_data['skills'])}, Exp={resume_data['experience_years']}")

                if score >= min_score:
                    prelim.append((resume, resume_data, score))
            except Exception as e:
                logger.error(f"Scoring/Processing failed for resume {resume.id}: {e}")

        logger.info(f"{len(prelim)}/{total_resumes} resumes passed minimum score {min_score} in phase 1")

        if len(prelim) < 5:
            logger.info("Phase 1 yielded too few results. Relaxing filter to include top potential candidates.")
            all_scored = []
            for resume in all_resumes:
                try:
                    parsed = resume.parsed_data or {}
                    extracted_skills = resume.skills or parsed.get('resume_technical_skills', []) or parsed.get('all_skills', [])
                    if isinstance(extracted_skills, str):
                        extracted_skills = [s.strip() for s in extracted_skills.split(',') if s.strip()]
                    resume_data = {
                        'skills': extracted_skills,
                        'experience_years': resume.experience_years if resume.experience_years is not None else (parsed.get('resume_experience') or 0),
                        'raw_text': resume.raw_text or '',
                        'summary': parsed.get('summary', '') or (resume.raw_text[:500] if resume.raw_text else ''),
                        'education': f"{parsed.get('resume_degree', 'Not mentioned')} - {parsed.get('resume_university', 'Not mentioned')}",
                        'role': parsed.get('resume_role', getattr(resume, 'job_title', 'Not mentioned')),
                        'certifications': parsed.get('resume_certificates', [])
                    }
                    
                    # HARD FILTER: Check minimum experience requirement (same as Phase 1)
                    min_exp_required = jd_requirements.get('min_experience_years', 0)
                    candidate_exp = resume_data['experience_years']
                    
                    if min_exp_required > 0 and candidate_exp < min_exp_required:
                        # Skip candidates who don't meet minimum experience
                        continue
                    
                    score = calculate_traditional_score(resume_data, jd_requirements)
                    all_scored.append((resume, resume_data, score))
                except Exception: continue
            all_scored.sort(key=lambda x: x[2], reverse=True)
            prelim = all_scored[:15]
            logger.info(f"Fallback: Passing top {len(prelim)} candidates to AI matching.")

        # Phase 2: Prepare data COMPLETELY DETACHED from DB session
        logger.info("Starting Phase 2: preparing detached data")
        try:
            # Convert all resume objects to plain dictionaries to avoid greenlet issues
            prelim_data = []
            
            # Pre-fetch user data for relocation stats
            emails = [r[0].uploaded_by for r in prelim if r[0].uploaded_by]
            user_map = {}
            if emails:
                try:
                    user_query = select(User).where(User.email.in_(emails))
                    user_result = await db.execute(user_query)
                    users_list = user_result.scalars().all()
                    user_map = {u.email.lower(): u for u in users_list}
                except Exception as e:
                    logger.warning(f"Failed to fetch user details: {e}")

            for resume, resume_data, score in prelim:
                try:
                    # format_resume_response creates a detached dictionary with all frontend fields
                    # Since we used selectinload, this is safe to call here
                    detached_data = format_resume_response(resume)
                    
                    # Add relocation info from User table
                    user = user_map.get(resume.uploaded_by.lower()) if resume.uploaded_by else None
                    if user:
                        detached_data['ready_to_relocate'] = user.ready_to_relocate
                        detached_data['preferred_location'] = user.preferred_location
                        detached_data['notice_period'] = user.notice_period
                    else:
                        meta = resume.meta_data or {}
                        user_prof = meta.get('user_profile', {})
                        detached_data['ready_to_relocate'] = meta.get('ready_to_relocate', False)
                        detached_data['preferred_location'] = user_prof.get('location', 'Not mentioned')
                        detached_data['notice_period'] = meta.get('notice_period', 0)

                    # Map resume_id consistently for downstream matching
                    detached_data['resume_id'] = resume.id
                    detached_data['source_type'] = resume.source_type
                    detached_data['source_id'] = resume.source_id
                    
                    # Add fields specifically needed for UniversalFitScorer (mapping from parsed_data or resume_data)
                    parsed = resume.parsed_data or {}
                    detached_data.update({
                        'resume_candidate_name': detached_data.get('name'),
                        'resume_role': detached_data.get('role'),
                        'resume_experience': detached_data.get('experience_years', 0),
                        'resume_degree': parsed.get('resume_degree', 'Not mentioned'),
                        'resume_university': parsed.get('resume_university', 'Not mentioned'),
                        'resume_location': detached_data.get('location'),
                        'resume_technical_skills': detached_data.get('skills', []),
                        'resume_certificates': parsed.get('resume_certificates', []),
                        'resume_achievements': parsed.get('resume_achievements', []),
                        'raw_text': resume.raw_text or '',
                        'summary': parsed.get('summary', '') or (resume.raw_text[:500] if resume.raw_text else '')
                    })
                    
                    # Ensure we don't lose the pre-calculated resume_data (skills, etc.)
                    detached_data.update(resume_data)
                    
                    prelim_data.append(detached_data)
                except Exception as ie:
                    logger.error(f"Error preparing resume {resume.id}: {ie}")
                    continue
            
            logger.info(f"Phase 2 complete: Prepared {len(prelim_data)} items for AI analysis")
            
        except Exception as e:
             logger.error(f"Phase 2 processing failed: {e}")
             raise e
        
        # Phase 3: AI-enhanced scoring with DETACHED data (no DB session access)
        semaphore = asyncio.Semaphore(5)
        async def score_resume(detached_data):
            try:
                resume_id = detached_data['resume_id']
                
                # Use cached result if already computed
                cached = existing_results.get(resume_id)
                if cached:
                    return {
                        **detached_data,
                        'match_score': cached.match_score,
                        'skill_match': cached.skill_match_score,
                        'experience_match': cached.experience_match_score,
                        'semantic_score': cached.semantic_score,
                        'matched_skills': cached.keyword_matches.get('matched_skills', []) if cached.keyword_matches else [],
                        'missing_skills': cached.keyword_matches.get('missing_skills', []) if cached.keyword_matches else [],
                        'match_explanation': cached.match_explanation,
                        'candidate_name': detached_data.get('name')
                    }, False
                
                # Calculate match score - now completely isolated from DB
                async with semaphore:
                    score_result = await calculate_match_score(detached_data, jd_requirements)
                    
                    return {
                        **detached_data,
                        'match_score': score_result['total_score'],
                        'skill_match': score_result['skill_match'],
                        'experience_match': score_result['experience_match'],
                        'semantic_score': score_result['semantic_score'],
                        'matched_skills': score_result['matched_skills'],
                        'missing_skills': score_result['missing_skills'],
                        'match_explanation': score_result['match_explanation'],
                        'learning_agility_score': score_result.get('learning_agility_score', 0.0),
                        'domain_context_score': score_result.get('domain_context_score', 0.0),
                        'communication_score': score_result.get('communication_score', 0.0),
                        'factor_breakdown': score_result.get('factor_breakdown', {}),
                        'candidate_name': detached_data.get('name')
                    }, True
            except Exception as e:
                logger.error(f"Error matching resume {detached_data.get('resume_id')}: {e}")
                return None, False

        # Run scoring tasks with detached data (NO database access here)
        tasks = [score_resume(data) for data in prelim_data]
        results = await asyncio.gather(*tasks)

        for result, should_persist in results:
            if not result:
                continue
            if result['match_score'] >= min_score:
                matches.append(result)
                if should_persist:
                    db.add(MatchResult(
                        job_id=job_id,
                        resume_id=result['resume_id'],
                        source_type=result.get('source_type'),
                        source_id=result.get('source_id'),
                        # Legacy fields (for backward compatibility)
                        match_score=result['match_score'],
                        skill_match_score=result['skill_match'],
                        experience_match_score=result['experience_match'],
                        semantic_score=result['semantic_score'],
                        keyword_matches={
                            'matched_skills': result['matched_skills'],
                            'missing_skills': result['missing_skills']
                        },
                        match_explanation=result['match_explanation'],
                        # NEW: Universal Fit Score fields
                        universal_fit_score=result['match_score'],
                        skill_evidence_score=result['skill_match'],
                        execution_score=result['experience_match'],
                        complexity_score=result['semantic_score'],
                        learning_agility_score=result.get('learning_agility_score', 0.0),
                        domain_context_score=result.get('domain_context_score', 0.0),
                        communication_score=result.get('communication_score', 0.0),
                        factor_breakdown=result.get('factor_breakdown', {})
                    ))

        await db.commit()
        
        # Step 9: Sort by score and return top N
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        top_matches = matches[:top_n]
        
        logger.info(f"JD Analysis complete: {len(matches)} matches found, returning top {len(top_matches)}")
        
        return {
            'job_id': job_id,
            'jd_filename': jd_filename,
            'total_resumes_analyzed': total_resumes,
            'total_matches': len(matches),
            'min_score_threshold': min_score,
            'jd_requirements': {
                'required_skills': jd_requirements.get('required_skills', []),
                'preferred_skills': jd_requirements.get('preferred_skills', []),
                'min_experience_years': jd_requirements.get('min_experience_years', 0),
                'education': jd_requirements.get('education', ''),
                'job_level': jd_requirements.get('job_level', '')
            },
            'top_matches': top_matches
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"JD Analysis error: {e}")
        logger.error(f"Full traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"JD Analysis failed: {str(e)}")

@router.get("/results/{job_id}")
async def get_jd_results(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Get saved JD analysis results"""
    try:
        # Get JD analysis
        jd_query = select(JDAnalysis).where(JDAnalysis.job_id == job_id)
        jd_result = await db.execute(jd_query)
        jd_analysis = jd_result.scalar_one_or_none()
        
        if not jd_analysis:
            raise HTTPException(status_code=404, detail="JD analysis not found")
        
        # Get match results
        match_query = select(MatchResult).where(
            MatchResult.job_id == job_id
        ).order_by(MatchResult.match_score.desc())
        match_result = await db.execute(match_query)
        match_results = match_result.scalars().all()
        
        # Fetch resume details for each match
        matches = []
        for match in match_results:
            resume_query = select(Resume).where(Resume.id == match.resume_id)
            resume_result = await db.execute(resume_query)
            resume = resume_result.scalar_one_or_none()
            

            if resume:
                base_response = format_resume_response(resume)
                matches.append({
                    **base_response,
                    'resume_id': resume.id,
                    'match_score': match.match_score,
                    'skill_match': match.skill_match_score,
                    'experience_match': match.experience_match_score,
                    'semantic_score': match.semantic_score,
                    # NEW: Universal Fit Score factors
                    'universal_fit_score': match.universal_fit_score or match.match_score,
                    'skill_evidence_score': match.skill_evidence_score or match.skill_match_score,
                    'execution_score': match.execution_score or match.experience_match_score,
                    'complexity_score': match.complexity_score or match.semantic_score,
                    'learning_agility_score': match.learning_agility_score or 0.0,
                    'domain_context_score': match.domain_context_score or 0.0,
                    'communication_score': match.communication_score or 0.0,
                    'notice_period': getattr(match, 'notice_period', 0), # Fallback if not in schema yet
                    'factor_breakdown': match.factor_breakdown or {},
                    # Legacy fields
                    'matched_skills': match.keyword_matches.get('matched_skills', []) if match.keyword_matches else [],
                    'missing_skills': match.keyword_matches.get('missing_skills', []) if match.keyword_matches else [],
                    'match_explanation': match.match_explanation,
                    'candidate_name': base_response.get('name')
                })
        
        return {
            'job_id': job_id,
            'jd_filename': jd_analysis.jd_filename,
            'submitted_at': jd_analysis.submitted_at.isoformat() if jd_analysis.submitted_at else None,
            'submitted_by': jd_analysis.submitted_by,
            'jd_requirements': {
                'required_skills': jd_analysis.required_skills,
                'preferred_skills': jd_analysis.preferred_skills,
                'min_experience_years': jd_analysis.required_experience,
                'education': jd_analysis.education,
                'job_level': jd_analysis.job_level
            },
            'total_matches': len(matches),
            'matches': matches
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get JD results error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_jd_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Get JD analysis history"""
    try:
        total_result = await db.execute(select(func.count(JDAnalysis.id)))
        total = total_result.scalar()
        
        jd_query = select(JDAnalysis).order_by(
            JDAnalysis.submitted_at.desc()
        ).offset(skip).limit(limit)
        jd_result = await db.execute(jd_query)
        jd_analyses = jd_result.scalars().all()
        
        history = []
        for jd in jd_analyses:
            # Count matches for this JD
            match_count_result = await db.execute(
                select(func.count(MatchResult.id)).where(MatchResult.job_id == jd.job_id)
            )
            match_count = match_count_result.scalar()
            
            history.append({
                'job_id': jd.job_id,
                'jd_filename': jd.jd_filename,
                'submitted_at': jd.submitted_at.isoformat() if jd.submitted_at else None,
                'submitted_by': jd.submitted_by,
                'total_matches': match_count,
                'required_skills': jd.required_skills,
                'job_level': jd.job_level
            })
        
        return {
            'total': total,
            'skip': skip,
            'limit': limit,
            'history': history
        }
    
    except Exception as e:
        logger.error(f"Get JD history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
