"""
API router for structured resume editing
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
import logging
from typing import List, Optional
import json

from models_structured import (
    StructuredResume, StructuredResumeResponse, SectionUpdateRequest,
    BulletPointUpdateRequest, ResumeExportRequest, KeywordInsertionRequest,
    KeywordInsertionResponse, ResumeParseRequest, ResumeParseResponse,
    SectionType, WorkExperience, Entrepreneurship, Education, AdditionalInfo, Headline
)
from services.structured_parser import StructuredResumeParser
from services.structured_storage import StructuredResumeStorage
from services.resume_parser import ResumeParserService
from services.storage import PDFStorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/structured-resume", tags=["structured-resume"])

# Initialize services
structured_parser = StructuredResumeParser()
structured_storage = StructuredResumeStorage()
pdf_parser = ResumeParserService()
pdf_storage = PDFStorageService()

@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(request: ResumeParseRequest):
    """
    Parse an uploaded resume into structured data
    
    Args:
        request: ResumeParseRequest with resume_id and parsing options
        
    Returns:
        ResumeParseResponse with structured resume data
    """
    try:
        # Get the original PDF path
        pdf_path = pdf_storage.get_pdf_path(request.resume_id)
        
        # Extract text from PDF
        full_text, _ = pdf_parser.extract_text(pdf_path)
        if not full_text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Parse into structured data
        structured_resume = structured_parser.parse_resume(full_text, request.resume_id)
        
        # Save structured data
        success = structured_storage.save_resume(structured_resume)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save structured resume data")
        
        # Generate parse summary
        parse_summary = {
            "total_sections": len(structured_resume.work_experience) + len(structured_resume.education) + 
                            len(structured_resume.entrepreneurship) + len(structured_resume.additional_info),
            "work_experience_count": len(structured_resume.work_experience),
            "education_count": len(structured_resume.education),
            "entrepreneurship_count": len(structured_resume.entrepreneurship),
            "additional_info_count": len(structured_resume.additional_info),
            "total_bullets": len(structured_resume.get_all_bullets()),
            "parsing_method": "enhanced_parser"
        }
        
        return ResumeParseResponse(
            resume_id=request.resume_id,
            structured_resume=structured_resume,
            parse_summary=parse_summary,
            warnings=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Resume parsing failed: {str(e)}")

@router.get("/{resume_id}", response_model=StructuredResumeResponse)
async def get_structured_resume(resume_id: str):
    """
    Get structured resume data
    
    Args:
        resume_id: Resume identifier
        
    Returns:
        StructuredResumeResponse with complete resume data
    """
    try:
        resume = structured_storage.load_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Structured resume not found")
        
        return StructuredResumeResponse(resume=resume)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get structured resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get structured resume: {str(e)}")

@router.put("/{resume_id}/section", response_model=StructuredResumeResponse)
async def update_section(resume_id: str, request: SectionUpdateRequest):
    """
    Update a resume section
    
    Args:
        resume_id: Resume identifier
        request: SectionUpdateRequest with section data
        
    Returns:
        StructuredResumeResponse with updated resume data
    """
    try:
        # Load existing resume
        resume = structured_storage.load_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Update the appropriate section
        if request.section_type == SectionType.WORK_EXPERIENCE:
            # Update or add work experience
            if isinstance(request.section_data, WorkExperience):
                # Find existing entry or add new one
                existing_index = None
                for i, exp in enumerate(resume.work_experience):
                    if exp.id == request.section_data.id:
                        existing_index = i
                        break
                
                if existing_index is not None:
                    resume.work_experience[existing_index] = request.section_data
                else:
                    resume.work_experience.append(request.section_data)
        
        elif request.section_type == SectionType.ENTREPRENEURSHIP:
            # Update or add entrepreneurship
            if isinstance(request.section_data, Entrepreneurship):
                existing_index = None
                for i, ent in enumerate(resume.entrepreneurship):
                    if ent.id == request.section_data.id:
                        existing_index = i
                        break
                
                if existing_index is not None:
                    resume.entrepreneurship[existing_index] = request.section_data
                else:
                    resume.entrepreneurship.append(request.section_data)
        
        elif request.section_type == SectionType.EDUCATION:
            # Update or add education
            if isinstance(request.section_data, Education):
                existing_index = None
                for i, edu in enumerate(resume.education):
                    if edu.id == request.section_data.id:
                        existing_index = i
                        break
                
                if existing_index is not None:
                    resume.education[existing_index] = request.section_data
                else:
                    resume.education.append(request.section_data)
        
        elif request.section_type == SectionType.ADDITIONAL_INFO:
            # Update or add additional info
            if isinstance(request.section_data, AdditionalInfo):
                existing_index = None
                for i, info in enumerate(resume.additional_info):
                    if info.id == request.section_data.id:
                        existing_index = i
                        break
                
                if existing_index is not None:
                    resume.additional_info[existing_index] = request.section_data
                else:
                    resume.additional_info.append(request.section_data)
        
        elif request.section_type == SectionType.HEADLINE:
            # Update headline
            if isinstance(request.section_data, Headline):
                resume.headline = request.section_data
        
        # Save updated resume
        success = structured_storage.save_resume(resume)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save updated resume")
        
        return StructuredResumeResponse(resume=resume)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update section: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update section: {str(e)}")

@router.put("/{resume_id}/bullet", response_model=StructuredResumeResponse)
async def update_bullet_point(resume_id: str, request: BulletPointUpdateRequest):
    """
    Update a bullet point within a section
    
    Args:
        resume_id: Resume identifier
        request: BulletPointUpdateRequest with bullet point data
        
    Returns:
        StructuredResumeResponse with updated resume data
    """
    try:
        # Load existing resume
        resume = structured_storage.load_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Find and update the bullet point
        updated = False
        
        if request.section_type == SectionType.WORK_EXPERIENCE:
            for exp in resume.work_experience:
                if exp.id == request.section_id:
                    for i, bullet in enumerate(exp.bullets):
                        if bullet.id == request.bullet.id:
                            exp.bullets[i] = request.bullet
                            updated = True
                            break
                    break
        
        elif request.section_type == SectionType.ENTREPRENEURSHIP:
            for ent in resume.entrepreneurship:
                if ent.id == request.section_id:
                    for i, bullet in enumerate(ent.bullets):
                        if bullet.id == request.bullet.id:
                            ent.bullets[i] = request.bullet
                            updated = True
                            break
                    break
        
        if not updated:
            raise HTTPException(status_code=404, detail="Bullet point not found")
        
        # Save updated resume
        success = structured_storage.save_resume(resume)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save updated resume")
        
        return StructuredResumeResponse(resume=resume)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update bullet point: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update bullet point: {str(e)}")

@router.delete("/{resume_id}/section/{section_id}")
async def delete_section(resume_id: str, section_id: str, section_type: str):
    """
    Delete a section from the resume
    
    Args:
        resume_id: Resume identifier
        section_id: Section identifier
        section_type: Type of section to delete
        
    Returns:
        Success message
    """
    try:
        # Load existing resume
        resume = structured_storage.load_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Delete the section
        deleted = False
        
        if section_type == SectionType.WORK_EXPERIENCE:
            resume.work_experience = [exp for exp in resume.work_experience if exp.id != section_id]
            deleted = True
        
        elif section_type == SectionType.ENTREPRENEURSHIP:
            resume.entrepreneurship = [ent for ent in resume.entrepreneurship if ent.id != section_id]
            deleted = True
        
        elif section_type == SectionType.EDUCATION:
            resume.education = [edu for edu in resume.education if edu.id != section_id]
            deleted = True
        
        elif section_type == SectionType.ADDITIONAL_INFO:
            resume.additional_info = [info for info in resume.additional_info if info.id != section_id]
            deleted = True
        
        if not deleted:
            raise HTTPException(status_code=400, detail="Invalid section type")
        
        # Save updated resume
        success = structured_storage.save_resume(resume)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save updated resume")
        
        return {"message": "Section deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete section: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete section: {str(e)}")

@router.post("/{resume_id}/export")
async def export_resume(resume_id: str, request: ResumeExportRequest):
    """
    Export structured resume to various formats
    
    Args:
        resume_id: Resume identifier
        request: ResumeExportRequest with export options
        
    Returns:
        FileResponse with exported resume
    """
    try:
        # Load structured resume
        resume = structured_storage.load_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Generate export based on format
        if request.format.lower() == "html":
            # Generate HTML resume
            html_content = _generate_html_resume(resume)
            
            # Save HTML file
            html_path = f"exports/{resume_id}-resume.html"
            Path("exports").mkdir(exist_ok=True)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return FileResponse(
                path=html_path,
                media_type="text/html",
                filename=f"resume-{resume_id}.html"
            )
        
        elif request.format.lower() == "pdf":
            # Generate HTML first, then convert to PDF
            html_content = _generate_html_resume(resume)
            
            # For now, return HTML (PDF conversion would require additional libraries)
            html_path = f"exports/{resume_id}-resume.html"
            Path("exports").mkdir(exist_ok=True)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return FileResponse(
                path=html_path,
                media_type="text/html",
                filename=f"resume-{resume_id}.html"
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export resume: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export resume: {str(e)}")

@router.post("/{resume_id}/keyword-insertions", response_model=KeywordInsertionResponse)
async def get_keyword_insertions(resume_id: str, request: KeywordInsertionRequest):
    """
    Get keyword insertion suggestions for resume bullets
    
    Args:
        resume_id: Resume identifier
        request: KeywordInsertionRequest with keywords and options
        
    Returns:
        KeywordInsertionResponse with insertion suggestions
    """
    try:
        # Load structured resume
        resume = structured_storage.load_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Get all bullet points
        all_bullets = resume.get_all_bullets()
        
        # Generate insertion suggestions (simplified version)
        suggestions = []
        skipped_keywords = []
        
        for bullet in all_bullets:
            if not bullet.is_active:
                continue
            
            # Simple keyword matching and insertion logic
            for keyword in request.keywords:
                if keyword.lower() not in bullet.text.lower():
                    # Generate insertion suggestion
                    suggestion = {
                        "bullet_id": bullet.id,
                        "insertion_text": f"({keyword})",
                        "insertion_type": "parenthetical",
                        "keywords_used": [keyword],
                        "confidence": 0.8
                    }
                    suggestions.append(suggestion)
        
        return KeywordInsertionResponse(
            suggestions=suggestions,
            skipped_keywords=skipped_keywords
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get keyword insertions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get keyword insertions: {str(e)}")

def _generate_html_resume(resume: StructuredResume) -> str:
    """Generate HTML resume from structured data"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{resume.headline.name} - Resume</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid #333;
                padding-bottom: 20px;
            }}
            .name {{
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .title {{
                font-size: 18px;
                color: #666;
                margin-bottom: 10px;
            }}
            .contact {{
                font-size: 14px;
                color: #666;
            }}
            .section {{
                margin-bottom: 25px;
            }}
            .section-title {{
                font-size: 18px;
                font-weight: bold;
                text-transform: uppercase;
                border-bottom: 1px solid #333;
                margin-bottom: 15px;
                padding-bottom: 5px;
            }}
            .experience-item {{
                margin-bottom: 20px;
            }}
            .experience-header {{
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .experience-dates {{
                font-style: italic;
                color: #666;
                margin-bottom: 10px;
            }}
            .bullet-points {{
                margin-left: 20px;
            }}
            .bullet-point {{
                margin-bottom: 5px;
            }}
            .education-item {{
                margin-bottom: 15px;
            }}
            .additional-info {{
                margin-bottom: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="name">{resume.headline.name}</div>
            <div class="title">{resume.headline.title}</div>
            <div class="contact">
                {_format_contact_info(resume.headline.contact)}
            </div>
        </div>
        
        {_format_work_experience(resume.work_experience)}
        {_format_entrepreneurship(resume.entrepreneurship)}
        {_format_education(resume.education)}
        {_format_additional_info(resume.additional_info)}
    </body>
    </html>
    """
    return html

def _format_contact_info(contact: dict) -> str:
    """Format contact information"""
    parts = []
    if 'email' in contact:
        parts.append(contact['email'])
    if 'phone' in contact:
        parts.append(contact['phone'])
    if 'location' in contact:
        parts.append(contact['location'])
    if 'linkedin' in contact:
        parts.append(contact['linkedin'])
    return ' | '.join(parts)

def _format_work_experience(experiences: List[WorkExperience]) -> str:
    """Format work experience section"""
    if not experiences:
        return ""
    
    html = '<div class="section"><div class="section-title">Professional Experience</div>'
    
    for exp in experiences:
        html += f'''
        <div class="experience-item">
            <div class="experience-header">{exp.title} at {exp.company}</div>
            <div class="experience-dates">{_format_dates(exp.start_date, exp.end_date, exp.is_current)}</div>
            <div class="bullet-points">
        '''
        
        for bullet in exp.bullets:
            if bullet.is_active:
                html += f'<div class="bullet-point">• {bullet.text}</div>'
        
        html += '</div></div>'
    
    html += '</div>'
    return html

def _format_entrepreneurship(entrepreneurships: List[Entrepreneurship]) -> str:
    """Format entrepreneurship section"""
    if not entrepreneurships:
        return ""
    
    html = '<div class="section"><div class="section-title">Entrepreneurship</div>'
    
    for ent in entrepreneurships:
        html += f'''
        <div class="experience-item">
            <div class="experience-header">{ent.title} at {ent.company}</div>
            <div class="experience-dates">{_format_dates(ent.start_date, ent.end_date, ent.is_current)}</div>
            <div class="bullet-points">
        '''
        
        for bullet in ent.bullets:
            if bullet.is_active:
                html += f'<div class="bullet-point">• {bullet.text}</div>'
        
        html += '</div></div>'
    
    html += '</div>'
    return html

def _format_education(educations: List[Education]) -> str:
    """Format education section"""
    if not educations:
        return ""
    
    html = '<div class="section"><div class="section-title">Education</div>'
    
    for edu in educations:
        html += f'''
        <div class="education-item">
            <div class="experience-header">{edu.degree} - {edu.institution}</div>
            <div class="experience-dates">{_format_dates(edu.start_date, edu.end_date, False)}</div>
        '''
        
        if edu.gpa:
            html += f'<div>GPA: {edu.gpa}</div>'
        
        if edu.extras:
            html += '<div>'
            for extra in edu.extras:
                html += f'<div>• {extra}</div>'
            html += '</div>'
        
        html += '</div>'
    
    html += '</div>'
    return html

def _format_additional_info(additional_infos: List[AdditionalInfo]) -> str:
    """Format additional information section"""
    if not additional_infos:
        return ""
    
    html = '<div class="section"><div class="section-title">Additional Information</div>'
    
    for info in additional_infos:
        html += f'<div class="additional-info"><strong>{info.category}:</strong> '
        html += ', '.join(info.items)
        html += '</div>'
    
    html += '</div>'
    return html

def _format_dates(start_date: Optional[str], end_date: Optional[str], is_current: bool) -> str:
    """Format date range"""
    if not start_date:
        return ""
    
    if is_current or end_date in ['Present', 'Current', 'Now']:
        return f"{start_date} - Present"
    elif end_date:
        return f"{start_date} - {end_date}"
    else:
        return start_date
