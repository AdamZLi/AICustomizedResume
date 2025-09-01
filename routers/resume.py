"""
Resume router for handling PDF upload, viewing, and text extraction
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import FileResponse
from pathlib import Path
import logging

from models import ResumeUploadResponse, ResumeTextResponse, ResumeRewriteRequest, ResumeRewriteResponse
from services.storage import PDFStorageService
from services.resume_parser import ResumeParserService
from services.rewrite_by_sections import ResumeRewriter
from services.pdf_render import PDFRenderer
from services.pdf_annotate import PDFAnnotator

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
