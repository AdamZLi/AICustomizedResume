"""
Truly minimal insertion service for conservative resume editing
Changes so subtle they're barely noticeable - just natural keyword insertions
"""
import json
import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from openai import OpenAI
import os

try:
    import Levenshtein
except ImportError:
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

@dataclass
class InsertionPlan:
    edits: List[Dict[str, Any]]
    skipped_keywords: List[str]

@dataclass
class InsertionEdit:
    line: int
    strategy: str
    insertion: str
    keywords_used: List[str]

class MinimalInsertionService:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        
        self.INSERTION_SCHEMA = {
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
                                "strategy": {"type": "string", "enum": ["modifier", "parenthetical", "tail"]},
                                "insertion": {"type": "string", "description": "the 1–2 word phrase to insert"},
                                "keywords_used": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["line", "strategy", "insertion", "keywords_used"]
                        }
                    },
                    "skipped_keywords": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["edits", "skipped_keywords"]
            }
        }

    def plan_insertions(self, lines: List[str], keywords: List[str], section_name: str) -> InsertionPlan:
        try:
            prompt = self._build_insertion_prompt(lines, keywords, section_name)
            response = self._call_openai_with_schema(prompt)
            result = self._parse_insertion_response(response.content)
            
            edits = []
            for edit_data in result.get('edits', []):
                edit = InsertionEdit(
                    line=edit_data['line'],
                    strategy=edit_data['strategy'],
                    insertion=edit_data['insertion'],
                    keywords_used=edit_data['keywords_used']
                )
                edits.append(edit)
            
            return InsertionPlan(
                edits=edits,
                skipped_keywords=result.get('skipped_keywords', [])
            )
            
        except Exception as e:
            logger.error(f"Failed to plan insertions: {e}")
            return InsertionPlan(edits=[], skipped_keywords=keywords)

    def apply_insertions(self, lines: List[str], plan: InsertionPlan) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        updated_lines = lines.copy()
        change_log = []
        included_keywords = []
        
        for edit in plan.edits:
            try:
                if edit.line < 1 or edit.line > len(lines):
                    continue
                
                original_line = lines[edit.line - 1]
                new_line = self._apply_insertion_strategy(original_line, edit)
                
                if new_line is None:
                    continue
                
                if not self._validate_bullet_prefix(original_line, new_line):
                    continue
                
                if not self._validate_character_delta(original_line, new_line):
                    continue
                
                updated_lines[edit.line - 1] = new_line
                
                change_log.append({
                    "before": original_line,
                    "after": new_line,
                    "keywords_used": edit.keywords_used,
                    "strategy": edit.strategy
                })
                
                included_keywords.extend(edit.keywords_used)
                logger.info(f"Applied {edit.strategy} insertion to line {edit.line}: {edit.insertion}")
                
            except Exception as e:
                logger.error(f"Error applying insertion: {e}")
                continue
        
        return updated_lines, change_log, list(set(included_keywords))

    def _build_insertion_prompt(self, lines: List[str], keywords: List[str], section_name: str) -> str:
        keywords_str = ", ".join(keywords)
        numbered_lines = []
        for i, line in enumerate(lines, 1):
            numbered_lines.append(f"{i}. {line}")
        
        lines_text = "\n".join(numbered_lines)
        
        prompt = f"""You are a conservative résumé copy editor.

Task: propose TRULY MINIMAL keyword insertions that are barely noticeable.
Return ONLY JSON per the schema.

SECTION: {section_name.upper()}

SELECTED_KEYWORDS (ranked): {keywords_str}

LINES (numbered; each line is immutable except for a tiny insertion):
{lines_text}

Allowed insertion strategies (pick the first that fits naturally):
A) single word modifier before a noun (e.g., "project management" → "Agile project management")
B) brief parenthetical at end (e.g., "team leadership" → "team leadership (remote)")
C) simple tail addition (e.g., "data analysis" → "data analysis, Python")

Hard rules:
- Do NOT reorder, add, or delete lines. Preserve bullet/indent characters exactly.
- Max change per edited line: ≤ 25 characters AND ≤ 2 words maximum.
- Changes must be so subtle they're barely noticeable when reading.
- If a keyword cannot fit naturally, SKIP it.
- Do NOT change meaning or invent facts.
- Prefer placing a given keyword once in the most relevant single line.

Return ONLY JSON matching the schema."""
        
        return prompt

    def _apply_insertion_strategy(self, original_line: str, edit: InsertionEdit) -> Optional[str]:
        try:
            if edit.strategy == "modifier":
                return self._apply_modifier_insertion(original_line, edit.insertion)
            elif edit.strategy == "parenthetical":
                return self._apply_parenthetical_insertion(original_line, edit.insertion)
            elif edit.strategy == "tail":
                return self._apply_tail_insertion(original_line, edit.insertion)
            else:
                return None
        except Exception as e:
            logger.error(f"Error applying {edit.strategy} insertion: {e}")
            return None

    def _apply_modifier_insertion(self, line: str, insertion: str) -> str:
        words = line.split()
        for i, word in enumerate(words):
            if i > 0 and word[0].isupper() and len(word) > 2:
                words.insert(i, insertion)
                return " ".join(words)
        
        prefix_match = re.match(r'^(\s*[•\-\*]?\s*)', line)
        if prefix_match:
            prefix = prefix_match.group(1)
            rest = line[len(prefix):]
            return prefix + insertion + " " + rest
        
        return line

    def _apply_parenthetical_insertion(self, line: str, insertion: str) -> str:
        return line.rstrip() + f" ({insertion})"

    def _apply_tail_insertion(self, line: str, insertion: str) -> str:
        return line.rstrip() + f", {insertion}"

    def _validate_bullet_prefix(self, original: str, replacement: str) -> bool:
        original_prefix = re.match(r'^(\s*[•\-\*]?\s*)', original)
        replacement_prefix = re.match(r'^(\s*[•\-\*]?\s*)', replacement)
        
        if not original_prefix or not replacement_prefix:
            return False
        
        return original_prefix.group(1) == replacement_prefix.group(1)

    def _validate_character_delta(self, original: str, replacement: str) -> bool:
        delta = Levenshtein.distance(original, replacement)
        return delta <= 25

    def _call_openai_with_schema(self, prompt: str) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a conservative resume copy editor. Make changes so subtle they're barely noticeable. Always respond with valid JSON matching the specified schema."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_schema", "json_schema": self.INSERTION_SCHEMA},
                temperature=0.05,
                max_tokens=500
            )
            
            return response.choices[0].message
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    def _parse_insertion_response(self, content: str) -> Dict[str, Any]:
        try:
            if not content:
                raise Exception("Empty response from OpenAI")
            
            result = json.loads(content)
            
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
