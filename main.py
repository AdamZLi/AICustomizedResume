"""
Main FastAPI application for the Resume Tailoring API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import openai

# Import our modules
from models import JobTextRequest, JobURLRequest, KeywordsResponse
from scraping import fetch_and_clean
from openai_service import extract_keywords_with_openai

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("WARNING: OPENAI_API_KEY not found in environment variables")
    print("Please set OPENAI_API_KEY in your .env file")
    client = None
else:
    client = openai.OpenAI(api_key=api_key)

app = FastAPI(
    title="Resume Tailoring API",
    description="API for extracting keywords from job descriptions and tailoring resumes",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Resume Tailoring API - Use POST /keywords_text or POST /keywords_url to extract keywords from job descriptions"}

@app.post("/keywords_text", response_model=KeywordsResponse)
async def extract_keywords(request: JobTextRequest):
    """
    Extract recruiter/ATS-scannable keywords from job description text using OpenAI.
    
    Args:
        request: JobTextRequest containing job_text and max_terms
        
    Returns:
        KeywordsResponse with keywords organized by recruiter search buckets
        
    Raises:
        HTTPException: If job_text is empty or OpenAI API call fails
    """
    # Validate input
    if not request.job_text.strip():
        raise HTTPException(status_code=400, detail="Job text cannot be empty")
    
    # Check if OpenAI client is available
    if not client:
        raise HTTPException(
            status_code=500, 
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY in your environment variables."
        )
    
    try:
        # Extract job title from the beginning of the job description
        job_title = "Product/Project Manager"  # Default fallback
        
        # Try to extract job title from the first few lines
        lines = request.job_text.strip().split('\n')
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip().lower()
            if any(keyword in line for keyword in ['product manager', 'project manager', 'senior', 'lead', 'director']):
                job_title = line.title()
                break
        
        # Use the OpenAI service to extract keywords
        return extract_keywords_with_openai(
            job_title=job_title,
            job_text=request.job_text,
            max_terms=request.max_terms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/keywords_url", response_model=KeywordsResponse)
async def keywords_url(request: JobURLRequest):
    """
    Extract recruiter/ATS-scannable keywords from a job posting URL using OpenAI.
    
    Args:
        request: JobURLRequest containing job_title, job_url, and max_terms
        
    Returns:
        KeywordsResponse with keywords organized by recruiter search buckets
        
    Raises:
        HTTPException: If URL cannot be fetched or insufficient text is extracted
    """
    # Check if OpenAI client is available
    if not client:
        raise HTTPException(
            status_code=500, 
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY in your environment variables."
        )
    
    try:
        # Fetch and clean the job description from the URL
        jd_text = fetch_and_clean(str(request.job_url))
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Could not fetch page: {str(e)}"
        )

    if len(jd_text) < 200:
        raise HTTPException(
            status_code=400,
            detail="Could not extract enough job text (site may require login or block bots). Please paste the JD text instead."
        )

    # Use the OpenAI service to extract keywords
    try:
        return extract_keywords_with_openai(
            job_title=request.job_title,
            job_text=jd_text,
            max_terms=request.max_terms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    openai_status = "configured" if client else "not configured"
    return {
        "status": "healthy", 
        "service": "Resume Tailoring API",
        "openai": openai_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


