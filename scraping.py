"""
Web scraping functionality for job posting URLs
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from readability import Document as Readability

# User agent for web scraping
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_and_clean(job_url: str) -> str:
    """Fetch job posting URL and extract clean text content using enhanced methods"""
    
    # Method 1: Try requests with enhanced headers and smart content detection
    text = try_enhanced_requests_method(job_url)
    if text and len(text) > 200:
        return text
    
    # Method 2: Try with different user agents
    text = try_alternative_user_agents(job_url)
    if text and len(text) > 200:
        return text
    
    # If both methods fail, return what we have
    return text or ""

def try_enhanced_requests_method(job_url: str) -> str:
    """Try to fetch content using requests with enhanced headers and smart content detection"""
    
    # Multiple header strategies to try
    header_strategies = [
        # Strategy 1: Modern browser headers
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        # Strategy 2: Mobile browser headers
        {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        },
        # Strategy 3: Desktop Safari headers
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    ]
    
    for i, headers in enumerate(header_strategies):
        try:
            print(f"Trying header strategy {i+1}...")
            
            # Add session cookies and referer for more authenticity
            session = requests.Session()
            
            # First, try to get the main page
            r = session.get(job_url, timeout=(20, 40), headers=headers, allow_redirects=True)
            r.raise_for_status()
            
            # Try to extract text with multiple methods
            text = extract_text_from_html(r.text, job_url)
            
            if text and len(text) > 200:
                print(f"Strategy {i+1} succeeded with {len(text)} characters")
                return text
                
        except Exception as e:
            print(f"Strategy {i+1} failed: {e}")
            continue
    
    return ""

def extract_text_from_html(html_content: str, url: str) -> str:
    """Extract text from HTML using multiple strategies"""
    
    # Strategy 1: Try Readability
    try:
        main_html = Readability(html_content).summary()
        text = BeautifulSoup(main_html, "html.parser").get_text(separator="\n", strip=True)
        if len(text) > 200:
            return text
    except Exception as e:
        print(f"Readability failed: {e}")
    
    # Strategy 2: Smart content detection
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Remove unwanted elements
    for element in soup(["script", "style", "nav", "header", "footer", "aside", "form", "button"]):
        element.decompose()
    
    # Ashby-specific selectors (based on their structure)
    ashby_selectors = [
        "[data-testid*='job']", "[data-testid*='description']", "[data-testid*='content']",
        "[class*='ashby']", "[class*='job']", "[class*='description']", "[class*='content']",
        "[id*='ashby']", "[id*='job']", "[id*='description']", "[id*='content']",
        ".ashby-job-description", ".ashby-content", ".job-description", ".job-content",
        ".posting-content", ".role-description", ".position-description",
        "[role='main']", "[role='article']", "main", "article"
    ]
    
    # Try Ashby-specific selectors first
    for selector in ashby_selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator="\n", strip=True)
                if len(text) > 200:
                    print(f"Found content with selector: {selector}")
                    return clean_text(text)
        except Exception:
            continue
    
    # Strategy 3: Find largest text blocks
    text_blocks = soup.find_all(["div", "section", "p", "span"])
    largest_blocks = []
    
    for block in text_blocks:
        text = block.get_text(strip=True)
        if len(text) > 100:  # Minimum meaningful content
            largest_blocks.append((len(text), text, block))
    
    # Sort by length and try the largest ones
    largest_blocks.sort(reverse=True)
    
    for length, text, block in largest_blocks[:5]:  # Try top 5
        # Check if this looks like job content
        if is_job_content(text):
            print(f"Found job content block with {length} characters")
            return clean_text(text)
    
    # Strategy 4: Extract all text and find job-related sections
    all_text = soup.get_text(separator="\n", strip=True)
    
    # Look for job-related keywords to identify relevant sections
    job_keywords = ["requirements", "qualifications", "responsibilities", "experience", "skills", "job", "position", "role"]
    
    lines = all_text.split('\n')
    relevant_lines = []
    
    for line in lines:
        line_lower = line.lower().strip()
        if any(keyword in line_lower for keyword in job_keywords) or len(line.strip()) > 50:
            relevant_lines.append(line)
    
    if relevant_lines:
        combined_text = '\n'.join(relevant_lines)
        if len(combined_text) > 200:
            return clean_text(combined_text)
    
    # Last resort: return all text
    return clean_text(all_text)

def is_job_content(text: str) -> bool:
    """Check if text looks like job description content"""
    text_lower = text.lower()
    
    # Job-related keywords that indicate this is job content
    job_indicators = [
        "requirements", "qualifications", "responsibilities", "experience", "skills",
        "job", "position", "role", "team", "collaborate", "develop", "manage",
        "years", "experience", "bachelor", "degree", "certification"
    ]
    
    # Check if text contains multiple job indicators
    indicator_count = sum(1 for indicator in job_indicators if indicator in text_lower)
    
    # Also check for reasonable length and structure
    has_structure = any(char in text for char in ['•', '-', '*', '1.', '2.', '3.'])
    
    return indicator_count >= 3 or (indicator_count >= 2 and has_structure)

def clean_text(text: str) -> str:
    """Clean and normalize extracted text"""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common web artifacts
    text = re.sub(r'Cookie Preferences|Privacy Policy|Terms of Service', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Skip to main content|Skip to navigation', '', text, flags=re.IGNORECASE)
    
    return text.strip()

def try_alternative_user_agents(job_url: str) -> str:
    """Try with different user agents and more aggressive strategies"""
    
    # More aggressive strategies
    strategies = [
        # Strategy 1: Try to get the raw HTML and look for hidden content
        try_extract_hidden_content,
        # Strategy 2: Try to follow redirects and get final page
        try_follow_redirects,
        # Strategy 3: Try to extract from meta tags and structured data
        try_extract_structured_data,
    ]
    
    for strategy in strategies:
        try:
            text = strategy(job_url)
            if text and len(text) > 200:
                return text
        except Exception as e:
            print(f"Strategy {strategy.__name__} failed: {e}")
            continue
    
    return ""

def try_extract_hidden_content(job_url: str) -> str:
    """Try to extract content that might be hidden or in comments"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        r = requests.get(job_url, timeout=(15, 30), headers=headers)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Look for content in comments
        comments = soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith('<!--'))
        for comment in comments:
            if len(comment.strip()) > 100:
                return clean_text(comment.strip())
        
        # Look for content in data attributes
        elements_with_data = soup.find_all(attrs={"data-content": True})
        for element in elements_with_data:
            content = element.get("data-content", "")
            if len(content) > 200:
                return clean_text(content)
        
        # Look for content in hidden elements
        hidden_elements = soup.find_all(attrs={"hidden": True}) + soup.find_all(attrs={"style": "display: none"})
        for element in hidden_elements:
            text = element.get_text(strip=True)
            if len(text) > 200:
                return clean_text(text)
        
        return ""
        
    except Exception as e:
        print(f"Hidden content extraction failed: {e}")
        return ""

def try_follow_redirects(job_url: str) -> str:
    """Try to follow redirects and get the final page content"""
    try:
        session = requests.Session()
        
        # Set up session with realistic browser behavior
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        
        # First request to get cookies and follow redirects
        r = session.get(job_url, timeout=(15, 30), allow_redirects=True)
        r.raise_for_status()
        
        # Try to extract text from the final page
        return extract_text_from_html(r.text, r.url)
        
    except Exception as e:
        print(f"Redirect following failed: {e}")
        return ""

def try_extract_structured_data(job_url: str) -> str:
    """Try to extract content from structured data (JSON-LD, microdata)"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        r = requests.get(job_url, timeout=(15, 30), headers=headers)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Look for JSON-LD structured data
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and "description" in data:
                    description = data["description"]
                    if len(description) > 200:
                        return clean_text(description)
            except:
                continue
        
        # Look for microdata
        microdata_elements = soup.find_all(attrs={"itemtype": True})
        for element in microdata_elements:
            description = element.find(attrs={"itemprop": "description"})
            if description:
                text = description.get_text(strip=True)
                if len(text) > 200:
                    return clean_text(text)
        
        return ""
        
    except Exception as e:
        print(f"Structured data extraction failed: {e}")
        return ""
