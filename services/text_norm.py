"""
Text normalization service for keyword matching
"""
import re
import unicodedata
from typing import List, Set

def normalize_nfkc_lower(text: str) -> str:
    """
    Normalize text using NFKC and convert to lowercase
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text string
    """
    if not text:
        return ""
    
    # Unicode NFKC normalization (combines characters and compatibility)
    normalized = unicodedata.normalize('NFKC', text)
    
    # Convert to lowercase
    normalized = normalized.lower()
    
    # Strip extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized

def expand_keyword_variants(keyword: str) -> List[str]:
    """
    Generate regex patterns for keyword variants with punctuation
    
    Args:
        keyword: Original keyword text
        
    Returns:
        List of regex patterns for matching variants
    """
    if not keyword:
        return []
    
    # Normalize the keyword first
    normalized = normalize_nfkc_lower(keyword)
    
    variants = [normalized]
    
    # Handle slash variants (a/b testing -> a b testing, a/b testing, a and b testing)
    if '/' in normalized:
        # Replace / with space
        space_variant = normalized.replace('/', ' ')
        variants.append(space_variant)
        
        # Replace / with " and "
        and_variant = normalized.replace('/', ' and ')
        variants.append(and_variant)
        
        # Keep original with /
        variants.append(normalized)
    
    # Handle hyphen variants (a-b testing -> a b testing, a-b testing)
    if '-' in normalized:
        # Replace - with space
        space_variant = normalized.replace('-', ' ')
        variants.append(space_variant)
        
        # Keep original with -
        variants.append(normalized)
    
    # Handle parentheses variants (a(b) testing -> a b testing, a(b) testing)
    if '(' in normalized or ')' in normalized:
        # Remove parentheses
        no_parens = re.sub(r'[()]', ' ', normalized)
        no_parens = re.sub(r'\s+', ' ', no_parens).strip()
        variants.append(no_parens)
        
        # Keep original with parentheses
        variants.append(normalized)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_variants = []
    for variant in variants:
        if variant not in seen:
            seen.add(variant)
            unique_variants.append(variant)
    
    return unique_variants

def build_regex_pattern(keyword: str) -> str:
    """
    Build a regex pattern for exact keyword matching with word boundaries
    
    Args:
        keyword: Keyword to build pattern for
        
    Returns:
        Compiled regex pattern string
    """
    if not keyword:
        return ""
    
    # Normalize the keyword first
    normalized = normalize_nfkc_lower(keyword)
    
    # Escape special regex characters
    escaped = re.escape(normalized)
    
    # Handle hyphen variants - replace escaped hyphens with pattern that matches hyphen or space
    escaped = re.sub(r'\\-', r'(?:-|\\s+)', escaped)
    
    # Handle slash variants - replace escaped slashes with pattern that matches slash, space, or "and"
    escaped = re.sub(r'\\/', r'(?:/|\\s+|\\s+and\\s+)', escaped)
    
    # Add word boundaries where safe (not at punctuation)
    if re.match(r'^[a-zA-Z]', keyword):
        escaped = r'\b' + escaped
    if re.match(r'[a-zA-Z]$', keyword):
        escaped = escaped + r'\b'
    
    return escaped

def clean_text_for_matching(text: str) -> str:
    """
    Clean text for keyword matching by removing excessive whitespace
    and normalizing line breaks
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    
    # Normalize line breaks
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Replace multiple newlines with single space
    text = re.sub(r'\n+', ' ', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text
