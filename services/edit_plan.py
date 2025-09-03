"""
Edit Plan Service for Resume Tailoring
Generates structured edit plans using OpenAI's structured outputs
"""
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class EditPlanService:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        
        # JSON schema for minimal edits
        self.EDIT_PLAN_SCHEMA = {
            "name": "resume_minimal_edits",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "edits": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "line": {"type": "integer", "minimum": 1},
                                "strategy": {"type": "string", "enum": ["modifier", "parenthetical", "tail"]},
                                "after_anchor": {"type": "string"},
                                "insertion": {"type": "string", "maxLength": 25},
                                "keywords_used": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["line", "strategy", "insertion", "keywords_used"],
                            "additionalProperties": False
                        }
                    },
                    "skipped_keywords": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["edits", "skipped_keywords"],
                "additionalProperties": False
            }
        }

    def make_edit_plan(
        self, 
        section_name: str, 
        lines: List[str], 
        selected_keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Generate an edit plan for a section using OpenAI's structured outputs
        
        Args:
            section_name: Name of the resume section
            lines: List of text lines from the section
            selected_keywords: Keywords to incorporate
            
        Returns:
            Dict containing the edit plan with edits array and skipped_keywords
        """
        try:
            # Prepare the prompt
            prompt = self._build_prompt(section_name, lines, selected_keywords)
            
            # Make the API call with structured output
            try:
                # Try the new structured output format first
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a resume optimization expert. Your job is to propose minimal insertions to incorporate keywords without rewriting content."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_schema"},
                    json_schema=self.EDIT_PLAN_SCHEMA["schema"],
                    temperature=0.3,
                    max_tokens=1000
                )
            except TypeError as e:
                if "json_schema" in str(e):
                    # Fallback to older API format without json_schema
                    logger.info("Using fallback API format without json_schema")
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a resume optimization expert. Your job is to propose minimal insertions to incorporate keywords without rewriting content. You MUST return valid JSON."
                            },
                            {
                                "role": "user",
                                "content": prompt + "\n\nIMPORTANT: Return ONLY valid JSON matching the schema. Do not include any other text."
                            }
                        ],
                        temperature=0.3,
                        max_tokens=1000
                    )
                else:
                    raise e
            
            # Parse the response
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
                
            edit_plan = json.loads(content)
            
            # Validate the response structure
            if not self._validate_edit_plan(edit_plan):
                raise ValueError("Invalid edit plan structure from OpenAI")
                
            logger.info(f"Generated edit plan for {section_name} with {len(edit_plan.get('edits', []))} edits")
            return edit_plan
            
        except Exception as e:
            logger.error(f"Error generating edit plan: {str(e)}")
            # Try fallback edit generation
            logger.info("Attempting fallback edit generation...")
            fallback_plan = self._generate_fallback_edits(section_name, lines, selected_keywords)
            if fallback_plan["edits"]:
                logger.info(f"Generated {len(fallback_plan['edits'])} fallback edits")
                return fallback_plan
            else:
                # Return empty plan if fallback also fails
                return {
                    "edits": [],
                    "skipped_keywords": selected_keywords
                }

    def _build_prompt(self, section_name: str, lines: List[str], selected_keywords: List[str]) -> str:
        """Build the prompt for the OpenAI API call"""
        
        lines_text = "\n".join([f"{i+1}: {line}" for i, line in enumerate(lines)])
        keywords_text = ", ".join(selected_keywords)
        
        prompt = f"""
You are optimizing a resume {section_name} section to incorporate these keywords: {keywords_text}

ORIGINAL TEXT (with line numbers):
{lines_text}

TASK: Propose minimal insertions per line number (NO rewrites). You MUST find opportunities to incorporate keywords.

ALLOWED STRATEGIES:
- "modifier": Single-word modifier (e.g., "experienced" → "experienced Python developer")
- "parenthetical": Brief parenthetical addition (e.g., "Python" → "Python (with Django)")
- "tail": Tiny tail addition (e.g., "testing" → "testing, using A/B testing")

CONSTRAINTS:
- Max change per line: 2 words OR 25 characters
- Don't reorder/delete lines or bullets
- Be creative and find insertion points - don't be overly conservative
- Preserve original meaning and flow
- You MUST find at least 1-2 opportunities for relevant keywords

EXAMPLES OF GOOD EDITS:
- Line 2: "Sourced pre-seed SaaS and AI startups" → "Sourced pre-seed SaaS and AI startups (using Python)"
- Line 4: "leveraging A/B testing and data analytics" → "leveraging A/B testing and data analytics, with Docker"
- Line 2: "funneled top prospects to the investment team" → "funneled top prospects to the investment team using agile methods"

RETURN: JSON matching the schema exactly. Each edit should specify:
- line: line number (1-based)
- strategy: one of the three allowed strategies
- after_anchor: text to insert after (if applicable, otherwise empty string)
- insertion: the text to add (max 25 chars)
- keywords_used: list of keywords this edit incorporates

Look for opportunities to add keywords naturally. If keywords are relevant to the role, try to find at least 1-2 insertion points.
"""
        return prompt

    def _generate_fallback_edits(self, section_name: str, lines: List[str], selected_keywords: List[str]) -> Dict[str, Any]:
        """
        Generate fallback edits when AI model fails
        Uses simple heuristics to find keyword insertion opportunities
        """
        edits = []
        skipped_keywords = []
        
        for keyword in selected_keywords:
            keyword_lower = keyword.lower()
            inserted = False
            
            # Look for opportunities in each line
            for i, line in enumerate(lines):
                line_lower = line.lower()
                
                # Skip if line is too short or already contains the keyword
                if len(line) < 20 or keyword_lower in line_lower:
                    continue
                
                # Strategy 1: Add as tail to lines about work/processes
                if any(word in line_lower for word in ['team', 'startups', 'analytics', 'testing', 'app', 'users']):
                    if not inserted and len(keyword) <= 15:  # Keep insertion short
                        edits.append({
                            "line": i + 1,
                            "strategy": "tail",
                            "after_anchor": "",
                            "insertion": f", {keyword}",
                            "keywords_used": [keyword]
                        })
                        inserted = True
                        break
                
                # Strategy 2: Add as parenthetical for technical terms
                elif any(word in line_lower for word in ['python', 'ai', 'saas', 'web']):
                    if not inserted and len(keyword) <= 20:
                        edits.append({
                            "line": i + 1,
                            "strategy": "parenthetical",
                            "after_anchor": "",
                            "insertion": f" ({keyword})",
                            "keywords_used": [keyword]
                        })
                        inserted = True
                        break
            
            if not inserted:
                skipped_keywords.append(keyword)
        
        return {
            "edits": edits,
            "skipped_keywords": skipped_keywords
        }

    def _validate_edit_plan(self, edit_plan: Dict[str, Any]) -> bool:
        """Validate the structure of the edit plan"""
        try:
            if not isinstance(edit_plan, dict):
                return False
                
            if "edits" not in edit_plan or "skipped_keywords" not in edit_plan:
                return False
                
            if not isinstance(edit_plan["edits"], list):
                return False
                
            if not isinstance(edit_plan["skipped_keywords"], list):
                return False
                
            # Validate each edit
            for edit in edit_plan["edits"]:
                if not isinstance(edit, dict):
                    return False
                    
                required_fields = ["line", "strategy", "insertion", "keywords_used"]
                if not all(field in edit for field in required_fields):
                    return False
                    
                if not isinstance(edit["line"], int) or edit["line"] < 1:
                    return False
                    
                if edit["strategy"] not in ["modifier", "parenthetical", "tail"]:
                    return False
                    
                if not isinstance(edit["insertion"], str) or len(edit["insertion"]) > 25:
                    return False
                    
                if not isinstance(edit["keywords_used"], list):
                    return False
                    
            return True
            
        except Exception:
            return False
