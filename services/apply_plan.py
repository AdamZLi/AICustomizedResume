"""
Apply Plan Service for Resume Tailoring
Safely applies edit plans with validation and change logging
"""
import logging
import re
from typing import List, Dict, Any, Tuple
from Levenshtein import distance as levenshtein_distance
from models import ChangeLogItem

logger = logging.getLogger(__name__)

class ApplyPlanService:
    def __init__(self):
        self.max_char_delta = 25
        self.max_word_delta = 3  # Allow up to 3 words for more natural insertions

    def apply_edit_plan(
        self, 
        original_lines: List[str], 
        edit_plan: Dict[str, Any]
    ) -> Tuple[List[str], List[ChangeLogItem], List[str]]:
        """
        Apply an edit plan to the original lines with validation
        
        Args:
            original_lines: List of original text lines
            edit_plan: Edit plan from EditPlanService
            
        Returns:
            Tuple of (updated_lines, change_log, applied_keywords)
        """
        try:
            updated_lines = original_lines.copy()
            change_log = []
            applied_keywords = []
            
            edits = edit_plan.get("edits", [])
            
            # Sort edits by line number to process in order
            edits.sort(key=lambda x: x["line"])
            
            for edit in edits:
                line_num = edit["line"]
                
                # Validate line number
                if line_num < 1 or line_num > len(original_lines):
                    logger.warning(f"Invalid line number {line_num}, skipping edit")
                    continue
                
                # Get original line (convert to 0-based index)
                original_line = original_lines[line_num - 1]
                
                # Apply the edit
                result = self._apply_single_edit(original_line, edit)
                
                if result["success"]:
                    updated_lines[line_num - 1] = result["updated_line"]
                    
                    # Create change log entry
                    change_log.append(ChangeLogItem(
                        section=f"Line {line_num}",
                        before=original_line,
                        after=result["updated_line"],
                        keywords_used=edit["keywords_used"]
                    ))
                    
                    # Track applied keywords
                    applied_keywords.extend(edit["keywords_used"])
                    
                    logger.info(f"Applied edit to line {line_num}: {edit['strategy']} - {edit['insertion']}")
                else:
                    logger.warning(f"Failed to apply edit to line {line_num}: {result['reason']}")
            
            # Remove duplicates from applied keywords
            applied_keywords = list(set(applied_keywords))
            
            return updated_lines, change_log, applied_keywords
            
        except Exception as e:
            logger.error(f"Error applying edit plan: {str(e)}")
            # Return original lines on error
            return original_lines, [], []

    def _apply_single_edit(self, original_line: str, edit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a single edit to a line with validation
        
        Args:
            original_line: Original text line
            edit: Single edit from the plan
            
        Returns:
            Dict with success status, updated line, and reason if failed
        """
        try:
            strategy = edit["strategy"]
            insertion = edit["insertion"]
            after_anchor = edit.get("after_anchor", "")
            
            # Validate insertion length
            if len(insertion) > self.max_char_delta:
                return {
                    "success": False,
                    "updated_line": original_line,
                    "reason": f"Insertion too long: {len(insertion)} chars (max {self.max_char_delta})"
                }
            
            # Apply strategy
            if strategy == "modifier":
                updated_line = self._apply_modifier_strategy(original_line, insertion)
            elif strategy == "parenthetical":
                updated_line = self._apply_parenthetical_strategy(original_line, insertion, after_anchor)
            elif strategy == "tail":
                updated_line = self._apply_tail_strategy(original_line, insertion, after_anchor)
            else:
                return {
                    "success": False,
                    "updated_line": original_line,
                    "reason": f"Unknown strategy: {strategy}"
                }
            
            # Validate the change
            validation = self._validate_line_change(original_line, updated_line)
            if not validation["valid"]:
                return {
                    "success": False,
                    "updated_line": original_line,
                    "reason": validation["reason"]
                }
            
            return {
                "success": True,
                "updated_line": updated_line,
                "reason": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "updated_line": original_line,
                "reason": f"Error applying edit: {str(e)}"
            }

    def _apply_modifier_strategy(self, original_line: str, insertion: str) -> str:
        """Apply modifier strategy: add word before existing content"""
        # Find the first word boundary
        words = original_line.split()
        if not words:
            return original_line
        
        # Insert the modifier before the first word
        return f"{insertion} {original_line}"

    def _apply_parenthetical_strategy(self, original_line: str, insertion: str, after_anchor: str) -> str:
        """Apply parenthetical strategy: add insertion after anchor text"""
        if after_anchor:
            # Insert after the first occurrence of anchor text
            anchor_pos = original_line.find(after_anchor)
            if anchor_pos != -1:
                insert_pos = anchor_pos + len(after_anchor)
                # Don't add extra parentheses if insertion already has them
                if insertion.startswith(' (') and insertion.endswith(')'):
                    return original_line[:insert_pos] + insertion + original_line[insert_pos:]
                else:
                    return original_line[:insert_pos] + f" ({insertion})" + original_line[insert_pos:]
        
        # Fallback: add at the end
        if insertion.startswith(' (') and insertion.endswith(')'):
            return f"{original_line}{insertion}"
        else:
            return f"{original_line} ({insertion})"

    def _apply_tail_strategy(self, original_line: str, insertion: str, after_anchor: str) -> str:
        """Apply tail strategy: add insertion after anchor text"""
        if after_anchor:
            # Insert after the first occurrence of anchor text
            anchor_pos = original_line.find(after_anchor)
            if anchor_pos != -1:
                insert_pos = anchor_pos + len(after_anchor)
                # Don't add extra comma if insertion already has one
                if insertion.startswith(', '):
                    return original_line[:insert_pos] + insertion + original_line[insert_pos:]
                else:
                    # Check if we need to add a comma
                    if original_line[insert_pos:].strip() and not original_line[insert_pos:].strip().startswith(','):
                        return original_line[:insert_pos] + f", {insertion}" + original_line[insert_pos:]
                    else:
                        return original_line[:insert_pos] + f" {insertion}" + original_line[insert_pos:]
        
        # Fallback: add at the end
        if insertion.startswith(', '):
            return f"{original_line}{insertion}"
        else:
            return f"{original_line}, {insertion}"

    def _validate_line_change(self, original_line: str, updated_line: str) -> Dict[str, Any]:
        """
        Validate that a line change meets our constraints
        
        Args:
            original_line: Original text line
            updated_line: Updated text line
            
        Returns:
            Dict with validation result and reason if invalid
        """
        try:
            # Check character delta
            char_delta = abs(len(updated_line) - len(original_line))
            if char_delta > self.max_char_delta:
                return {
                    "valid": False,
                    "reason": f"Character delta too large: {char_delta} (max {self.max_char_delta})"
                }
            
            # Check word delta
            original_words = len(original_line.split())
            updated_words = len(updated_line.split())
            word_delta = abs(updated_words - original_words)
            if word_delta > self.max_word_delta:
                return {
                    "valid": False,
                    "reason": f"Word delta too large: {word_delta} (max {self.max_word_delta})"
                }
            
            # Check Levenshtein distance
            lev_distance = levenshtein_distance(original_line, updated_line)
            if lev_distance > self.max_char_delta:
                return {
                    "valid": False,
                    "reason": f"Levenshtein distance too large: {lev_distance} (max {self.max_char_delta})"
                }
            
            # Check that original line is preserved (no reordering)
            if not self._preserves_original_structure(original_line, updated_line):
                return {
                    "valid": False,
                    "reason": "Original line structure not preserved"
                }
            
            return {"valid": True, "reason": None}
            
        except Exception as e:
            return {
                "valid": False,
                "reason": f"Validation error: {str(e)}"
            }

    def _preserves_original_structure(self, original_line: str, updated_line: str) -> bool:
        """
        Check if the updated line preserves the original structure
        """
        # Remove whitespace for comparison
        original_clean = re.sub(r'\s+', ' ', original_line.strip())
        updated_clean = re.sub(r'\s+', ' ', updated_line.strip())
        
        # Check if original content is still present
        original_words = set(original_clean.lower().split())
        updated_words = set(updated_clean.lower().split())
        
        # At least 70% of original words should be preserved (more lenient)
        preserved_words = len(original_words.intersection(updated_words))
        preservation_ratio = preserved_words / len(original_words) if original_words else 1.0
        
        # Also check if the updated line contains the original line as a substring
        # This handles cases where we're adding modifiers or tails
        contains_original = original_clean.lower() in updated_clean.lower()
        
        return preservation_ratio >= 0.7 or contains_original

    def generate_diff_preview(self, original_lines: List[str], updated_lines: List[str]) -> List[Dict[str, Any]]:
        """
        Generate a diff preview for the UI
        
        Args:
            original_lines: Original text lines
            updated_lines: Updated text lines
            
        Returns:
            List of diff entries for each line
        """
        diff_preview = []
        
        max_lines = max(len(original_lines), len(updated_lines))
        
        for i in range(max_lines):
            original = original_lines[i] if i < len(original_lines) else ""
            updated = updated_lines[i] if i < len(updated_lines) else ""
            
            if original != updated:
                diff_preview.append({
                    "line_number": i + 1,
                    "original": original,
                    "updated": updated,
                    "type": "modified"
                })
            else:
                diff_preview.append({
                    "line_number": i + 1,
                    "original": original,
                    "updated": updated,
                    "type": "unchanged"
                })
        
        return diff_preview
