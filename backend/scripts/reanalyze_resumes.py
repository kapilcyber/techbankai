import asyncio
import sys
import os

# Add parent directory to path to allow imports from src
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from src.config.database import AsyncSessionLocal
from src.models.resume import Resume, Experience, Certification
from src.services import openai_service
from src.services.file_processor import extract_text_from_file
from src.utils.logger import get_logger

logger = get_logger("reanalyze_resumes")

async def reanalyze_resume_id(resume_id, current_index, total_count):
    async with AsyncSessionLocal() as session:
        try:
            # Fetch resume with relationships
            result = await session.execute(
                select(Resume).where(Resume.id == resume_id).options(
                    selectinload(Resume.work_history),
                    selectinload(Resume.certificates)
                )
            )
            resume = result.scalar()
            if not resume:
                return False

            logger.info(f"🔄 Analyzing [{current_index}/{total_count}] {resume.filename}...")

            # 1. Ensure we have raw text
            raw_text = resume.raw_text
            if not raw_text:
                file_path = resume.file_url.lstrip('/')
                absolute_file_path = os.path.join(parent_dir, file_path)
                
                if os.path.exists(absolute_file_path):
                    ext = absolute_file_path.split('.')[-1]
                    logger.info(f"📄 Extracting text from {absolute_file_path}...")
                    raw_text = extract_text_from_file(absolute_file_path, ext)
                    resume.raw_text = raw_text
                else:
                    logger.warning(f"⚠️ File not found at {absolute_file_path}. Skipping.")
                    return False

            if not raw_text or len(raw_text.strip()) < 50:
                logger.warning(f"⚠️ Resume {resume.id} has insufficient text. Skipping.")
                return False
            
            # 2. Use updated GPT-4o parser
            parsed_data = await openai_service.parse_resume_with_gpt(raw_text)
            
            # 3. Update core fields
            resume.parsed_data = parsed_data
            
            skills = parsed_data.get('resume_technical_skills', [])
            if not skills:
                skills = parsed_data.get('all_skills', [])
            resume.skills = skills
            
            try:
                resume.experience_years = float(parsed_data.get('resume_experience', 0.0))
            except (TypeError, ValueError):
                resume.experience_years = 0.0
            
            # Update meta
            if resume.meta_data is None:
                resume.meta_data = {}
            temp_meta = dict(resume.meta_data)
            temp_meta['last_analyzed_model'] = 'gpt-4o'
            resume.meta_data = temp_meta
            
            # 4. Repopulate work history (Experiences)
            # Use relationship instead of direct delete for safer cascade
            resume.work_history = []
            
            work_history = parsed_data.get('work_history', [])
            if not work_history and "resume_key_responsibilities" in parsed_data:
                work_history = [{"description": r} for r in parsed_data["resume_key_responsibilities"]]

            for item in work_history:
                exp = Experience(
                    resume_id=resume.id,
                    company=str(item.get('company', 'Not mentioned'))[:250],
                    role=str(item.get('role', 'Not mentioned'))[:250],
                    location=str(item.get('location', 'Not mentioned'))[:250],
                    start_date=str(item.get('start_date', 'Not mentioned'))[:45],
                    end_date=str(item.get('end_date', 'Not mentioned'))[:45],
                    is_current=int(item.get('is_current', 0)),
                    description=str(item.get('description', 'Not mentioned'))
                )
                resume.work_history.append(exp)
            
            # 5. Repopulate certifications
            resume.certificates = []
            for cert_name in parsed_data.get('resume_certificates', []):
                if cert_name and isinstance(cert_name, str):
                    cert = Certification(
                        resume_id=resume.id,
                        name=cert_name[:250]
                    )
                    resume.certificates.append(cert)
            
            session.add(resume)
            await session.commit()
            logger.info(f"✅ Re-analyzed {resume.filename} successfully.")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error analyzing resume {resume_id}: {str(e)}")
            await session.rollback()
            return False

async def reanalyze_all():
    # First, get all IDs
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Resume.id))
        resume_ids = result.scalars().all()
    
    logger.info(f"🚀 Starting re-analysis of {len(resume_ids)} resumes using GPT-4o...")
    
    success_count = 0
    for idx, r_id in enumerate(resume_ids):
        success = await reanalyze_resume_id(r_id, idx + 1, len(resume_ids))
        if success:
            success_count += 1
            
    logger.info(f"✨ Re-analysis complete! Processed {success_count}/{len(resume_ids)} resumes.")

if __name__ == "__main__":
    asyncio.run(reanalyze_all())
