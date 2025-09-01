"""
Data models and schemas for the Resume Tailoring API
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional

class JobTextRequest(BaseModel):
    """Request model for text-based keyword extraction"""
    job_text: str = Field(..., description="Job description text to analyze")
    max_terms: int = Field(default=30, ge=1, le=100, description="Maximum number of terms to extract")
    resume_id: Optional[str] = Field(None, description="Optional resume ID to compare keywords against")

class JobURLRequest(BaseModel):
    """Request model for URL-based keyword extraction"""
    job_title: str = Field(..., description="Job title for context")
    job_url: HttpUrl = Field(..., description="URL of the job posting to scrape")
    max_terms: int = Field(default=30, ge=1, le=100, description="Maximum number of terms to extract")
    resume_id: Optional[str] = Field(None, description="Optional resume ID to compare keywords against")

class KeywordItem(BaseModel):
    """Individual keyword with priority"""
    text: str = Field(..., description="The keyword text")
    priority: str = Field(..., description="Priority: must_have, nice_to_have")

class RecruiterBuckets(BaseModel):
    """Organized keywords by recruiter search categories"""
    summary_headline_signals: List[KeywordItem] = Field(..., description="What recruiters search to find profiles fast")
    core_requirements: List[KeywordItem] = Field(..., description="Role-defining skills from Requirements/Qualifications")
    methods_frameworks: List[KeywordItem] = Field(..., description="Named ways of working that are searchable")
    tools_tech_stack: List[KeywordItem] = Field(..., description="Systems and tools recruiters filter on in ATS")
    domain_platform_keywords: List[KeywordItem] = Field(..., description="Industry or problem space terms")
    kpis_outcomes_metrics: List[KeywordItem] = Field(..., description="Quantifiable results recruiters scan for")
    leadership_scope_signals: List[KeywordItem] = Field(..., description="Level indicators recruiters query for when filtering seniors")

class IncludedKeyword(BaseModel):
    """Keyword found in resume with position information"""
    text: str = Field(..., description="The keyword text")
    positions: List[List[int]] = Field(..., description="List of [start, end] position pairs for highlighting")
    match_type: str = Field(..., description="Type of match: exact or fuzzy")

class MissingKeyword(BaseModel):
    """Keyword not found in resume"""
    text: str = Field(..., description="The keyword text")

class CoverageStats(BaseModel):
    """Coverage statistics for keyword comparison"""
    included: int = Field(..., description="Number of keywords found in resume")
    missing: int = Field(..., description="Number of keywords not found in resume")
    percent: float = Field(..., description="Percentage of keywords found")

class KeywordComparison(BaseModel):
    """Results of comparing keywords to resume text"""
    included: List[IncludedKeyword] = Field(..., description="Keywords found in resume")
    missing: List[MissingKeyword] = Field(..., description="Keywords not found in resume")
    coverage: CoverageStats = Field(..., description="Coverage statistics")

class KeywordsResponse(BaseModel):
    """Response model containing organized keywords"""
    recruiter_buckets: RecruiterBuckets = Field(..., description="Keywords organized by recruiter search buckets")
    comparison: Optional[KeywordComparison] = Field(None, description="Keyword comparison results if resume_id provided")

class ResumeUploadResponse(BaseModel):
    """Response model for resume upload"""
    resume_id: str = Field(..., description="Unique identifier for the uploaded resume")
    filename: str = Field(..., description="Original filename of the uploaded PDF")
    size: int = Field(..., description="File size in bytes")
    preview_chars: int = Field(..., description="Number of characters in the preview")
    text_excerpt: str = Field(..., description="First 800 characters of extracted text")
    pdf_url: str = Field(..., description="URL to view the PDF")
    text_url: str = Field(..., description="URL to get the full text")

class ResumeTextResponse(BaseModel):
    """Response model for resume text extraction"""
    resume_id: str = Field(..., description="Unique identifier for the resume")
    text: str = Field(..., description="Full extracted text from the PDF")

class ResumeRewriteRequest(BaseModel):
    """Request model for resume rewrite"""
    resume_id: str = Field(..., description="Unique identifier for the resume to rewrite")
    selected_keywords: List[str] = Field(..., description="List of keywords to incorporate")
    job_title: Optional[str] = Field(None, description="Target job title for context")
    tone: Optional[str] = Field(None, description="Desired tone for the rewrite")

class ChangeLogItem(BaseModel):
    """Individual change log entry"""
    section: str = Field(..., description="Section of the resume that was changed")
    before: str = Field(..., description="Original text before changes")
    after: str = Field(..., description="Updated text after changes")
    keywords_used: List[str] = Field(..., description="Keywords that were incorporated in this change")

class ResumeRewriteResponse(BaseModel):
    """Response model for resume rewrite"""
    resume_id: str = Field(..., description="Unique identifier for the resume")
    pdf_url: str = Field(..., description="URL to download the updated PDF")
    updated_text: str = Field(..., description="Full updated resume text")
    change_log: List[ChangeLogItem] = Field(..., description="Detailed log of all changes made")
    included_keywords: List[str] = Field(..., description="Keywords that were successfully incorporated")
