import os
import logging
from typing import Union

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using pdfminer.six."""
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(file_path)
        logger.info(f"Extracted text from PDF: {file_path}")
        return text
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise Exception(f"PDF extraction failed: {e}")

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        import docx
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        text = '\n'.join(full_text)
        logger.info(f"Extracted text from DOCX: {file_path}")
        return text
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        raise Exception(f"DOCX extraction failed: {e}")

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from plain text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        logger.info(f"Extracted text from TXT: {file_path}")
        return text
    except Exception as e:
        logger.error(f"TXT extraction failed: {e}")
        raise Exception(f"TXT extraction failed: {e}")

def parse_resume(file_path: str) -> str:
    """
    Parse resume file and return extracted text.
    Supports PDF, DOCX, and TXT formats.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    _, ext = os.path.splitext(file_path.lower())

    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) != 2:
        print("Usage: python resume_parser.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        text = parse_resume(file_path)
        print(text[:500])  # Print first 500 characters
    except Exception as e:
        print(f"Error: {e}")