from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from datetime import datetime, timedelta
from src.models.resume import Resume
from src.models.jd_analysis import JDAnalysis, MatchResult
from src.models.user_db import User
from src.config.database import get_postgres_db
from src.middleware.auth_middleware import get_admin_user
from src.utils.logger import get_logger
from src.utils.user_type_mapper import normalize_user_type, get_user_type_from_source_type
from src.utils.response_formatter import format_resume_response

logger = get_logger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Get dashboard statistics with breakdown by user type and upload trends (Admin only)"""
    try:
        # Get PostgreSQL stats (including users)
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()
        
        total_resumes_result = await db.execute(select(func.count(Resume.id)))
        total_resumes = total_resumes_result.scalar()
        
        total_jd_analyses_result = await db.execute(select(func.count(JDAnalysis.id)))
        total_jd_analyses = total_jd_analyses_result.scalar()
        
        total_matches_result = await db.execute(select(func.count(MatchResult.id)))
        total_matches = total_matches_result.scalar()
        
        # Get breakdown by user type
        all_resumes_result = await db.execute(select(Resume))
        all_resumes = all_resumes_result.scalars().all()
        
        user_type_counts = {}
        user_type_skills = {}
        
        for resume in all_resumes:
            # Get user_type from meta_data or derive from source_type
            meta = resume.meta_data or {}
            user_type = meta.get('user_type')
            if not user_type:
                user_type = get_user_type_from_source_type(resume.source_type)
            user_type = normalize_user_type(user_type)
            
            # Count by user type
            user_type_counts[user_type] = user_type_counts.get(user_type, 0) + 1
            
            # Collect skills by user type
            if resume.skills:
                if user_type not in user_type_skills:
                    user_type_skills[user_type] = {}
                for skill in resume.skills:
                    user_type_skills[user_type][skill] = user_type_skills[user_type].get(skill, 0) + 1
        
        # Get top skills from all resumes
        all_skills_result = await db.execute(select(Resume.skills))
        all_skills = all_skills_result.scalars().all()
        skill_count = {}
        for skills in all_skills:
            if skills:
                for skill in skills:
                    skill_count[skill] = skill_count.get(skill, 0) + 1
        
        top_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Get top skills by user type
        top_skills_by_user_type = {}
        for user_type, skills_dict in user_type_skills.items():
            top_skills_by_user_type[user_type] = sorted(
                skills_dict.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        
        # Get upload trends (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        upload_trends_query = select(
            func.date(Resume.uploaded_at).label('date'),
            func.count(Resume.id).label('count')
        ).where(
            Resume.uploaded_at >= thirty_days_ago
        ).group_by(
            func.date(Resume.uploaded_at)
        ).order_by(
            func.date(Resume.uploaded_at)
        )
        trends_result = await db.execute(upload_trends_query)
        trends_data = trends_result.all()
        
        upload_trends = [
            {
                'date': row.date.isoformat() if row.date else None,
                'count': row.count
            }
            for row in trends_data
        ]
        
        # Get recent uploads with formatted responses
        recent_resumes_query = select(Resume).order_by(Resume.uploaded_at.desc()).limit(5)
        recent_resumes_result = await db.execute(recent_resumes_query)
        recent_resumes = recent_resumes_result.scalars().all()
        
        # Get recent JD analyses
        recent_jd_query = select(JDAnalysis).order_by(JDAnalysis.submitted_at.desc()).limit(5)
        recent_jd_result = await db.execute(recent_jd_query)
        recent_jd = recent_jd_result.scalars().all()
        
        return {
            'total_users': total_users,
            'total_resumes': total_resumes,
            'total_jd_analyses': total_jd_analyses,
            'total_matches': total_matches,
            'user_type_breakdown': user_type_counts,
            'top_skills': [{'skill': skill, 'count': count} for skill, count in top_skills],
            'top_skills_by_user_type': {
                ut: [{'skill': skill, 'count': count} for skill, count in skills_list]
                for ut, skills_list in top_skills_by_user_type.items()
            },
            'upload_trends': upload_trends,
            'recent_resumes': [
                format_resume_response(r)
                for r in recent_resumes
            ],
            'recent_jd_analyses': [
                {
                    'job_id': jd.job_id,
                    'filename': jd.jd_filename,
                    'submitted_at': jd.submitted_at.isoformat() if jd.submitted_at else None
                }
                for jd in recent_jd
            ]
        }
    
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """List all users (Admin only)"""
    try:
        total_result = await db.execute(select(func.count(User.id)))
        total = total_result.scalar()
        
        users_query = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        users_result = await db.execute(users_query)
        users = users_result.scalars().all()
        
        return {
            'total': total,
            'skip': skip,
            'limit': limit,
            'users': [
                {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'mode': user.mode or 'user',
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
                for user in users
            ]
        }
    
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Delete user (Admin only)"""
    try:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()
        
        logger.info(f"Deleted user: {user_id}")
        return {"message": "User deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/resumes/bulk")
async def bulk_delete_resumes(
    resume_ids: list[int],
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Bulk delete resumes (Admin only)"""
    try:
        deleted_count = 0
        for resume_id in resume_ids:
            query = select(Resume).where(Resume.id == resume_id)
            result = await db.execute(query)
            resume = result.scalar_one_or_none()
            if resume:
                await db.execute(delete(Resume).where(Resume.id == resume_id))
                deleted_count += 1
        
        await db.commit()
        
        logger.info(f"Bulk deleted {deleted_count} resumes")
        return {
            'message': f'Successfully deleted {deleted_count} resumes',
            'deleted_count': deleted_count
        }
    
    except Exception as e:
        logger.error(f"Bulk delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
