"""
Token management service for section-based resume processing
"""
import tiktoken
import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)

class TokenManager:
    def __init__(self):
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # Token budgets per section
        self.MAX_INPUT_TOKENS = 1800
        self.MAX_OUTPUT_TOKENS = 500
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        return len(self.encoding.encode(text))
    
    def ensure_budget(self, text: str, max_in_tokens: int = 1800) -> str:
        """
        Ensure text fits within token budget by trimming to budget by paragraphs if over
        Returns: trimmed text that fits within budget
        """
        token_count = self.count_tokens(text)
        
        if token_count <= max_in_tokens:
            return text
        
        logger.info(f"Text exceeds budget: {token_count} > {max_in_tokens} tokens, trimming by paragraphs")
        
        # Split into paragraphs
        paragraphs = self._split_into_paragraphs(text)
        
        # Build text back up within budget
        result_paragraphs = []
        current_tokens = 0
        
        for paragraph in paragraphs:
            paragraph_tokens = self.count_tokens(paragraph)
            
            if current_tokens + paragraph_tokens <= max_in_tokens:
                result_paragraphs.append(paragraph)
                current_tokens += paragraph_tokens
            else:
                # If this paragraph would exceed budget, try to fit part of it
                if current_tokens < max_in_tokens * 0.8:  # Leave some buffer
                    partial_paragraph = self._truncate_to_tokens(paragraph, max_in_tokens - current_tokens)
                    if partial_paragraph.strip():
                        result_paragraphs.append(partial_paragraph)
                break
        
        result = '\n\n'.join(result_paragraphs)
        final_tokens = self.count_tokens(result)
        
        logger.info(f"Trimmed text: {token_count} -> {final_tokens} tokens")
        return result
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs using various delimiters"""
        # Split by double newlines, bullet points, or other paragraph boundaries
        paragraphs = re.split(r'\n\s*\n|\n\s*[-•]\s*|\n\s*[A-Z][^a-z]', text)
        
        # Clean up paragraphs
        cleaned_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 10:  # Minimum paragraph length
                cleaned_paragraphs.append(para)
        
        return cleaned_paragraphs
    
    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)
    
    def validate_section_budget(self, text: str, section_name: str) -> Tuple[bool, int, str]:
        """Validate if a section fits within budget"""
        token_count = self.count_tokens(text)
        
        if token_count > self.MAX_INPUT_TOKENS:
            return False, token_count, f"Section '{section_name}' exceeds {self.MAX_INPUT_TOKENS} token limit (has {token_count} tokens)"
        
        return True, token_count, ""

# Global instance
token_manager = TokenManager()
