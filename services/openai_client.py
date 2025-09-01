"""
OpenAI client for section-based resume rewriting with structured outputs
"""
import os
import json
import logging
import time
import re
import traceback
from typing import List, Optional, Dict, Any
from openai import OpenAI
from models import ChangeLogItem
from services.tokens import token_manager

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        
        # Token budgets
        self.MAX_INPUT_TOKENS = 1800
        self.MAX_OUTPUT_TOKENS = 500
        
        # JSON schema for structured output
        self.SECTION_SCHEMA = {
            "name": "resume_section_rewrite",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "section": {"type": "string"},
                "updated_text": {"type": "string"},
                "included_keywords": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "change_log": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "before": {"type": "string"},
                            "after": {"type": "string"},
                            "keywords_used": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["before", "after", "keywords_used"]
                    }
                }
            },
            "required": ["section", "updated_text", "included_keywords", "change_log"]
        }

    def rewrite_section(
        self, 
        section_name: str, 
        text: str, 
        selected_keywords: List[str], 
        job_title: Optional[str] = None,
        tone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rewrite a single section using structured outputs
        Returns: Dict with section, updated_text, included_keywords, change_log
        """
        try:
            # Ensure text fits within budget
            budgeted_text = token_manager.ensure_budget(text, self.MAX_INPUT_TOKENS)
            
            # Build prompt
            prompt = self._build_section_prompt(section_name, budgeted_text, selected_keywords, job_title, tone)
            
            # Call OpenAI with structured output
            response = self._call_openai_with_retry(prompt)
            
            # Parse and validate response
            result = self._parse_structured_response(response.content)
            
            # Validate required fields
            required_fields = ["section", "updated_text", "included_keywords", "change_log"]
            for field in required_fields:
                if field not in result:
                    raise Exception(f"Missing required field: {field}")
            
            logger.info(f"Successfully rewrote section '{section_name}' with {len(result['included_keywords'])} keywords")
            return result
            
        except Exception as e:
            logger.error(f"Failed to rewrite section '{section_name}': {e}")
            # Return original text if processing fails
            return {
                "section": section_name,
                "updated_text": text,
                "included_keywords": [],
                "change_log": []
            }

    def _build_section_prompt(
        self, 
        section_name: str, 
        text: str, 
        selected_keywords: List[str], 
        job_title: Optional[str] = None,
        tone: Optional[str] = None
    ) -> str:
        """Build prompt for section rewriting"""
        keywords_str = ", ".join(selected_keywords)
        
        prompt = f"""You are a résumé editor. Rewrite the {section_name} section to naturally include the SELECTED KEYWORDS (no fabrication). Keep structure/length similar; emphasize measurable impact.

SELECTED KEYWORDS: {keywords_str}
SECTION: {section_name.upper()}
ORIGINAL TEXT:
{text}

Return only JSON per the schema. Focus on incorporating keywords naturally while maintaining the original structure and impact."""

        if job_title:
            prompt += f"\n\nTARGET JOB TITLE: {job_title}"
        
        if tone:
            prompt += f"\n\nDESIRED TONE: {tone}"
        
        return prompt

    def _call_openai_with_retry(self, prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        """Call OpenAI API with exponential backoff retry logic"""
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Use gpt-4o-mini as recommended
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional resume writer. Always respond with valid JSON matching the specified schema."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_schema", "json_schema": self.SECTION_SCHEMA},
                    temperature=0.2,
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

    def _parse_structured_response(self, content: str) -> Dict[str, Any]:
        """Parse and validate structured response from OpenAI"""
        try:
            if not content:
                raise Exception("Empty response from OpenAI")
            
            logger.info(f"OpenAI response length: {len(content)}")
            
            # Parse JSON response
            result = json.loads(content)
            
            # Validate required fields
            required_fields = ["section", "updated_text", "included_keywords", "change_log"]
            for field in required_fields:
                if field not in result:
                    raise Exception(f"Missing required field: {field}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Full response content: {content}")
            
            # Try to extract JSON using regex as fallback
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    extracted_json = json_match.group()
                    result = json.loads(extracted_json)
                    
                    required_fields = ["section", "updated_text", "included_keywords", "change_log"]
                    for field in required_fields:
                        if field not in result:
                            raise Exception(f"Missing required field: {field}")
                    
                    logger.info("Successfully extracted JSON using regex fallback")
                    return result
                except Exception as fallback_error:
                    logger.error(f"Regex fallback also failed: {fallback_error}")
            
            raise Exception(f"Invalid JSON response from OpenAI: {e}")
        except Exception as e:
            raise Exception(f"Failed to parse OpenAI response: {e}")
