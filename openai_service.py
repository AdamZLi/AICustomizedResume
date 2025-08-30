"""
OpenAI service for keyword extraction and processing
"""

import json
import re
import openai
from models import KeywordItem, RecruiterBuckets, KeywordsResponse

def extract_keywords_with_openai(job_title: str, job_text: str, max_terms: int) -> KeywordsResponse:
    """
    Extract recruiter/ATS-scannable keywords from job description using OpenAI.
    
    Args:
        job_title: Job title for context
        job_text: Job description text to analyze
        max_terms: Maximum number of terms to extract
        
    Returns:
        KeywordsResponse with keywords organized by recruiter search buckets
        
    Raises:
        Exception: If OpenAI API call fails or response parsing fails
    """
    
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
- Lowercase; deduplicate; total ≤ {max_terms} items across all buckets.
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
{job_text}
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
    response = openai.chat.completions.create(
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
