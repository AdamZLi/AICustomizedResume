"""
Web scraping functionality for job posting URLs
"""

import re
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
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    
    try:
        r = requests.get(job_url, timeout=(15, 30), headers=headers)
        r.raise_for_status()
        
        # Try Readability first
        try:
            main_html = Readability(r.text).summary()
            text = BeautifulSoup(main_html, "html.parser").get_text(separator="\n", strip=True)
        except Exception:
            # Fallback: try to extract text directly from the page
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Smart content detection for job sites
            content_selectors = [
                # Job-specific selectors
                "[class*='job']", "[class*='description']", "[class*='content']",
                "[id*='job']", "[id*='description']", "[id*='content']",
                ".job-description", ".job-content", ".description-content",
                ".posting-content", ".role-description", ".position-description",
                # Generic content selectors
                "main", "article", ".content", "#content", ".main-content",
                # Ashby-specific (if they exist)
                "[data-testid*='job']", "[data-testid*='description']",
                ".ashby-job-description", ".ashby-content"
            ]
            
            content_element = None
            for selector in content_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        if element and len(element.get_text(strip=True)) > 100:
                            content_element = element
                            break
                    if content_element:
                        break
                except:
                    continue
            
            # If no specific content area found, try to find the largest text block
            if not content_element:
                text_blocks = soup.find_all(["div", "section", "p"])
                largest_block = None
                max_length = 0
                
                for block in text_blocks:
                    text_length = len(block.get_text(strip=True))
                    if text_length > max_length and text_length > 50:
                        max_length = text_length
                        largest_block = block
                
                if largest_block:
                    content_element = largest_block
                else:
                    # Last resort: get all text
                    content_element = soup
            
            text = content_element.get_text(separator="\n", strip=True)
        
        # Clean up the text
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        text = re.sub(r"\s+", " ", text)  # Normalize whitespace
        
        return text
        
    except Exception as e:
        print(f"Enhanced requests method failed: {e}")
        return ""

def try_alternative_user_agents(job_url: str) -> str:
    """Try with different user agents to bypass some bot detection"""
    alternative_user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    for user_agent in alternative_user_agents:
        try:
            headers = {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            
            r = requests.get(job_url, timeout=(10, 20), headers=headers)
            r.raise_for_status()
            
            # Simple text extraction
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
                element.decompose()
            
            text = soup.get_text(separator="\n", strip=True)
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
            text = re.sub(r"\s+", " ", text)
            
            if len(text) > 200:
                print(f"Alternative user agent worked: {user_agent[:50]}...")
                return text
                
        except Exception as e:
            print(f"Alternative user agent failed: {e}")
            continue
    
    return ""
