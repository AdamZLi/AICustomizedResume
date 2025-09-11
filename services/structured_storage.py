"""
Storage service for structured resume data
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from models_structured import StructuredResume

logger = logging.getLogger(__name__)

class StructuredResumeStorage:
    """Storage service for structured resume data"""
    
    def __init__(self, storage_dir: str = "structured_resumes"):
        """
        Initialize structured resume storage
        
        Args:
            storage_dir: Directory to store structured resume data
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def save_resume(self, resume: StructuredResume) -> bool:
        """
        Save structured resume to storage
        
        Args:
            resume: StructuredResume object to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update timestamp
            resume.updated_at = datetime.now()
            
            # Convert to dict for JSON serialization
            resume_dict = resume.dict()
            
            # Save to file
            file_path = self.storage_dir / f"{resume.id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(resume_dict, f, indent=2, default=str)
            
            logger.info(f"Saved structured resume {resume.id} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save structured resume {resume.id}: {e}")
            return False
    
    def load_resume(self, resume_id: str) -> Optional[StructuredResume]:
        """
        Load structured resume from storage
        
        Args:
            resume_id: Resume identifier
            
        Returns:
            StructuredResume object or None if not found
        """
        try:
            file_path = self.storage_dir / f"{resume_id}.json"
            
            if not file_path.exists():
                logger.warning(f"Structured resume {resume_id} not found")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                resume_dict = json.load(f)
            
            # Convert back to StructuredResume object
            resume = StructuredResume(**resume_dict)
            
            logger.info(f"Loaded structured resume {resume_id}")
            return resume
            
        except Exception as e:
            logger.error(f"Failed to load structured resume {resume_id}: {e}")
            return None
    
    def delete_resume(self, resume_id: str) -> bool:
        """
        Delete structured resume from storage
        
        Args:
            resume_id: Resume identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self.storage_dir / f"{resume_id}.json"
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted structured resume {resume_id}")
                return True
            else:
                logger.warning(f"Structured resume {resume_id} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete structured resume {resume_id}: {e}")
            return False
    
    def list_resumes(self) -> list[Dict[str, Any]]:
        """
        List all stored resumes with metadata
        
        Returns:
            List of resume metadata dictionaries
        """
        resumes = []
        
        try:
            for file_path in self.storage_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        resume_dict = json.load(f)
                    
                    # Extract metadata
                    metadata = {
                        'id': resume_dict.get('id'),
                        'original_filename': resume_dict.get('original_filename'),
                        'created_at': resume_dict.get('created_at'),
                        'updated_at': resume_dict.get('updated_at'),
                        'file_path': str(file_path)
                    }
                    resumes.append(metadata)
                    
                except Exception as e:
                    logger.warning(f"Failed to read resume metadata from {file_path}: {e}")
                    continue
            
            # Sort by updated_at descending
            resumes.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list resumes: {e}")
        
        return resumes
    
    def resume_exists(self, resume_id: str) -> bool:
        """
        Check if a structured resume exists
        
        Args:
            resume_id: Resume identifier
            
        Returns:
            True if exists, False otherwise
        """
        file_path = self.storage_dir / f"{resume_id}.json"
        return file_path.exists()
    
    def get_resume_metadata(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """
        Get resume metadata without loading full data
        
        Args:
            resume_id: Resume identifier
            
        Returns:
            Metadata dictionary or None if not found
        """
        try:
            file_path = self.storage_dir / f"{resume_id}.json"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                resume_dict = json.load(f)
            
            # Return only metadata fields
            metadata = {
                'id': resume_dict.get('id'),
                'original_filename': resume_dict.get('original_filename'),
                'created_at': resume_dict.get('created_at'),
                'updated_at': resume_dict.get('updated_at'),
                'work_experience_count': len(resume_dict.get('work_experience', [])),
                'education_count': len(resume_dict.get('education', [])),
                'entrepreneurship_count': len(resume_dict.get('entrepreneurship', [])),
                'additional_info_count': len(resume_dict.get('additional_info', []))
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get resume metadata {resume_id}: {e}")
            return None
