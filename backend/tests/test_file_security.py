import pytest
from src.utils.validators import validate_file_signature

def test_valid_pdf_signature():
    # Real PDF signature: %PDF-
    pdf_content = b"\x25\x50\x44\x46-1.4\n..."
    assert validate_file_signature(pdf_content, "pdf") is True
    assert validate_file_signature(pdf_content, ".PDF") is True

def test_invalid_pdf_signature():
    # Malicious text file disguised as PDF
    malicious_content = b"<?php echo 'malicious'; ?>"
    assert validate_file_signature(malicious_content, "pdf") is False

def test_valid_docx_signature():
    # Real DOCX signature: PK..
    docx_content = b"\x50\x4B\x03\x04\x14\x00..."
    assert validate_file_signature(docx_content, "docx") is True

def test_invalid_docx_signature():
    # Text file disguised as DOCX
    malicious_content = b"Some random text content"
    assert validate_file_signature(malicious_content, "docx") is False

def test_empty_content():
    assert validate_file_signature(b"", "pdf") is False

def test_unsupported_extension():
    pdf_content = b"\x25\x50\x44\x46-1.4\n..."
    assert validate_file_signature(pdf_content, "exe") is False
