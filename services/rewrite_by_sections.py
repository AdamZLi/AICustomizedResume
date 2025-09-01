"""
Orchestrator for section-based resume rewriting
"""
import logging
from typing import Dict, List, Tuple, Optional
from models import ChangeLogItem
from services.sections import SectionParser
from services.openai_client import OpenAIClient
from services.tokens import token_manager

logger = logging.getLogger(__name__)

class ResumeRewriter:
    def __init__(self):
        self.section_parser = SectionParser()
        self.openai_client = OpenAIClient()
    
    def rewrite_resume_by_sections(
        self, 
        full_text: str, 
        selected_keywords: List[str], 
        job_title: Optional[str] = None,
        tone: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Rewrite resume by sections and combine results
        Returns: { updated_text, included_keywords, change_log }
        """
        try:
            logger.info(f"Starting section-based resume rewrite with {len(selected_keywords)} keywords")
            
            # Step 1: Split resume into sections
            sections = self.section_parser.split_resume_into_sections(full_text)
            logger.info(f"Parsed resume into {len(sections)} sections: {list(sections.keys())}")
            
            # Step 2: Process each section
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
                    
                    # Rewrite section
                    try:
                        result = self.openai_client.rewrite_section(
                            section_name, section_content, selected_keywords, job_title, tone
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
                        
                        logger.info(f"Successfully processed section '{section_name}'")
                        
                    except Exception as e:
                        logger.warning(f"Failed to process section '{section_name}': {e}")
                        # Keep original content if processing fails
                        processed_sections[section_name] = section_content
            
            # Step 3: Combine sections in canonical order
            updated_text = self._combine_sections(processed_sections, section_order)
            
            # Step 4: Remove duplicate keywords
            unique_keywords = list(set(all_included_keywords))
            
            logger.info(f"Section-based rewrite complete: {len(processed_sections)} sections, {len(unique_keywords)} keywords, {len(all_change_logs)} changes")
            
            return {
                "updated_text": updated_text,
                "included_keywords": unique_keywords,
                "change_log": all_change_logs
            }
            
        except Exception as e:
            logger.error(f"Section-based rewrite failed: {e}")
            raise Exception(f"Resume rewrite failed: {str(e)}")
    
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
