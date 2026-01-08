from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import uuid
from datetime import datetime
from src.models.jd_analysis import JDAnalysis, MatchResult
from src.models.resume import Resume
from src.config.database import get_postgres_db
from src.middleware.auth_middleware import get_admin_user, get_current_user
from src.services.storage import save_uploaded_file
from src.services.file_processor import extract_text_from_file
from src.services import openai_service
from src.services.matching_engine import calculate_match_score, calculate_traditional_score
from src.utils.validators import validate_file_type
from src.utils.logger import get_logger
from src.utils.user_type_mapper import normalize_user_type, get_user_type_from_source_type, get_source_type_from_user_type
import asyncio

logger = get_logger(__name__)
router = APIRouter(prefix="/api/jd", tags=["JD Analysis"])

ALLOWED_EXTENSIONS = ['pdf', 'docx', 'doc']

@router.post("/analyze")
async def analyze_jd(
    file: UploadFile = File(...),
    min_score: int = Query(80, ge=0, le=100, description="Minimum match score threshold"),
    top_n: int = Query(10, ge=1, le=50, description="Number of top candidates to return"),
    user_types: List[str] = Query(None, description="Filter by source types"),
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Upload JD file and get top matching candidates
    This is the core JD analysis feature
    """
    try:
        # Step 1: Validate file type
        if not validate_file_type(file.filename, ALLOWED_EXTENSIONS):
            raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOC, DOCX allowed.")
        
        # Step 2: Save JD file
        logger.info(f"Saving JD file: {file.filename}")
        file_path, file_url = await save_uploaded_file(file, subfolder="jd")
        file_extension = file.filename.split('.')[-1]
        
        # Step 3: Extract text from JD
        logger.info("Extracting text from JD")
        jd_text = extract_text_from_file(file_path, file_extension)
        
        if not jd_text:
            raise HTTPException(status_code=400, detail="Failed to extract text from JD file")
        
        # Step 4: Extract JD requirements using OpenAI
        logger.info("Analyzing JD with OpenAI GPT-4")
        jd_requirements = await openai_service.extract_jd_requirements(jd_text)
        
        # Step 5: Generate unique job ID
        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        
        # Step 6: Save JD analysis to database
        jd_analysis = JDAnalysis(
            job_id=job_id,
            jd_filename=file.filename,
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
        query = select(Resume)
        if user_types:
            # Map user_types to source_types
            source_types = [get_source_type_from_user_type(normalize_user_type(ut)) for ut in user_types]
            query = query.where(Resume.source_type.in_(source_types))
        result = await db.execute(query)
        all_resumes = result.scalars().all()
        total_resumes = len(all_resumes)
        
        logger.info(f"Found {total_resumes} resumes to match against")
        
        # Step 8: Calculate match scores using two-phase concurrency and caching
        matches = []
        existing_results_query = select(MatchResult).where(MatchResult.job_id == job_id)
        existing_results_result = await db.execute(existing_results_query)
        existing_results_list = existing_results_result.scalars().all()
        existing_results = {mr.resume_id: mr for mr in existing_results_list}
        logger.info(f"Found {len(existing_results)} existing match results for caching")

        # Phase 1: Traditional scoring for all resumes (fast)
        prelim = []
        for resume in all_resumes:
            resume_data = {
                'skills': resume.skills or [],
                'experience_years': resume.experience_years or 0,
                'raw_text': resume.raw_text or '',
                'summary': resume.parsed_data.get('summary', '') if resume.parsed_data else '',
                'education': resume.parsed_data.get('education', []) if resume.parsed_data else []
            }
            try:
                score = calculate_traditional_score(resume_data, jd_requirements)
                if score >= min_score:
                    prelim.append((resume, resume_data, score))
            except Exception as e:
                logger.error(f"Traditional scoring failed for resume {resume.id}: {e}")

        logger.info(f"{len(prelim)} resumes passed minimum score {min_score} in phase 1")

        # Phase 2: AI-enhanced scoring concurrently for prelim candidates, skip if cached
        semaphore = asyncio.Semaphore(5)
        async def score_resume(resume, resume_data):
            try:
                # Use cached result if already computed
                cached = existing_results.get(resume.id)
                if cached:
                    # Get normalized user_type
                    meta = resume.meta_data or {}
                    user_type = meta.get('user_type')
                    if not user_type:
                        user_type = get_user_type_from_source_type(resume.source_type)
                    user_type = normalize_user_type(user_type)
                    
                    parsed = resume.parsed_data or {}
                    return {
                        'resume_id': resume.id,
                        'source_type': resume.source_type,
                        'user_type': user_type,  # Add normalized user_type
                        'source_id': resume.source_id,
                        'candidate_name': parsed.get('resume_candidate_name', parsed.get('name', 'Unknown')),
                        'email': parsed.get('resume_contact_info', parsed.get('email', '')),
                        'role': parsed.get('resume_role', parsed.get('role', 'Not mentioned')),
                        'location': parsed.get('resume_location', parsed.get('location', 'Not mentioned')),
                        'match_score': cached.match_score,
                        'skill_match': cached.skill_match_score,
                        'experience_match': cached.experience_match_score,
                        'semantic_score': cached.semantic_score,
                        'matched_skills': cached.keyword_matches.get('matched_skills', []) if cached.keyword_matches else [],
                        'missing_skills': cached.keyword_matches.get('missing_skills', []) if cached.keyword_matches else [],
                        'match_explanation': cached.match_explanation,
                        'file_url': resume.file_url,
                        'experience_years': resume.experience_years,
                        'all_skills': resume.skills,
                        'parsed_data': parsed  # Include full parsed_data
                    }, False
                async with semaphore:
                    score_result = await calculate_match_score(resume_data, jd_requirements)
                    # Get normalized user_type
                    meta = resume.meta_data or {}
                    user_type = meta.get('user_type')
                    if not user_type:
                        user_type = get_user_type_from_source_type(resume.source_type)
                    user_type = normalize_user_type(user_type)
                    
                    parsed = resume.parsed_data or {}
                    return {
                        'resume_id': resume.id,
                        'source_type': resume.source_type,
                        'user_type': user_type,  # Add normalized user_type
                        'source_id': resume.source_id,
                        'candidate_name': parsed.get('resume_candidate_name', parsed.get('name', 'Unknown')),
                        'email': parsed.get('resume_contact_info', parsed.get('email', '')),
                        'role': parsed.get('resume_role', parsed.get('role', 'Not mentioned')),
                        'location': parsed.get('resume_location', parsed.get('location', 'Not mentioned')),
                        'match_score': score_result['total_score'],
                        'skill_match': score_result['skill_match'],
                        'experience_match': score_result['experience_match'],
                        'semantic_score': score_result['semantic_score'],
                        'matched_skills': score_result['matched_skills'],
                        'missing_skills': score_result['missing_skills'],
                        'match_explanation': score_result['match_explanation'],
                        'file_url': resume.file_url,
                        'experience_years': resume.experience_years,
                        'all_skills': resume.skills,
                        'parsed_data': parsed  # Include full parsed_data
                    }, True
            except Exception as e:
                logger.error(f"Error matching resume {resume.id}: {e}")
                return None, False

        tasks = [score_resume(resume, data) for (resume, data, _) in prelim]
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
                        match_score=result['match_score'],
                        skill_match_score=result['skill_match'],
                        experience_match_score=result['experience_match'],
                        semantic_score=result['semantic_score'],
                        keyword_matches={
                            'matched_skills': result['matched_skills'],
                            'missing_skills': result['missing_skills']
                        },
                        match_explanation=result['match_explanation']
                    ))

        await db.commit()
        
        # Step 9: Sort by score and return top N
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        top_matches = matches[:top_n]
        
        logger.info(f"JD Analysis complete: {len(matches)} matches found, returning top {len(top_matches)}")
        
        return {
            'job_id': job_id,
            'jd_filename': file.filename,
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
        logger.error(f"JD Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
                # Get normalized user_type
                meta = resume.meta_data or {}
                user_type = meta.get('user_type')
                if not user_type:
                    user_type = get_user_type_from_source_type(resume.source_type)
                user_type = normalize_user_type(user_type)
                
                parsed = resume.parsed_data or {}
                matches.append({
                    'resume_id': resume.id,
                    'source_type': resume.source_type,
                    'user_type': user_type,  # Add normalized user_type
                    'source_id': resume.source_id,
                    'candidate_name': parsed.get('resume_candidate_name', parsed.get('name', 'Unknown')),
                    'email': parsed.get('resume_contact_info', parsed.get('email', '')),
                    'role': parsed.get('resume_role', parsed.get('role', 'Not mentioned')),
                    'location': parsed.get('resume_location', parsed.get('location', 'Not mentioned')),
                    'match_score': match.match_score,
                    'skill_match': match.skill_match_score,
                    'experience_match': match.experience_match_score,
                    'semantic_score': match.semantic_score,
                    'matched_skills': match.keyword_matches.get('matched_skills', []) if match.keyword_matches else [],
                    'missing_skills': match.keyword_matches.get('missing_skills', []) if match.keyword_matches else [],
                    'match_explanation': match.match_explanation,
                    'file_url': resume.file_url,
                    'experience_years': resume.experience_years,
                    'all_skills': resume.skills,
                    'parsed_data': parsed  # Include full parsed_data
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
