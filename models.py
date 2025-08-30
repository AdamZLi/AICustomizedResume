"""
Data models and schemas for the Resume Tailoring API
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List

class JobTextRequest(BaseModel):
    """Request model for text-based keyword extraction"""
    job_text: str = Field(..., description="Job description text to analyze")
    max_terms: int = Field(default=30, ge=1, le=100, description="Maximum number of terms to extract")

class JobURLRequest(BaseModel):
    """Request model for URL-based keyword extraction"""
    job_title: str = Field(..., description="Job title for context")
    job_url: HttpUrl = Field(..., description="URL of the job posting to scrape")
    max_terms: int = Field(default=30, ge=1, le=100, description="Maximum number of terms to extract")

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

class KeywordsResponse(BaseModel):
    """Response model containing organized keywords"""
    recruiter_buckets: RecruiterBuckets = Field(..., description="Keywords organized by recruiter search buckets")
