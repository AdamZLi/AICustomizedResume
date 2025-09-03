"""
PDF Annotation Service for Resume Tailoring
Adds highlights and sticky notes to PDFs based on edit plans
"""
import logging
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class PDFAnnotator:
    def __init__(self):
        self.uploads_dir = Path("uploads")
        
    def annotate_pdf_with_edits(
        self, 
        pdf_path: str, 
        edit_plan: Dict[str, Any],
        original_lines: List[str]
    ) -> str:
        """
        Annotate a PDF with highlights and sticky notes based on edit plan
        
        Args:
            pdf_path: Path to the original PDF
            edit_plan: Edit plan from EditPlanService
            original_lines: Original text lines for reference
            
        Returns:
            Path to the annotated PDF
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Open the PDF
            doc = fitz.open(pdf_path)
            
            # Process each edit
            edits = edit_plan.get("edits", [])
            for edit in edits:
                self._apply_edit_annotation(doc, edit, original_lines)
            
            # Generate output path
            pdf_name = Path(pdf_path).stem
            annotated_path = self.uploads_dir / f"{pdf_name}-annotated.pdf"
            
            # Save the annotated PDF
            doc.save(str(annotated_path))
            doc.close()
            
            logger.info(f"Successfully annotated PDF: {annotated_path}")
            return str(annotated_path)
            
        except Exception as e:
            logger.error(f"Error annotating PDF: {str(e)}")
            # Return original path on error
            return pdf_path
    
    def _apply_edit_annotation(
        self, 
        doc: fitz.Document, 
        edit: Dict[str, Any], 
        original_lines: List[str]
    ):
        """
        Apply a single edit annotation to the PDF
        
        Args:
            doc: PyMuPDF document object
            edit: Single edit from the plan
            original_lines: Original text lines
        """
        try:
            line_num = edit["line"]
            if line_num < 1 or line_num > len(original_lines):
                return
            
            original_line = original_lines[line_num - 1]
            strategy = edit["strategy"]
            insertion = edit["insertion"]
            
            # Search for the text in the PDF
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Search for the original line text
                text_instances = page.search_for(original_line)
                
                if text_instances:
                    # Found the text, add annotation
                    for rect in text_instances:
                        self._add_highlight_and_note(
                            page, 
                            rect, 
                            strategy, 
                            insertion, 
                            edit["keywords_used"]
                        )
                    return
                
                # If exact match not found, try partial match
                words = original_line.split()
                if len(words) > 3:
                    # Search for a phrase (first 3+ words)
                    phrase = " ".join(words[:3])
                    text_instances = page.search_for(phrase)
                    
                    if text_instances:
                        for rect in text_instances:
                            self._add_highlight_and_note(
                                page, 
                                rect, 
                                strategy, 
                                insertion, 
                                edit["keywords_used"]
                            )
                        return
            
            # If text not found on any page, add a note at the top of first page
            logger.warning(f"Text for line {line_num} not found in PDF, adding note to first page")
            first_page = doc[0]
            self._add_fallback_note(
                first_page, 
                line_num, 
                strategy, 
                insertion, 
                edit["keywords_used"]
            )
            
        except Exception as e:
            logger.error(f"Error applying edit annotation: {str(e)}")
    
    def _add_highlight_and_note(
        self, 
        page: fitz.Page, 
        rect: fitz.Rect, 
        strategy: str, 
        insertion: str, 
        keywords_used: List[str]
    ):
        """
        Add a highlight and sticky note to the page
        
        Args:
            page: PyMuPDF page object
            rect: Rectangle where to place the annotation
            strategy: Edit strategy used
            insertion: Text that was inserted
            keywords_used: Keywords incorporated
        """
        try:
            # Add highlight
            highlight = page.add_highlight_annot(rect)
            highlight.set_colors(stroke=(1, 1, 0))  # Yellow highlight
            highlight.set_opacity(0.3)
            highlight.update()
            
            # Add sticky note
            note_text = self._format_note_text(strategy, insertion, keywords_used)
            
            # Position note above the highlight
            note_rect = fitz.Rect(
                rect.x0, 
                rect.y0 - 30, 
                rect.x0 + 200, 
                rect.y0
            )
            
            note = page.add_text_annot(note_rect.tl, note_text)
            note.set_colors(stroke=(0, 0, 0))  # Black text
            note.set_opacity(1.0)
            note.update()
            
        except Exception as e:
            logger.error(f"Error adding highlight and note: {str(e)}")
    
    def _add_fallback_note(
        self, 
        page: fitz.Page, 
        line_num: int, 
        strategy: str, 
        insertion: str, 
        keywords_used: List[str]
    ):
        """
        Add a fallback note when text location can't be determined
        
        Args:
            page: PyMuPDF page object
            line_num: Line number from edit plan
            strategy: Edit strategy used
            insertion: Text that was inserted
            keywords_used: Keywords incorporated
        """
        try:
            note_text = f"Line {line_num}: {self._format_note_text(strategy, insertion, keywords_used)}"
            
            # Position note at top-left of page
            note_rect = fitz.Rect(50, 50, 250, 80)
            
            note = page.add_text_annot(note_rect.tl, note_text)
            note.set_colors(stroke=(1, 0, 0))  # Red text for fallback notes
            note.set_opacity(1.0)
            note.update()
            
        except Exception as e:
            logger.error(f"Error adding fallback note: {str(e)}")
    
    def _format_note_text(self, strategy: str, insertion: str, keywords_used: List[str]) -> str:
        """
        Format the text for sticky notes
        
        Args:
            strategy: Edit strategy used
            insertion: Text that was inserted
            keywords_used: Keywords incorporated
            
        Returns:
            Formatted note text
        """
        strategy_labels = {
            "modifier": "Modifier",
            "parenthetical": "Parenthetical",
            "tail": "Tail"
        }
        
        strategy_label = strategy_labels.get(strategy, strategy.title())
        keywords_text = ", ".join(keywords_used[:3])  # Limit to first 3 keywords
        
        if strategy == "tail":
            return f"Tail: {insertion}\nKeywords: {keywords_text}"
        else:
            return f"{strategy_label}: {insertion}\nKeywords: {keywords_text}"
    
    def get_annotation_summary(self, pdf_path: str, edit_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of annotations applied to the PDF
        
        Args:
            pdf_path: Path to the PDF
            edit_plan: Edit plan that was applied
            
        Returns:
            Summary of annotations
        """
        try:
            edits = edit_plan.get("edits", [])
            
            summary = {
                "total_edits": len(edits),
                "strategies_used": {},
                "keywords_incorporated": [],
                "annotation_status": "completed"
            }
            
            # Count strategies
            for edit in edits:
                strategy = edit["strategy"]
                summary["strategies_used"][strategy] = summary["strategies_used"].get(strategy, 0) + 1
                
                # Collect keywords
                summary["keywords_incorporated"].extend(edit["keywords_used"])
            
            # Remove duplicate keywords
            summary["keywords_incorporated"] = list(set(summary["keywords_incorporated"]))
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating annotation summary: {str(e)}")
            return {
                "total_edits": 0,
                "strategies_used": {},
                "keywords_incorporated": [],
                "annotation_status": "error"
            }
