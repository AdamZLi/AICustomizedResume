"""
OpenAI client for line-level minimal resume editing with structured outputs
"""
import os
import json
import logging
import time
import re
import traceback
from typing import List, Optional, Dict, Any, Tuple
from openai import OpenAI
from models import ChangeLogItem
from services.tokens import token_manager
from services.keyword_placement import KeywordPlacementService

# Import Levenshtein for character delta validation
try:
    import Levenshtein
except ImportError:
    # Fallback implementation if Levenshtein is not available
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]
    
    class Levenshtein:
        @staticmethod
        def distance(s1, s2):
            return levenshtein_distance(s1, s2)

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        self.keyword_placement_service = KeywordPlacementService()
        
        # Token budgets
        self.MAX_INPUT_TOKENS = 1800
        self.MAX_OUTPUT_TOKENS = 500
        
        # JSON schema for line-level minimal edits
        self.MINIMAL_EDITS_SCHEMA = {
            "name": "resume_minimal_edits",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "edits": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "line": {"type": "integer", "minimum": 1},
                                "replacement": {"type": "string"},
                                "keywords_used": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["line", "replacement", "keywords_used"]
                        }
                    },
                    "skipped_keywords": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["edits", "skipped_keywords"]
            }
        }

    def rewrite_section(
        self, 
        section_name: str, 
        text: str, 
        selected_keywords: List[str], 
        job_title: Optional[str] = None,
        tone: Optional[str] = None,
        full_resume_text: Optional[str] = None,
        all_sections: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Rewrite a single section using line-level minimal edits
        Returns: Dict with section, updated_text, included_keywords, change_log
        """
        try:
            # Split text into lines for processing
            lines = text.split('\n')
            if not lines:
                return self._create_fallback_response(section_name, text)
            
            # Get keywords for this section
            section_keywords = self._get_keywords_for_section(
                section_name, selected_keywords, all_sections or {}, full_resume_text or ""
            )
            
            if not section_keywords:
                return self._create_fallback_response(section_name, text)
            
            # Build line-level prompt
            prompt = self._build_line_level_prompt(section_name, lines, section_keywords, job_title)
            
            # Call OpenAI with structured output
            response = self._call_openai_with_retry(prompt)
            
            # Parse and validate response
            result = self._parse_minimal_edits_response(response.content)
            
            # Apply edits with validation
            updated_lines, change_log, included_keywords = self._apply_edits_with_validation(
                lines, result.get('edits', [])
            )
            
            # Reconstruct text
            updated_text = '\n'.join(updated_lines)
            
            logger.info(f"Successfully processed section '{section_name}' with {len(included_keywords)} keywords")
            
            return {
                "section": section_name,
                "updated_text": updated_text,
                "included_keywords": included_keywords,
                "change_log": change_log
            }
            
        except Exception as e:
            logger.error(f"Failed to rewrite section '{section_name}': {e}")
            return self._create_fallback_response(section_name, text)

    def _build_line_level_prompt(
        self, 
        section_name: str, 
        lines: List[str], 
        keywords: List[str], 
        job_title: Optional[str] = None
    ) -> str:
        """Build prompt for line-level minimal edits"""
        keywords_str = ", ".join(keywords)
        
        # Number the lines
        numbered_lines = []
        for i, line in enumerate(lines, 1):
            numbered_lines.append(f"{i}. {line}")
        
        lines_text = "\n".join(numbered_lines)
        
        prompt = f"""You are a conservative résumé copy editor.
Your ONLY job is to insert short keywords into specific lines with minimal surface change.
Do not reorder, delete, or add lines. Do not change bullet/indent characters.

SECTION: {section_name.upper()}

SELECTED_KEYWORDS (ranked): {keywords_str}

LINES (numbered; treat each as immutable except for minimal insertions):
{lines_text}

Allowed edit styles (choose the first that fits naturally):
A) add a 1–3 word **modifier** before a noun (e.g., "Agile project timelines")
B) add a short **parenthetical** (e.g., "backup (RTO/RPO)")
C) add a brief **with/using** tail (e.g., ", using A/B testing")

Hard rules:
- Edit **only** lines where a keyword can fit naturally.
- Keep each changed line's delta ≤ **20 characters**.
- Keep line count, order, bullet/indent characters **exactly the same**.
- If a keyword doesn't fit, skip it (don't force).
- If nothing fits, return **no edits**.

Return ONLY JSON matching the schema."""

        if job_title:
            prompt += f"\n\nTARGET JOB TITLE: {job_title}"
        
        return prompt

    def _apply_edits_with_validation(
        self, 
        original_lines: List[str], 
        edits: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """Apply edits with server-side validation"""
        updated_lines = original_lines.copy()
        change_log = []
        included_keywords = []
        
        for edit in edits:
            try:
                line_num = edit.get('line', 0)
                replacement = edit.get('replacement', '')
                keywords_used = edit.get('keywords_used', [])
                
                # Validate line number
                if line_num < 1 or line_num > len(original_lines):
                    logger.warning(f"Invalid line number {line_num}, skipping edit")
                    continue
                
                original_line = original_lines[line_num - 1]
                
                # Validate bullet prefix preservation
                if not self._validate_bullet_prefix(original_line, replacement):
                    logger.warning(f"Bullet prefix changed in line {line_num}, skipping edit")
                    continue
                
                # Validate character delta
                if not self._validate_character_delta(original_line, replacement):
                    logger.warning(f"Character delta too large in line {line_num}, skipping edit")
                    continue
                
                # Apply the edit
                updated_lines[line_num - 1] = replacement
                
                # Add to change log
                change_log.append({
                    "before": original_line,
                    "after": replacement,
                    "keywords_used": keywords_used
                })
                
                # Add keywords to included list
                included_keywords.extend(keywords_used)
                
                logger.info(f"Applied edit to line {line_num}: {original_line[:50]}... → {replacement[:50]}...")
                
            except Exception as e:
                logger.error(f"Error applying edit: {e}")
                continue
        
        return updated_lines, change_log, list(set(included_keywords))

    def _validate_bullet_prefix(self, original: str, replacement: str) -> bool:
        """Validate that bullet/indent characters are preserved"""
        # Extract prefix (spaces, tabs, bullet points, etc.)
        original_prefix = re.match(r'^(\s*[•\-\*]?\s*)', original)
        replacement_prefix = re.match(r'^(\s*[•\-\*]?\s*)', replacement)
        
        if not original_prefix or not replacement_prefix:
            return False
        
        return original_prefix.group(1) == replacement_prefix.group(1)

    def _validate_character_delta(self, original: str, replacement: str) -> bool:
        """Validate that character delta is ≤ 20 characters"""
        delta = Levenshtein.distance(original, replacement)
        return delta <= 20

    def _parse_minimal_edits_response(self, content: str) -> Dict[str, Any]:
        """Parse and validate minimal edits response"""
        try:
            if not content:
                raise Exception("Empty response from OpenAI")
            
            result = json.loads(content)
            
            # Validate required fields
            required_fields = ["edits", "skipped_keywords"]
            for field in required_fields:
                if field not in result:
                    raise Exception(f"Missing required field: {field}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Full response content: {content}")
            raise Exception(f"Invalid JSON response from OpenAI: {e}")
        except Exception as e:
            raise Exception(f"Failed to parse OpenAI response: {e}")

    def _create_fallback_response(self, section_name: str, text: str) -> Dict[str, Any]:
        """Create fallback response when processing fails"""
        return {
            "section": section_name,
            "updated_text": text,
            "included_keywords": [],
            "change_log": []
        }

    def _get_keywords_for_section(
        self, 
        section_name: str, 
        all_keywords: List[str], 
        all_sections: Dict[str, str], 
        full_resume_text: str
    ) -> List[str]:
        """Get keywords that should be placed in this specific section"""
        if not all_sections:
            return all_keywords
        
        # Analyze placements for all keywords
        placements = self.keyword_placement_service.analyze_keyword_placements(
            full_resume_text, all_keywords, all_sections
        )
        
        # Filter placements for this section
        section_placements = [p for p in placements if p.section == section_name]
        
        # Get keywords for this section
        section_keywords = [p.keyword for p in section_placements]
        
        # If no specific placements found, use all keywords
        if not section_keywords:
            section_keywords = all_keywords
        
        logger.info(f"Selected {len(section_keywords)} keywords for section '{section_name}': {section_keywords}")
        return section_keywords

    def _call_openai_with_retry(self, prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        """Call OpenAI API with exponential backoff retry logic"""
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a conservative resume copy editor. Always respond with valid JSON matching the specified schema."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_schema", "json_schema": self.MINIMAL_EDITS_SCHEMA},
                    temperature=0.1,  # Very low temperature for conservative edits
                    max_tokens=self.MAX_OUTPUT_TOKENS
                )
                
                return response.choices[0].message
                
            except Exception as e:
                error_str = str(e).lower()
                
                if "429" in error_str or "rate limit" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 1
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"Rate limit exceeded after {max_retries} retries")
                
                if attempt < max_retries - 1:
                    logger.warning(f"OpenAI API error on attempt {attempt + 1}: {e}")
                    time.sleep(1)
                    continue
                else:
                    raise Exception(f"OpenAI API failed after {max_retries} attempts: {e}")
        
        raise Exception("All retry attempts failed")
