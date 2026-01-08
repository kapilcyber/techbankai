from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from src.models.resume import Resume
from src.config.database import get_postgres_db
from src.middleware.auth_middleware import get_admin_user
from src.services.resume_parser import parse_resume
from src.utils.logger import get_logger
import base64
import tempfile
import os

logger = get_logger(__name__)
router = APIRouter(prefix="/api/resumes/gmail", tags=["Gmail Resume Uploads"])

@router.post("/webhook")
async def gmail_webhook(
    request: Request,
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Gmail webhook endpoint for processing resume attachments
    Accepts Gmail push notification payload
    Queues Celery task for async processing
    """
    try:
        # Parse Gmail webhook payload
        payload = await request.json()
        
        # Extract Gmail message data
        message_id = payload.get('messageId') or payload.get('message_id')
        sender = payload.get('sender') or payload.get('from')
        subject = payload.get('subject')
        attachment_data = payload.get('attachment') or payload.get('attachment_data')
        
        if not message_id:
            raise HTTPException(status_code=400, detail="Missing message_id in payload")
        
        if not attachment_data:
            raise HTTPException(status_code=400, detail="Missing attachment data in payload")
        
        # Decode attachment if base64 encoded
        if isinstance(attachment_data, str):
            try:
                attachment_bytes = base64.b64decode(attachment_data)
            except Exception:
                attachment_bytes = attachment_data.encode() if isinstance(attachment_data, str) else attachment_data
        else:
            attachment_bytes = attachment_data
        
        # Save attachment to temporary file
        file_extension = payload.get('file_extension', 'pdf')
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
            tmp_file.write(attachment_bytes)
            tmp_file_path = tmp_file.name
        
        try:
            # Parse resume
            logger.info(f"Parsing Gmail resume: message_id={message_id}")
            parsed_data = await parse_resume(tmp_file_path, file_extension)
            
            # Determine file URL (for now, use local path; later integrate with Google Drive)
            file_url = f"/uploads/resumes/{message_id}.{file_extension}"
            
            # Check if resume with this message_id already exists
            from sqlalchemy import select
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
                    'subject': subject,
                    'received_at': payload.get('received_at')
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
                        'subject': subject,
                        'received_at': payload.get('received_at')
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
            
            return {
                'success': True,
                'message': 'Gmail resume processed successfully',
                'message_id': message_id
            }
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gmail webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


