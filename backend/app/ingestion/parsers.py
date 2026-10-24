"""PDF parsing utilities."""
import logging
from pathlib import Path
from typing import List, Tuple

import pypdf

logger = logging.getLogger(__name__)


def parse_pdf(file_path: Path) -> List[Tuple[int, str]]:
    """
    Parse a PDF file and extract text with page numbers.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        List of (page_number, text) tuples. Page numbers start at 1.
        
    Raises:
        Exception: If PDF cannot be parsed
    """
    pages = []
    
    try:
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            num_pages = len(reader.pages)
            
            logger.info(f"Parsing PDF: {file_path.name} ({num_pages} pages)")
            
            for page_num in range(num_pages):
                try:
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    
                    if text and text.strip():
                        # Normalize whitespace
                        text = " ".join(text.split())
                        pages.append((page_num + 1, text))
                    else:
                        logger.debug(f"Page {page_num + 1} is empty")
                        
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num + 1}: {e}")
                    continue
                    
    except Exception as e:
        logger.error(f"Failed to parse PDF {file_path}: {e}")
        raise Exception(f"PDF parsing failed: {e}")
    
    if not pages:
        raise Exception("No text could be extracted from PDF")
    
    logger.info(f"Extracted {len(pages)} non-empty pages from {file_path.name}")
    return pages
