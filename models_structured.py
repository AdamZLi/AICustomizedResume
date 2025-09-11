"""
Enhanced data models for structured resume editing
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class SectionType(str, Enum):
    """Types of resume sections"""
    HEADLINE = "headline"
    WORK_EXPERIENCE = "work_experience"
    ENTREPRENEURSHIP = "entrepreneurship"
    EDUCATION = "education"
    ADDITIONAL_INFO = "additional_info"
    SKILLS = "skills"

class BulletPoint(BaseModel):
    """Individual bullet point in a resume section"""
    id: str = Field(..., description="Unique identifier for the bullet point")
    text: str = Field(..., description="The bullet point text content")
    is_active: bool = Field(default=True, description="Whether this bullet point is included in the resume")
    order: int = Field(..., description="Display order within the section")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('text')
    def validate_text_length(cls, v):
        if len(v) < 10:
            raise ValueError('Bullet point must be at least 10 characters')
        if len(v) > 500:
            raise ValueError('Bullet point must be less than 500 characters')
        return v.strip()

class WorkExperience(BaseModel):
    """Work experience entry"""
    id: str = Field(..., description="Unique identifier for the work experience")
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    location: Optional[str] = Field(None, description="Work location")
    start_date: Optional[str] = Field(None, description="Start date (e.g., 'Jan 2020')")
    end_date: Optional[str] = Field(None, description="End date (e.g., 'Present', 'Dec 2022')")
    is_current: bool = Field(default=False, description="Whether this is the current position")
    bullets: List[BulletPoint] = Field(default_factory=list, description="List of achievement bullet points")
    order: int = Field(..., description="Display order")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Entrepreneurship(BaseModel):
    """Entrepreneurship/startup experience entry"""
    id: str = Field(..., description="Unique identifier for the entrepreneurship entry")
    company: str = Field(..., description="Company/project name")
    title: str = Field(..., description="Role/title")
    location: Optional[str] = Field(None, description="Location")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date")
    is_current: bool = Field(default=False, description="Whether this is ongoing")
    bullets: List[BulletPoint] = Field(default_factory=list, description="List of achievement bullet points")
    order: int = Field(..., description="Display order")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Education(BaseModel):
    """Education entry"""
    id: str = Field(..., description="Unique identifier for the education entry")
    institution: str = Field(..., description="School/university name")
    degree: str = Field(..., description="Degree type and field")
    location: Optional[str] = Field(None, description="Institution location")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date")
    gpa: Optional[str] = Field(None, description="GPA if relevant")
    extras: List[str] = Field(default_factory=list, description="Additional details (honors, activities, etc.)")
    order: int = Field(..., description="Display order")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Headline(BaseModel):
    """Resume headline section"""
    name: str = Field(..., description="Full name")
    title: str = Field(..., description="Professional title/tagline")
    summary: Optional[str] = Field(None, description="Brief professional summary")
    contact: Dict[str, str] = Field(default_factory=dict, description="Contact information (email, phone, location, linkedin)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class AdditionalInfo(BaseModel):
    """Additional information section"""
    id: str = Field(..., description="Unique identifier")
    category: str = Field(..., description="Category name (e.g., 'Skills', 'Certifications', 'Languages')")
    items: List[str] = Field(default_factory=list, description="List of items in this category")
    order: int = Field(..., description="Display order")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class StructuredResume(BaseModel):
    """Complete structured resume data"""
    id: str = Field(..., description="Unique identifier for the resume")
    original_filename: str = Field(..., description="Original uploaded filename")
    headline: Headline = Field(..., description="Resume headline section")
    work_experience: List[WorkExperience] = Field(default_factory=list, description="Work experience entries")
    entrepreneurship: List[Entrepreneurship] = Field(default_factory=list, description="Entrepreneurship entries")
    education: List[Education] = Field(default_factory=list, description="Education entries")
    additional_info: List[AdditionalInfo] = Field(default_factory=list, description="Additional information sections")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def get_all_bullets(self) -> List[BulletPoint]:
        """Get all bullet points from all sections"""
        bullets = []
        for exp in self.work_experience:
            bullets.extend(exp.bullets)
        for ent in self.entrepreneurship:
            bullets.extend(ent.bullets)
        return bullets
    
    def get_section_by_type(self, section_type: SectionType) -> List[Union[WorkExperience, Entrepreneurship, Education, AdditionalInfo]]:
        """Get sections by type"""
        if section_type == SectionType.WORK_EXPERIENCE:
            return self.work_experience
        elif section_type == SectionType.ENTREPRENEURSHIP:
            return self.entrepreneurship
        elif section_type == SectionType.EDUCATION:
            return self.education
        elif section_type == SectionType.ADDITIONAL_INFO:
            return self.additional_info
        return []

# API Request/Response Models

class StructuredResumeResponse(BaseModel):
    """Response model for structured resume data"""
    resume: StructuredResume = Field(..., description="Complete structured resume data")

class SectionUpdateRequest(BaseModel):
    """Request model for updating a resume section"""
    resume_id: str = Field(..., description="Resume identifier")
    section_type: SectionType = Field(..., description="Type of section to update")
    section_data: Union[WorkExperience, Entrepreneurship, Education, AdditionalInfo, Headline] = Field(..., description="Section data")

class BulletPointUpdateRequest(BaseModel):
    """Request model for updating a bullet point"""
    resume_id: str = Field(..., description="Resume identifier")
    section_type: SectionType = Field(..., description="Type of section")
    section_id: str = Field(..., description="Section identifier")
    bullet: BulletPoint = Field(..., description="Updated bullet point data")

class ResumeExportRequest(BaseModel):
    """Request model for exporting resume"""
    resume_id: str = Field(..., description="Resume identifier")
    format: str = Field(default="pdf", description="Export format (pdf, html, docx)")
    include_annotations: bool = Field(default=False, description="Whether to include keyword annotations")

class KeywordInsertionRequest(BaseModel):
    """Request model for keyword insertion suggestions"""
    resume_id: str = Field(..., description="Resume identifier")
    keywords: List[str] = Field(..., description="Keywords to insert")
    max_insertions_per_bullet: int = Field(default=2, description="Maximum insertions per bullet point")
    max_chars_per_insertion: int = Field(default=25, description="Maximum characters per insertion")

class KeywordInsertionSuggestion(BaseModel):
    """Individual keyword insertion suggestion"""
    bullet_id: str = Field(..., description="Target bullet point ID")
    insertion_text: str = Field(..., description="Text to insert")
    insertion_type: str = Field(..., description="Type: modifier, parenthetical, or tail")
    keywords_used: List[str] = Field(..., description="Keywords incorporated in this insertion")
    confidence: float = Field(..., description="Confidence score (0-1)")

class KeywordInsertionResponse(BaseModel):
    """Response model for keyword insertion suggestions"""
    suggestions: List[KeywordInsertionSuggestion] = Field(..., description="List of insertion suggestions")
    skipped_keywords: List[str] = Field(..., description="Keywords that couldn't be inserted")

class ResumeParseRequest(BaseModel):
    """Request model for parsing uploaded resume"""
    resume_id: str = Field(..., description="Resume identifier")
    parse_options: Dict[str, Any] = Field(default_factory=dict, description="Parsing options")

class ResumeParseResponse(BaseModel):
    """Response model for resume parsing"""
    resume_id: str = Field(..., description="Resume identifier")
    structured_resume: StructuredResume = Field(..., description="Parsed structured resume data")
    parse_summary: Dict[str, Any] = Field(..., description="Summary of parsing results")
    warnings: List[str] = Field(default_factory=list, description="Parsing warnings")
