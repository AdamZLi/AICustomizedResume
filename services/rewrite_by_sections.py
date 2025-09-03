"""
Orchestrator for section-based resume rewriting using minimal insertions
"""
import logging
from typing import Dict, List, Tuple, Optional, Any
from models import ChangeLogItem
from services.sections import SectionParser
from services.minimal_insert import MinimalInsertionService
from services.tokens import token_manager

logger = logging.getLogger(__name__)

class ResumeRewriter:
    def __init__(self):
        self.section_parser = SectionParser()
        self.minimal_insertion_service = MinimalInsertionService()
    
    def rewrite_resume_by_sections(
        self, 
        full_text: str, 
        selected_keywords: List[str], 
        job_title: Optional[str] = None,
        tone: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Rewrite resume by sections using minimal insertions
        Returns: { updated_text, included_keywords, change_log }
        """
        try:
            logger.info(f"Starting minimal insertion resume rewrite with {len(selected_keywords)} keywords")
            
            # Step 1: Split resume into sections
            sections = self.section_parser.split_resume_into_sections(full_text)
            logger.info(f"Parsed resume into {len(sections)} sections: {list(sections.keys())}")
            
            # Step 2: Process each section with minimal insertions
            processed_sections = {}
            all_included_keywords = []
            all_change_logs = []
            
            section_order = self.section_parser.get_section_order()
            
            for section_name in section_order:
                if section_name in sections:
                    section_content = sections[section_name]
                    
                    # Log section details
                    original_chars = len(section_content)
                    original_tokens = token_manager.count_tokens(section_content)
                    logger.info(f"Processing section '{section_name}': {original_chars} chars, {original_tokens} tokens")
                    
                    # Validate budget
                    is_valid, token_count, error_msg = token_manager.validate_section_budget(section_content, section_name)
                    if not is_valid:
                        logger.warning(f"Section '{section_name}' exceeds budget: {error_msg}")
                        # Keep original content for this section
                        processed_sections[section_name] = section_content
                        continue
                    
                    # Process section with minimal insertions
                    try:
                        result = self._process_section_with_insertions(
                            section_name, section_content, selected_keywords, job_title
                        )
                        
                        processed_sections[section_name] = result["updated_text"]
                        all_included_keywords.extend(result["included_keywords"])
                        
                        # Convert change log items
                        for change in result["change_log"]:
                            change_log_item = ChangeLogItem(
                                section=section_name,
                                before=change.get("before", ""),
                                after=change.get("after", ""),
                                keywords_used=change.get("keywords_used", [])
                            )
                            all_change_logs.append(change_log_item)
                        
                        logger.info(f"Successfully processed section '{section_name}' with {len(result['included_keywords'])} keywords")
                        
                    except Exception as e:
                        logger.warning(f"Failed to process section '{section_name}': {e}")
                        # Keep original content if processing fails
                        processed_sections[section_name] = section_content
            
            # Step 3: Combine sections in canonical order
            updated_text = self._combine_sections(processed_sections, section_order)
            
            # Step 4: Remove duplicate keywords
            unique_keywords = list(set(all_included_keywords))
            
            logger.info(f"Minimal insertion rewrite complete: {len(processed_sections)} sections, {len(unique_keywords)} keywords, {len(all_change_logs)} changes")
            
            return {
                "updated_text": updated_text,
                "included_keywords": unique_keywords,
                "change_log": all_change_logs
            }
            
        except Exception as e:
            logger.error(f"Minimal insertion rewrite failed: {e}")
            raise Exception(f"Resume rewrite failed: {str(e)}")

    def _process_section_with_insertions(
        self, 
        section_name: str, 
        section_content: str, 
        selected_keywords: List[str], 
        job_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single section using minimal insertions
        Returns: Dict with updated_text, included_keywords, change_log
        """
        try:
            # Split section into lines
            lines = section_content.split('\n')
            if not lines:
                return {
                    "updated_text": section_content,
                    "included_keywords": [],
                    "change_log": []
                }
            
            # Get keywords for this section
            section_keywords = self._get_keywords_for_section(
                section_name, selected_keywords
            )
            
            if not section_keywords:
                logger.info(f"No keywords selected for section '{section_name}'")
                return {
                    "updated_text": section_content,
                    "included_keywords": [],
                    "change_log": []
                }
            
            # Plan insertions
            logger.info(f"Planning insertions for section '{section_name}' with {len(section_keywords)} keywords")
            insertion_plan = self.minimal_insertion_service.plan_insertions(
                lines, section_keywords, section_name
            )
            
            # Apply insertions with guardrails
            logger.info(f"Applying {len(insertion_plan.edits)} insertions to section '{section_name}'")
            updated_lines, change_log, included_keywords = self.minimal_insertion_service.apply_insertions(
                lines, insertion_plan
            )
            
            # Reconstruct section text
            updated_text = '\n'.join(updated_lines)
            
            # Log results
            logger.info(f"Section '{section_name}': {len(included_keywords)} keywords inserted, {len(insertion_plan.skipped_keywords)} skipped")
            
            return {
                "updated_text": updated_text,
                "included_keywords": included_keywords,
                "change_log": change_log
            }
            
        except Exception as e:
            logger.error(f"Failed to process section '{section_name}' with insertions: {e}")
            # Return original content on failure
            return {
                "updated_text": section_content,
                "included_keywords": [],
                "change_log": []
            }

    def _get_keywords_for_section(self, section_name: str, all_keywords: List[str]) -> List[str]:
        """Get keywords that should be placed in this specific section"""
        # For now, use all keywords for all sections
        # This can be enhanced with keyword placement analysis later
        return all_keywords

    def _combine_sections(self, sections: Dict[str, str], section_order: List[str]) -> str:
        """Combine processed sections back into full resume"""
        combined_lines = []
        
        for section_name in section_order:
            if section_name in sections:
                section_content = sections[section_name]
                if section_content.strip():
                    # Add section header
                    section_header = self.section_parser.get_section_header(section_name)
                    combined_lines.append(section_header)
                    combined_lines.append("")  # Empty line
                    
                    # Add section content
                    combined_lines.append(section_content)
                    combined_lines.append("")  # Empty line
        
        return '\n'.join(combined_lines).strip()
