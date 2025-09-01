"""
Robust resume parser service for extracting clean text from PDF files
"""
from pathlib import Path
import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

class ResumeParserService:
    def __init__(self):
        pass
    
    def extract_text(self, pdf_path: Path, preview_chars: int = 800) -> Tuple[str, str]:
        """
        Extract clean text from PDF using robust fallback chain
        Returns: (full_text, preview_text)
        """
        try:
            # Use the safe extraction method
            full_text = self.extract_text_safe(str(pdf_path))
            
            if not full_text:
                raise Exception("No usable text could be extracted from PDF")
            
            # Create preview excerpt
            preview_text = full_text[:preview_chars]
            if len(full_text) > preview_chars:
                preview_text += "..."
            
            logger.info(f"Successfully extracted {len(full_text)} characters from PDF")
            return full_text, preview_text
            
        except Exception as e:
            logger.error(f"Failed to parse PDF {pdf_path}: {e}")
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    def extract_text_safe(self, pdf_path: str) -> str:
        """
        Robust PDF text extraction with fallback chain and cleaning
        Returns: Clean text string
        """
        raw_text = ""
        
        # Try PyMuPDF first (highest quality)
        try:
            raw_text = self._extract_with_pymupdf(pdf_path)
            if raw_text:
                logger.info("Successfully extracted text using PyMuPDF")
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}")
        
        # Try pdfminer.six if PyMuPDF failed
        if not raw_text:
            try:
                raw_text = self._extract_with_pdfminer(pdf_path)
                if raw_text:
                    logger.info("Successfully extracted text using pdfminer.six")
            except Exception as e:
                logger.warning(f"pdfminer.six extraction failed: {e}")
        
        # Try pypdf as last resort
        if not raw_text:
            try:
                raw_text = self._extract_with_pypdf(pdf_path)
                if raw_text:
                    logger.info("Successfully extracted text using pypdf")
            except Exception as e:
                logger.warning(f"pypdf extraction failed: {e}")
        
        if not raw_text:
            raise Exception("All PDF text extraction methods failed")
        
        # Clean and normalize the extracted text
        cleaned_text = self._clean_extracted_text(raw_text)
        
        # Validate minimum text length
        if len(cleaned_text) < 400:
            raise Exception("Extracted text too short (< 400 chars) - likely corrupted or unreadable")
        
        return cleaned_text
    
    def _extract_with_pymupdf(self, pdf_path: str) -> str:
        """Extract text using PyMuPDF (highest quality)"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Use "text" mode with sorting for best results
                text = page.get_text("text", sort=True)
                if text.strip():
                    text_parts.append(text.strip())
            
            doc.close()
            return "\n".join(text_parts)
        except ImportError:
            raise Exception("PyMuPDF not available")
    
    def _extract_with_pdfminer(self, pdf_path: str) -> str:
        """Extract text using pdfminer.six"""
        try:
            from pdfminer.high_level import extract_text
            return extract_text(pdf_path)
        except ImportError:
            raise Exception("pdfminer.six not available")
    
    def _extract_with_pypdf(self, pdf_path: str) -> str:
        """Extract text using pypdf (fallback)"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            text_parts = []
            
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return "\n".join(text_parts)
        except ImportError:
            raise Exception("pypdf not available")
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        """
        if not text:
            return ""
        
        # Convert line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Collapse multiple newlines to max 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Collapse multiple spaces to single space
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove non-printable characters except tabs, newlines, carriage returns
        text = re.sub(r'[^\x20-\x7E\t\n\r]', '', text)
        
        # Remove lines longer than 2000 chars (likely embedded garbage)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if len(line) <= 2000:
                cleaned_lines.append(line)
            else:
                # Truncate very long lines
                cleaned_lines.append(line[:2000] + "...")
        
        text = '\n'.join(cleaned_lines)
        
        # Remove duplicate paragraphs (occurring more than 2 times)
        paragraphs = text.split('\n\n')
        seen_paragraphs = {}
        deduplicated_paragraphs = []
        
        for para in paragraphs:
            para_stripped = para.strip()
            if para_stripped:
                if para_stripped not in seen_paragraphs:
                    seen_paragraphs[para_stripped] = 1
                    deduplicated_paragraphs.append(para)
                elif seen_paragraphs[para_stripped] < 2:
                    seen_paragraphs[para_stripped] += 1
                    deduplicated_paragraphs.append(para)
                # Skip paragraphs that appear more than 2 times
        
        text = '\n\n'.join(deduplicated_paragraphs)
        
        # Final cleanup
        text = text.strip()
        
        return text
    
    def get_text_preview(self, pdf_path: Path, preview_chars: int = 800) -> str:
        """Get just the preview text from a PDF"""
        _, preview = self.extract_text(pdf_path, preview_chars)
        return preview
