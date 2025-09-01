"""
Storage service for handling PDF file operations
"""
import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)

class PDFStorageService:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    def save_pdf(self, file: UploadFile) -> tuple[str, Path]:
        """
        Save uploaded PDF file and return resume_id and file path
        
        Args:
            file: Uploaded file from FastAPI
            
        Returns:
            Tuple of (resume_id, file_path)
            
        Raises:
            HTTPException: If file is not a PDF or empty
        """
        # Validate file type
        if not file.content_type or file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400, 
                detail="Only PDF files are allowed"
            )
        
        # Validate file has content
        if not file.size or file.size == 0:
            raise HTTPException(
                status_code=400, 
                detail="File cannot be empty"
            )
        
        # Check file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400, 
                detail="File size must be less than 10MB"
            )
        
        # Generate unique resume ID
        resume_id = str(uuid.uuid4())
        file_path = self.upload_dir / f"{resume_id}.pdf"
        
        try:
            # Save file to disk
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
            
            logger.info(f"PDF saved successfully: resume_id={resume_id}, size={file.size}")
            return resume_id, file_path
            
        except Exception as e:
            logger.error(f"Failed to save PDF: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to save file"
            )
    
    def get_pdf_path(self, resume_id: str) -> Path:
        """
        Get the file path for a given resume_id
        
        Args:
            resume_id: Unique identifier for the resume
            
        Returns:
            Path to the PDF file
            
        Raises:
            HTTPException: If file doesn't exist
        """
        file_path = self.upload_dir / f"{resume_id}.pdf"
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404, 
                detail="Resume not found"
            )
        
        return file_path
    
    def delete_pdf(self, resume_id: str) -> bool:
        """
        Delete a PDF file by resume_id
        
        Args:
            resume_id: Unique identifier for the resume
            
        Returns:
            True if deleted, False if not found
        """
        file_path = self.upload_dir / f"{resume_id}.pdf"
        
        if file_path.exists():
            file_path.unlink()
            logger.info(f"PDF deleted: resume_id={resume_id}")
            return True
        
        return False
