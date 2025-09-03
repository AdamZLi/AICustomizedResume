"""
Resume router for handling PDF upload, viewing, and text extraction
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import FileResponse
from pathlib import Path
import logging
import json

from models import (
    ResumeUploadResponse, ResumeTextResponse, ResumeRewriteRequest, ResumeRewriteResponse,
    EditPlanRequest, EditPlanResponse, ApplyPlanRequest, ApplyPlanResponse, AnnotatedPDFResponse
)
from services.storage import PDFStorageService
from services.resume_parser import ResumeParserService
from services.rewrite_by_sections import ResumeRewriter
from services.pdf_render import PDFRenderer
from services.pdf_annotate import PDFAnnotator
from services.edit_plan import EditPlanService
from services.apply_plan import ApplyPlanService
from services.sections import ResumeSectionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["resume"])

# Initialize services
storage_service = PDFStorageService()
parser_service = ResumeParserService()

@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a PDF resume file
    
    Args:
        file: PDF file to upload
        
    Returns:
        ResumeUploadResponse with resume details and URLs
    """
    try:
        # Save the PDF file
        resume_id, file_path = storage_service.save_pdf(file)
        
        # Extract text preview
        text_excerpt = parser_service.get_text_preview(file_path)
        
        # Build response
        response = ResumeUploadResponse(
            resume_id=resume_id,
            filename=file.filename or "resume.pdf",
            size=file.size or 0,
            preview_chars=800,
            text_excerpt=text_excerpt,
            pdf_url=f"/resume/{resume_id}/pdf",
            text_url=f"/resume/{resume_id}/text"
        )
        
        logger.info(f"Resume uploaded successfully: {resume_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process uploaded file"
        )

@router.get("/{resume_id}/pdf")
async def get_resume_pdf(resume_id: str):
    """
    Get the PDF file for inline viewing
    
    Args:
        resume_id: Unique identifier for the resume
        
    Returns:
        PDF file for inline viewing
    """
    try:
        file_path = storage_service.get_pdf_path(resume_id)
        
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving PDF {resume_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to serve PDF file"
        )

@router.get("/{resume_id}/text", response_model=ResumeTextResponse)
async def get_resume_text(resume_id: str):
    """
    Get the full extracted text from a resume PDF
    
    Args:
        resume_id: Unique identifier for the resume
        
    Returns:
        ResumeTextResponse with the full extracted text
    """
    try:
        file_path = storage_service.get_pdf_path(resume_id)
        
        # Extract full text
        full_text, _ = parser_service.extract_text(file_path)
        
        response = ResumeTextResponse(
            resume_id=resume_id,
            text=full_text
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting text from {resume_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to extract text from PDF"
        )

@router.post("/rewrite", response_model=ResumeRewriteResponse)
async def rewrite_resume(request: ResumeRewriteRequest):
    """Rewrite resume incorporating selected keywords"""
    try:
        # Get the original PDF path
        pdf_path = storage_service.get_pdf_path(request.resume_id)
        if not pdf_path:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Log file details for diagnostics
        import os
        file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
        logger.info(f"Processing resume {request.resume_id}: file_size={file_size} bytes, path={pdf_path}")
        
        # Extract text from the original PDF
        full_text, preview_text = parser_service.extract_text(pdf_path)
        if not full_text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Log extraction results
        from services.tokens import token_manager
        token_count = token_manager.count_tokens(full_text)
        logger.info(f"Resume {request.resume_id}: extracted {len(full_text)} chars, {token_count} tokens")
        logger.info(f"First 300 chars: {full_text[:300]}...")
        logger.info(f"Last 300 chars: {full_text[-300:] if len(full_text) > 300 else full_text}")
        
        # Validate token budget
        if token_count > 50000:  # Safety check
            raise HTTPException(status_code=400, detail=f"Resume too large: {token_count} tokens exceeds safety limit")
        
        # Initialize section-based rewriter
        resume_rewriter = ResumeRewriter()
        
        # Rewrite the resume with keywords using section-based approach
        result = resume_rewriter.rewrite_resume_by_sections(
            full_text=full_text,
            selected_keywords=request.selected_keywords,
            job_title=request.job_title,
            tone=request.tone
        )
        
        updated_text = result["updated_text"]
        change_log = result["change_log"]
        
        # Initialize PDF renderer
        pdf_renderer = PDFRenderer()
        
        # Render updated text to HTML
        updated_html_path = pdf_renderer.render_resume_to_pdf(
            resume_id=request.resume_id,
            resume_text=updated_text
        )
        
        # Optional: Create annotated version with keyword highlights
        pdf_annotator = PDFAnnotator()
        annotated_path = pdf_annotator.annotate_pdf_with_keywords(
            pdf_path=updated_html_path,
            keywords=request.selected_keywords
        )
        
        # Get list of successfully included keywords
        included_keywords = []
        for change in change_log:
            included_keywords.extend(change.keywords_used)
        included_keywords = list(set(included_keywords))  # Remove duplicates
        
        # Log the rewrite operation
        logging.info(f"Resume {request.resume_id} rewritten with {len(included_keywords)} keywords")
        
        return ResumeRewriteResponse(
            resume_id=request.resume_id,
            pdf_url=f"/resume/{request.resume_id}/updated.html",
            updated_text=updated_text,
            original_text=full_text,
            change_log=change_log,
            included_keywords=included_keywords
        )
        
    except Exception as e:
        logging.error(f"Resume rewrite failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Resume rewrite failed: {str(e)}")

@router.get("/{resume_id}/updated.html")
async def get_updated_html(resume_id: str):
    """Get the updated HTML file"""
    try:
        html_path = f"uploads/{resume_id}-updated.html"
        
        # Check if file exists
        import os
        if not os.path.exists(html_path):
            raise HTTPException(status_code=404, detail="Updated HTML not found")
        
        return FileResponse(
            path=html_path,
            media_type="text/html",
            filename=f"resume-{resume_id}-updated.html"
        )
        
    except Exception as e:
        logging.error(f"Failed to serve updated HTML: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve updated HTML")

@router.post("/edit-plan", response_model=EditPlanResponse)
async def generate_edit_plan(request: EditPlanRequest):
    """
    Generate an edit plan for incorporating keywords into a resume section
    
    Args:
        request: EditPlanRequest with resume_id and selected_keywords
        
    Returns:
        EditPlanResponse with the generated edit plan
    """
    try:
        # Get the original PDF path
        pdf_path = storage_service.get_pdf_path(request.resume_id)
        if not pdf_path:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Extract text from the original PDF
        full_text, _ = parser_service.extract_text(pdf_path)
        if not full_text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Initialize services
        section_service = ResumeSectionService()
        edit_plan_service = EditPlanService()
        
        # Get the most relevant section for keyword incorporation
        section_name, section_text = section_service.get_best_section_for_keywords(
            full_text, request.selected_keywords
        )
        
        # Split section into lines
        lines = [line.strip() for line in section_text.split('\n') if line.strip()]
        
        # Generate edit plan
        edit_plan = edit_plan_service.make_edit_plan(
            section_name=section_name,
            lines=lines,
            selected_keywords=request.selected_keywords
        )
        
        return EditPlanResponse(
            resume_id=request.resume_id,
            edit_plan=edit_plan,
            section_name=section_name,
            original_lines=lines
        )
        
    except Exception as e:
        logging.error(f"Edit plan generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Edit plan generation failed: {str(e)}")

@router.post("/apply-plan", response_model=ApplyPlanResponse)
async def apply_edit_plan(request: ApplyPlanRequest):
    """
    Apply an edit plan to update resume text
    
    Args:
        request: ApplyPlanRequest with resume_id, edit_plan, and section_name
        
    Returns:
        ApplyPlanResponse with updated text and change log
    """
    try:
        # Get the original PDF path
        pdf_path = storage_service.get_pdf_path(request.resume_id)
        if not pdf_path:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Extract text from the original PDF
        full_text, _ = parser_service.extract_text(pdf_path)
        if not full_text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Initialize services
        section_service = ResumeSectionService()
        apply_plan_service = ApplyPlanService()
        
        # Get the section text
        section_name, section_text = section_service.get_section_by_name(
            full_text, request.section_name
        )
        
        # Split section into lines
        original_lines = [line.strip() for line in section_text.split('\n') if line.strip()]
        
        # Apply the edit plan
        updated_lines, change_log, applied_keywords = apply_plan_service.apply_edit_plan(
            original_lines=original_lines,
            edit_plan=request.edit_plan.dict()
        )
        
        # Generate diff preview
        diff_preview = apply_plan_service.generate_diff_preview(original_lines, updated_lines)
        
        return ApplyPlanResponse(
            resume_id=request.resume_id,
            updated_lines=updated_lines,
            change_log=change_log,
            applied_keywords=applied_keywords,
            diff_preview=diff_preview
        )
        
    except Exception as e:
        logging.error(f"Edit plan application failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Edit plan application failed: {str(e)}")

@router.post("/{resume_id}/annotate", response_model=AnnotatedPDFResponse)
async def create_annotated_pdf(
    resume_id: str,
    edit_plan: str = Form(...),
    section_name: str = Form(...)
):
    """
    Create an annotated PDF with highlights and notes based on edit plan
    
    Args:
        resume_id: Unique identifier for the resume
        edit_plan: Edit plan to apply for annotation
        section_name: Name of the section being annotated
        
    Returns:
        AnnotatedPDFResponse with URLs to annotated and original PDFs
    """
    try:
        # Parse the edit plan JSON string
        try:
            edit_plan_dict = json.loads(edit_plan)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid edit plan JSON")
        
        # Get the original PDF path
        pdf_path = storage_service.get_pdf_path(resume_id)
        if not pdf_path:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Extract text from the original PDF
        full_text, _ = parser_service.extract_text(pdf_path)
        if not full_text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Initialize services
        section_service = ResumeSectionService()
        pdf_annotator = PDFAnnotator()
        
        # Get the section text
        section_name, section_text = section_service.get_section_by_name(
            full_text, section_name
        )
        
        # Split section into lines
        original_lines = [line.strip() for line in section_text.split('\n') if line.strip()]
        
        # Create annotated PDF
        annotated_path = pdf_annotator.annotate_pdf_with_edits(
            pdf_path=pdf_path,
            edit_plan=edit_plan_dict,
            original_lines=original_lines
        )
        
        # Get annotation summary
        annotation_summary = pdf_annotator.get_annotation_summary(annotated_path, edit_plan_dict)
        
        # Build response
        return AnnotatedPDFResponse(
            resume_id=resume_id,
            annotated_pdf_url=f"/resume/{resume_id}/annotated.pdf",
            annotation_summary=annotation_summary,
            original_pdf_url=f"/resume/{resume_id}/pdf"
        )
        
    except Exception as e:
        logging.error(f"PDF annotation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF annotation failed: {str(e)}")

@router.get("/{resume_id}/annotated.pdf")
async def get_annotated_pdf(resume_id: str):
    """
    Get the annotated PDF file
    
    Args:
        resume_id: Unique identifier for the resume
        
    Returns:
        Annotated PDF file for download
    """
    try:
        # Look for annotated PDF
        annotated_path = f"uploads/{resume_id}-annotated.pdf"
        
        # Check if file exists
        import os
        if not os.path.exists(annotated_path):
            raise HTTPException(status_code=404, detail="Annotated PDF not found")
        
        return FileResponse(
            path=annotated_path,
            media_type="application/pdf",
            filename=f"resume-{resume_id}-annotated.pdf",
            headers={"Content-Disposition": "attachment"}
        )
        
    except Exception as e:
        logging.error(f"Failed to serve annotated PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve annotated PDF")
