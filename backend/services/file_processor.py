import PyPDF2
import pdfplumber
from docx import Document
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file using pdfplumber (more accurate)
    Falls back to PyPDF2 if pdfplumber fails
    """
    try:
        # Try pdfplumber first (better for complex PDFs)
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            if text.strip():
                logger.info(f"Extracted {len(text)} characters from PDF using pdfplumber")
                return text.strip()
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}, trying PyPDF2")
    
    # Fallback to PyPDF2
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            logger.info(f"Extracted {len(text)} characters from PDF using PyPDF2")
            return text.strip()
    except Exception as e:
        logger.error(f"Failed to extract PDF text: {e}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        logger.info(f"Extracted {len(text)} characters from DOCX")
        return text.strip()
    except Exception as e:
        logger.error(f"Failed to extract DOCX text: {e}")
        return ""

def extract_text_from_doc(file_path: str) -> str:
    """
    Extract text from DOC file (old format)
    Note: This requires additional libraries like antiword or conversion
    For now, return empty and log warning
    """
    logger.warning("DOC format not fully supported, please convert to DOCX or PDF")
    return ""

def extract_text_from_file(file_path: str, file_extension: str) -> str:
    """
    Extract text from file based on extension
    """
    ext = file_extension.lower().replace('.', '')
    
    if ext == 'pdf':
        return extract_text_from_pdf(file_path)
    elif ext == 'docx':
        return extract_text_from_docx(file_path)
    elif ext == 'doc':
        return extract_text_from_doc(file_path)
    else:
        logger.error(f"Unsupported file extension: {ext}")
        return ""
