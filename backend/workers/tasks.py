from workers.celery_app import celery_app
from services.resume_parser import parse_resume
from services.storage import StorageService
from models.resume import Resume
from config.database import AsyncSessionLocal
from sqlalchemy import select
from utils.logger import get_logger
import base64
import tempfile
import os

logger = get_logger(__name__)

@celery_app.task(name="workers.tasks.process_gmail_resume")
def process_gmail_resume(message_id: str, attachment_data: bytes, sender: str = None, subject: str = None):
    """
    Process Gmail resume attachment (Celery task)
    This runs asynchronously in the background
    """
    import asyncio
    
    async def _process():
        db = AsyncSessionLocal()
        try:
            # Decode attachment if base64 encoded
            if isinstance(attachment_data, str):
                try:
                    attachment_bytes = base64.b64decode(attachment_data)
                except Exception:
                    attachment_bytes = attachment_data.encode() if isinstance(attachment_data, str) else attachment_data
            else:
                attachment_bytes = attachment_data
            
            # Save attachment to temporary file
            file_extension = 'pdf'  # Default, could be determined from attachment metadata
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
                tmp_file.write(attachment_bytes)
                tmp_file_path = tmp_file.name
            
            try:
                # Parse resume
                logger.info(f"Processing Gmail resume: message_id={message_id}")
                parsed_data = await parse_resume(tmp_file_path, file_extension)
                
                # Determine file URL (upload to storage)
                # For now, save locally; later integrate with Google Drive
                from fastapi import UploadFile
                from io import BytesIO
                
                # Create a file-like object for storage service
                file_obj = BytesIO(attachment_bytes)
                file_obj.name = f"{message_id}.{file_extension}"
                
                # Upload to storage (Google Drive or local)
                # Note: This is a simplified version; in production, you'd use proper async file handling
                file_url = f"/uploads/resumes/{message_id}.{file_extension}"
                
                # Check if resume with this message_id already exists
                query = select(Resume).where(
                    Resume.source_type == 'gmail',
                    Resume.source_id == message_id
                )
                result = await db.execute(query)
                existing_resume = result.scalar_one_or_none()
                
                if existing_resume:
                    # Update existing record
                    existing_resume.filename = f"{message_id}.{file_extension}"
                    existing_resume.file_url = file_url
                    existing_resume.parsed_data = parsed_data
                    existing_resume.skills = parsed_data.get('all_skills', parsed_data.get('resume_technical_skills', []))
                    existing_resume.experience_years = parsed_data.get('resume_experience', 0)
                    existing_resume.source_metadata = {
                        'message_id': message_id,
                        'sender': sender,
                        'subject': subject
                    }
                    await db.commit()
                    await db.refresh(existing_resume)
                    logger.info(f"Updated Gmail resume: {message_id}")
                else:
                    # Create new record
                    resume = Resume(
                        filename=f"{message_id}.{file_extension}",
                        file_url=file_url,
                        source_type='gmail',
                        source_id=message_id,
                        source_metadata={
                            'message_id': message_id,
                            'sender': sender,
                            'subject': subject
                        },
                        raw_text=parsed_data.get('raw_text', ''),
                        parsed_data=parsed_data,
                        skills=parsed_data.get('all_skills', parsed_data.get('resume_technical_skills', [])),
                        experience_years=parsed_data.get('resume_experience', 0),
                        uploaded_by=sender or 'gmail@unknown.com',
                        meta_data={
                            'parsing_method': parsed_data.get('parsing_method', 'unknown'),
                            'gmail_metadata': {
                                'sender': sender,
                                'subject': subject
                            }
                        }
                    )
                    
                    db.add(resume)
                    await db.commit()
                    await db.refresh(resume)
                    logger.info(f"Successfully processed Gmail resume: {message_id}")
            
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
        
        except Exception as e:
            logger.error(f"Error processing Gmail resume {message_id}: {e}")
            raise
        finally:
            await db.close()
    
    # Run async function
    asyncio.run(_process())
    return {"status": "success", "message_id": message_id}


