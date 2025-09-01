"""
Resume loader service for fetching resume text by ID
"""
import logging
from pathlib import Path
from typing import Optional
from .storage import PDFStorageService
from .resume_parser import ResumeParserService

logger = logging.getLogger(__name__)

class ResumeLoaderService:
    def __init__(self, upload_dir: str = "uploads"):
        """
        Initialize resume loader service
        
        Args:
            upload_dir: Directory where PDF files are stored
        """
        self.storage = PDFStorageService(upload_dir)
        self.parser = ResumeParserService()
    
    def get_resume_text(self, resume_id: str) -> Optional[str]:
        """
        Get the full text content of a resume by ID
        
        Args:
            resume_id: Unique identifier for the resume
            
        Returns:
            Full resume text or None if not found/failed to parse
        """
        try:
            # Get the PDF file path
            pdf_path = self.storage.get_pdf_path(resume_id)
            
            # Extract text from PDF
            full_text, _ = self.parser.extract_text(pdf_path)
            
            logger.info(f"Successfully loaded resume text for ID: {resume_id}")
            return full_text
            
        except Exception as e:
            logger.error(f"Failed to load resume text for ID {resume_id}: {e}")
            return None
    
    def resume_exists(self, resume_id: str) -> bool:
        """
        Check if a resume exists by ID
        
        Args:
            resume_id: Unique identifier for the resume
            
        Returns:
            True if resume exists, False otherwise
        """
        try:
            self.storage.get_pdf_path(resume_id)
            return True
        except:
            return False
