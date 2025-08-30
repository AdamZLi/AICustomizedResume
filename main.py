from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any
import openai
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from readability import Document as Readability
import re

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

# User agent for web scraping
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

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

class JobTextRequest(BaseModel):
    job_text: str = Field(..., description="Job description text to analyze")
    max_terms: int = Field(default=30, ge=1, le=100, description="Maximum number of terms to extract")

class JobURLRequest(BaseModel):
    job_title: str = Field(..., description="Job title for context")
    job_url: HttpUrl = Field(..., description="URL of the job posting to scrape")
    max_terms: int = Field(default=30, ge=1, le=100, description="Maximum number of terms to extract")

def fetch_and_clean(job_url: str) -> str:
    """Fetch job posting URL and extract clean text content"""
    r = requests.get(job_url, timeout=(10, 20), headers={"User-Agent": UA})
    r.raise_for_status()
    main_html = Readability(r.text).summary()   # pull main article content
    text = BeautifulSoup(main_html, "html.parser").get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

class KeywordItem(BaseModel):
    text: str = Field(..., description="The keyword text")
    priority: str = Field(..., description="Priority: must_have, nice_to_have")

class RecruiterBuckets(BaseModel):
    summary_headline_signals: List[KeywordItem] = Field(..., description="What recruiters search to find profiles fast")
    core_requirements: List[KeywordItem] = Field(..., description="Role-defining skills from Requirements/Qualifications")
    methods_frameworks: List[KeywordItem] = Field(..., description="Named ways of working that are searchable")
    tools_tech_stack: List[KeywordItem] = Field(..., description="Systems and tools recruiters filter on in ATS")
    domain_platform_keywords: List[KeywordItem] = Field(..., description="Industry or problem space terms")
    kpis_outcomes_metrics: List[KeywordItem] = Field(..., description="Quantifiable results recruiters scan for")
    leadership_scope_signals: List[KeywordItem] = Field(..., description="Level indicators recruiters query for when filtering seniors")

class KeywordsResponse(BaseModel):
    recruiter_buckets: RecruiterBuckets = Field(..., description="Keywords organized by recruiter search buckets")

@app.get("/")
async def root():
    return {"message": "Resume Tailoring API - Use POST /keywords_text to extract keywords from job descriptions"}

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
        
        # Prepare the improved prompt for OpenAI
        prompt = f"""You are a top-tier tech recruiter screening Senior Product Manager / Senior Project Manager candidates for big tech and VC-backed startups.

TASK
From the job description, extract ONLY recruiter/ATS-scannable keywords a strong resume should reflect. Organize them into the seven buckets below.

STRICT EXCLUSIONS
- Ignore benefits/perks/compensation/location/EEO or company boilerplate (e.g., pto, 401k, equity/rsu, hybrid/remote, wellness, commuter, salary, offices, visa/sponsorship, diversity statements).
- Exclude company names and generic fluff (e.g., team player, great culture). No dates or salary figures.

WHAT TO EXTRACT (JD-faithful, ATS-friendly)
- Short, concrete phrases (1–3 words): hard skills, tools/tech, methods/frameworks, domain/platform terms, KPIs/metrics, leadership/scope signals.
- Prefer items explicitly present in the JD's "Requirements", "Qualifications", and "Responsibilities" sections.
- Lowercase; deduplicate; total ≤ {request.max_terms} items across all buckets.
- PRIORITY: label each item as "must_have" (role-defining for THIS JD) or "nice_to_have".

TITLE AWARENESS
- If product manager ⇒ emphasize product strategy/roadmap, discovery/experimentation (e.g., a/b testing), analytics/metrics (arr, mrr, dau/mau, conversion), platform/apis, growth/monetization, cross-functional leadership.
- If project manager ⇒ emphasize delivery planning, risk/issue management, scope/schedule/cost, dependencies/critical path, stakeholder management, agile/scrum, pmbok/pmp.
- Stay strictly faithful to the JD wording.

OUTPUT
Return ONLY JSON that matches the provided JSON Schema (no prose).

CONTEXT
job_title: {job_title}

job_description:
\"\"\"
{request.job_text}
\"\"\"

Return the response in this exact JSON format:
{{
    "recruiter_buckets": {{
        "summary_headline_signals": [
            {{"text": "keyword1", "priority": "must_have"}},
            {{"text": "keyword2", "priority": "nice_to_have"}}
        ],
        "core_requirements": [
            {{"text": "keyword3", "priority": "must_have"}}
        ],
        "methods_frameworks": [
            {{"text": "keyword4", "priority": "must_have"}}
        ],
        "tools_tech_stack": [
            {{"text": "keyword5", "priority": "must_have"}}
        ],
        "domain_platform_keywords": [
            {{"text": "keyword6", "priority": "must_have"}}
        ],
        "kpis_outcomes_metrics": [
            {{"text": "keyword7", "priority": "must_have"}}
        ],
        "leadership_scope_signals": [
            {{"text": "keyword8", "priority": "must_have"}}
        ]
    }}
}}"""
        
        # Call OpenAI API using modern format
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional tech recruiter specializing in Product and Project Management roles. Extract relevant keywords that recruiters would screen for in resumes, organized by recruiter search buckets."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        # Parse OpenAI response
        content = response.choices[0].message.content
        
        # Extract JSON from response (handle potential markdown formatting)
        import json
        import re
        
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
            except json.JSONDecodeError:
                # Fallback: try to parse the entire response
                parsed = json.loads(content)
        else:
            # Fallback: try to parse the entire response
            parsed = json.loads(content)
        
        # Extract recruiter buckets
        recruiter_buckets = parsed.get("recruiter_buckets", {})
        
        # Process and clean the extracted terms for each bucket
        def clean_keywords(keywords):
            if not isinstance(keywords, list):
                return []
            
            cleaned = []
            for item in keywords:
                if isinstance(item, dict) and "text" in item and "priority" in item:
                    text = item.get("text", "").strip().lower()
                    priority = item.get("priority", "").strip().lower()
                    
                    if text and len(text) > 1:
                        # Validate priority
                        valid_priorities = ["must_have", "nice_to_have"]
                        
                        if priority in valid_priorities:
                            cleaned.append(KeywordItem(
                                text=text,
                                priority=priority
                            ))
            
            # Remove duplicates based on text
            seen = set()
            unique_keywords = []
            for item in cleaned:
                if item.text not in seen:
                    seen.add(item.text)
                    unique_keywords.append(item)
            
            return unique_keywords
        
        # Process each bucket
        summary_headline_signals = clean_keywords(recruiter_buckets.get("summary_headline_signals", []))
        core_requirements = clean_keywords(recruiter_buckets.get("core_requirements", []))
        methods_frameworks = clean_keywords(recruiter_buckets.get("methods_frameworks", []))
        tools_tech_stack = clean_keywords(recruiter_buckets.get("tools_tech_stack", []))
        domain_platform_keywords = clean_keywords(recruiter_buckets.get("domain_platform_keywords", []))
        kpis_outcomes_metrics = clean_keywords(recruiter_buckets.get("kpis_outcomes_metrics", []))
        leadership_scope_signals = clean_keywords(recruiter_buckets.get("leadership_scope_signals", []))
        
        # Create the response
        return KeywordsResponse(
            recruiter_buckets=RecruiterBuckets(
                summary_headline_signals=summary_headline_signals,
                core_requirements=core_requirements,
                methods_frameworks=methods_frameworks,
                tools_tech_stack=tools_tech_stack,
                domain_platform_keywords=domain_platform_keywords,
                kpis_outcomes_metrics=kpis_outcomes_metrics,
                leadership_scope_signals=leadership_scope_signals
            )
        )
        
    except openai.APIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except openai.AuthenticationError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI authentication error: {str(e)}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse OpenAI response: {str(e)}")
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
    except requests.RequestException as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Could not fetch page: {str(e)}"
        )

    if len(jd_text) < 500:
        raise HTTPException(
            status_code=400,
            detail="Could not extract enough job text (site may require login or block bots). Please paste the JD text instead."
        )

    # Reuse the existing keyword extraction logic
    try:
        # Prepare the improved prompt for OpenAI
        prompt = f"""You are a top-tier tech recruiter screening Senior Product Manager / Senior Project Manager candidates for big tech and VC-backed startups.

TASK
From the job description, extract ONLY recruiter/ATS-scannable keywords a strong resume should reflect. Organize them into the seven buckets below.

STRICT EXCLUSIONS
- Ignore benefits/perks/compensation/location/EEO or company boilerplate (e.g., pto, 401k, equity/rsu, hybrid/remote, wellness, commuter, salary, offices, visa/sponsorship, diversity statements).
- Exclude company names and generic fluff (e.g., team player, great culture). No dates or salary figures.

WHAT TO EXTRACT (JD-faithful, ATS-friendly)
- Short, concrete phrases (1–3 words): hard skills, tools/tech, methods/frameworks, domain/platform terms, KPIs/metrics, leadership/scope signals.
- Prefer items explicitly present in the JD's "Requirements", "Qualifications", and "Responsibilities" sections.
- Lowercase; deduplicate; total ≤ {request.max_terms} items across all buckets.
- PRIORITY: label each item as "must_have" (role-defining for THIS JD) or "nice_to_have".

TITLE AWARENESS
- If product manager ⇒ emphasize product strategy/roadmap, discovery/experimentation (e.g., a/b testing), analytics/metrics (arr, mrr, dau/mau, conversion), platform/apis, growth/monetization, cross-functional leadership.
- If project manager ⇒ emphasize delivery planning, risk/issue management, scope/schedule/cost, dependencies/critical path, stakeholder management, agile/scrum, pmbok/pmp.
- Stay strictly faithful to the JD wording.

OUTPUT
Return ONLY JSON that matches the provided JSON Schema (no prose).

CONTEXT
job_title: {request.job_title}

job_description:
\"\"\"
{jd_text}
\"\"\"

Return the response in this exact JSON format:
{{
    "recruiter_buckets": {{
        "summary_headline_signals": [
            {{"text": "keyword1", "priority": "must_have"}},
            {{"text": "keyword2", "priority": "nice_to_have"}}
        ],
        "core_requirements": [
            {{"text": "keyword3", "priority": "must_have"}}
        ],
        "methods_frameworks": [
            {{"text": "keyword4", "priority": "must_have"}}
        ],
        "tools_tech_stack": [
            {{"text": "keyword5", "priority": "must_have"}}
        ],
        "domain_platform_keywords": [
            {{"text": "keyword6", "priority": "must_have"}}
        ],
        "kpis_outcomes_metrics": [
            {{"text": "keyword7", "priority": "must_have"}}
        ],
        "leadership_scope_signals": [
            {{"text": "keyword8", "priority": "must_have"}}
        ]
    }}
}}"""
        
        # Call OpenAI API using modern format
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional tech recruiter specializing in Product and Project Management roles. Extract relevant keywords that recruiters would screen for in resumes, organized by recruiter search buckets."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        # Parse OpenAI response
        content = response.choices[0].message.content
        
        # Extract JSON from response (handle potential markdown formatting)
        import json
        import re
        
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
            except json.JSONDecodeError:
                # Fallback: try to parse the entire response
                parsed = json.loads(content)
        else:
            # Fallback: try to parse the entire response
            parsed = json.loads(content)
        
        # Extract recruiter buckets
        recruiter_buckets = parsed.get("recruiter_buckets", {})
        
        # Process and clean the extracted terms for each bucket
        def clean_keywords(keywords):
            if not isinstance(keywords, list):
                return []
            
            cleaned = []
            for item in keywords:
                if isinstance(item, dict) and "text" in item and "priority" in item:
                    text = item.get("text", "").strip().lower()
                    priority = item.get("priority", "").strip().lower()
                    
                    if text and len(text) > 1:
                        # Validate priority
                        valid_priorities = ["must_have", "nice_to_have"]
                        
                        if priority in valid_priorities:
                            cleaned.append(KeywordItem(
                                text=text,
                                priority=priority
                            ))
            
            # Remove duplicates based on text
            seen = set()
            unique_keywords = []
            for item in cleaned:
                if item.text not in seen:
                    seen.add(item.text)
                    unique_keywords.append(item)
            
            return unique_keywords
        
        # Process each bucket
        summary_headline_signals = clean_keywords(recruiter_buckets.get("summary_headline_signals", []))
        core_requirements = clean_keywords(recruiter_buckets.get("core_requirements", []))
        methods_frameworks = clean_keywords(recruiter_buckets.get("methods_frameworks", []))
        tools_tech_stack = clean_keywords(recruiter_buckets.get("tools_tech_stack", []))
        domain_platform_keywords = clean_keywords(recruiter_buckets.get("domain_platform_keywords", []))
        kpis_outcomes_metrics = clean_keywords(recruiter_buckets.get("kpis_outcomes_metrics", []))
        leadership_scope_signals = clean_keywords(recruiter_buckets.get("leadership_scope_signals", []))
        
        # Create the response
        return KeywordsResponse(
            recruiter_buckets=RecruiterBuckets(
                summary_headline_signals=summary_headline_signals,
                core_requirements=core_requirements,
                methods_frameworks=methods_frameworks,
                tools_tech_stack=tools_tech_stack,
                domain_platform_keywords=domain_platform_keywords,
                kpis_outcomes_metrics=kpis_outcomes_metrics,
                leadership_scope_signals=leadership_scope_signals
            )
        )
        
    except openai.APIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except openai.AuthenticationError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI authentication error: {str(e)}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse OpenAI response: {str(e)}")
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

