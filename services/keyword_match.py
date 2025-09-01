"""
Keyword matching service for comparing keywords to resume text
"""
import re
import logging
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher
from .text_norm import normalize_nfkc_lower, build_regex_pattern, clean_text_for_matching

logger = logging.getLogger(__name__)

class KeywordMatcher:
    def __init__(self, fuzzy_threshold: float = 0.90):
        """
        Initialize keyword matcher
        
        Args:
            fuzzy_threshold: Minimum similarity score for fuzzy matching (0-1)
        """
        self.fuzzy_threshold = fuzzy_threshold
    
    def find_positions(self, text: str, pattern: str) -> List[List[int]]:
        """
        Find all positions of a regex pattern in text
        
        Args:
            text: Text to search in
            pattern: Regex pattern to search for
            
        Returns:
            List of [start, end] position pairs
        """
        if not text or not pattern:
            return []
        
        try:
            positions = []
            for match in re.finditer(pattern, text, re.IGNORECASE):
                positions.append([match.start(), match.end()])
            return positions
        except re.error as e:
            logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            return []
    
    def fuzzy_match(self, text: str, keyword: str) -> bool:
        """
        Check if keyword fuzzy matches in text using difflib.SequenceMatcher
        
        Args:
            text: Text to search in
            keyword: Keyword to search for
            
        Returns:
            True if fuzzy match found above threshold
        """
        if not text or not keyword:
            return False
        
        try:
            # Use SequenceMatcher for simple fuzzy matching
            matcher = SequenceMatcher(None, keyword.lower(), text.lower())
            similarity = matcher.ratio()
            return similarity >= self.fuzzy_threshold
        except Exception as e:
            logger.warning(f"Fuzzy matching failed for '{keyword}': {e}")
            return False
    
    def match_keyword(self, text: str, keyword: str) -> Dict:
        """
        Match a single keyword against text using multiple strategies
        
        Args:
            text: Text to search in
            keyword: Keyword to search for
            
        Returns:
            Dict with match results including positions and match type
        """
        if not text or not keyword:
            return {
                "text": keyword,
                "positions": [],
                "match_type": "none",
                "found": False
            }
        
        # Normalize text and keyword for matching
        normalized_text = normalize_nfkc_lower(text)
        normalized_keyword = normalize_nfkc_lower(keyword)
        
        # Try exact regex matching first
        pattern = build_regex_pattern(normalized_keyword)
        positions = self.find_positions(normalized_text, pattern)
        
        if positions:
            return {
                "text": keyword,
                "positions": positions,
                "match_type": "exact",
                "found": True
            }
        
        # Try fuzzy matching as fallback
        if self.fuzzy_match(normalized_text, normalized_keyword):
            return {
                "text": keyword,
                "positions": [],  # No positions for fuzzy matches
                "match_type": "fuzzy",
                "found": True
            }
        
        return {
            "text": keyword,
            "positions": [],
            "match_type": "none",
            "found": False
        }
    
    def compare_keywords_to_resume(self, resume_text: str, keywords: List[str]) -> Dict:
        """
        Compare a list of keywords to resume text
        
        Args:
            resume_text: Full resume text
            keywords: List of keywords to search for
            
        Returns:
            Dict with included/missing keywords and coverage stats
        """
        if not resume_text or not keywords:
            return {
                "included": [],
                "missing": [],
                "coverage": {"included": 0, "missing": 0, "percent": 0.0}
            }
        
        # Clean text for matching
        cleaned_text = clean_text_for_matching(resume_text)
        
        included = []
        missing = []
        
        for keyword in keywords:
            match_result = self.match_keyword(cleaned_text, keyword)
            
            if match_result["found"]:
                included.append({
                    "text": keyword,
                    "positions": match_result["positions"],
                    "match_type": match_result["match_type"]
                })
            else:
                missing.append({
                    "text": keyword
                })
        
        # Calculate coverage
        total = len(keywords)
        included_count = len(included)
        missing_count = len(missing)
        percent = (included_count / total * 100) if total > 0 else 0.0
        
        return {
            "included": included,
            "missing": missing,
            "coverage": {
                "included": included_count,
                "missing": missing_count,
                "percent": round(percent, 1)
            }
        }
