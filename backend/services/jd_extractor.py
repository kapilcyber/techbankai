import json
from typing import Dict, List
from utils.logger import get_logger
from .openai_service import extract_jd_requirements as _extract_jd_requirements

logger = get_logger(__name__)

async def extract_jd_requirements(jd_text: str) -> Dict:
    """Wrapper to extract JD requirements using OpenAI service"""
    logger.info("JD extractor: extracting requirements via OpenAI service")
    return await _extract_jd_requirements(jd_text)

async def extract_jd_keywords(jd_text: str) -> List[str]:
    """Derive keywords from JD requirements output"""
    try:
        req = await extract_jd_requirements(jd_text)
        keywords = req.get("keywords", [])
        required = req.get("required_skills", [])
        preferred = req.get("preferred_skills", [])
        # Merge and de-duplicate
        merged = list({*(keywords or []), *(required or []), *(preferred or [])})
        return merged
    except Exception as e:
        logger.error(f"JD keyword extraction failed: {e}")
        return []

