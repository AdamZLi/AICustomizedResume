import os
from pathlib import Path

class PDFRenderer:
    def __init__(self):
        self.uploads_dir = Path("uploads")
        self.uploads_dir.mkdir(exist_ok=True)
    
    def render_resume_to_pdf(self, resume_id: str, resume_text: str) -> str:
        """
        For now, save as HTML file instead of PDF to avoid dependency issues
        Returns: path to the generated HTML file
        """
        
        # Create HTML content with professional styling
        html_content = self._create_resume_html(resume_text)
        
        # Generate HTML filename
        html_filename = f"{resume_id}-updated.html"
        html_path = self.uploads_dir / html_filename
        
        try:
            # Save as HTML file
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return str(html_path)
            
        except Exception as e:
            raise Exception(f"HTML generation failed: {str(e)}")
    
    def _create_resume_html(self, resume_text: str) -> str:
        """
        Convert plain text resume to structured HTML
        This is a basic implementation - you can enhance it based on your needs
        """
        
        # Split text into lines and process
        lines = resume_text.strip().split('\n')
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<meta charset="UTF-8">',
            '<title>Updated Resume</title>',
            '<style>',
            'body { font-family: "Times New Roman", Times, serif; font-size: 11pt; line-height: 1.4; color: #333; margin: 0; padding: 0.75in; }',
            '.resume-header { text-align: center; margin-bottom: 1.5em; border-bottom: 2px solid #333; padding-bottom: 1em; }',
            '.name { font-size: 24pt; font-weight: bold; margin-bottom: 0.5em; }',
            '.contact-info { font-size: 10pt; margin-bottom: 0.5em; }',
            '.section { margin-bottom: 1.5em; }',
            '.section-title { font-size: 14pt; font-weight: bold; text-transform: uppercase; border-bottom: 1px solid #333; margin-bottom: 0.75em; padding-bottom: 0.25em; }',
            '.job-entry { margin-bottom: 1em; }',
            '.job-title { font-weight: bold; font-size: 12pt; }',
            '.company { font-weight: bold; font-style: italic; }',
            '.dates { float: right; font-style: italic; }',
            '.job-description { margin-top: 0.5em; margin-left: 1em; }',
            '.job-description ul { margin: 0.25em 0; padding-left: 1.5em; }',
            '.job-description li { margin-bottom: 0.25em; }',
            '.skills-section ul { list-style: none; padding: 0; margin: 0; }',
            '.skills-section li { display: inline-block; margin-right: 1em; margin-bottom: 0.5em; padding: 0.25em 0.5em; background-color: #f5f5f5; border-radius: 3px; }',
            '.clearfix::after { content: ""; display: table; clear: both; }',
            '</style>',
            '</head>',
            '<body>'
        ]
        
        current_section = None
        in_job_description = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers (common resume sections)
            lower_line = line.lower()
            if any(keyword in lower_line for keyword in ['summary', 'objective', 'profile']):
                current_section = 'summary'
                html_parts.append('<div class="section">')
                html_parts.append('<div class="section-title">Professional Summary</div>')
                html_parts.append('<p>' + line + '</p>')
                html_parts.append('</div>')
                
            elif any(keyword in lower_line for keyword in ['experience', 'work history', 'employment']):
                current_section = 'experience'
                html_parts.append('<div class="section">')
                html_parts.append('<div class="section-title">Professional Experience</div>')
                
            elif any(keyword in lower_line for keyword in ['education', 'academic']):
                current_section = 'education'
                html_parts.append('<div class="section">')
                html_parts.append('<div class="section-title">Education</div>')
                html_parts.append('<p>' + line + '</p>')
                html_parts.append('</div>')
                
            elif any(keyword in lower_line for keyword in ['skills', 'technical skills', 'competencies']):
                current_section = 'skills'
                html_parts.append('<div class="section">')
                html_parts.append('<div class="section-title">Skills</div>')
                html_parts.append('<ul class="skills-section">')
                
            elif current_section == 'experience':
                # Handle experience section formatting
                if line and not line.startswith('•') and not line.startswith('-'):
                    # This might be a job title/company line
                    if in_job_description:
                        html_parts.append('</div>')  # Close previous job description
                        in_job_description = False
                    
                    html_parts.append('<div class="job-entry">')
                    html_parts.append('<div class="job-title">' + line + '</div>')
                    in_job_description = True
                    
                elif line.startswith('•') or line.startswith('-'):
                    # This is a bullet point
                    if not in_job_description:
                        html_parts.append('<div class="job-entry">')
                        html_parts.append('<div class="job-description">')
                        in_job_description = True
                    
                    html_parts.append('<ul>')
                    html_parts.append('<li>' + line[1:].strip() + '</li>')
                    html_parts.append('</ul>')
                    
                else:
                    # Regular text line
                    if in_job_description:
                        html_parts.append('<p>' + line + '</p>')
                    else:
                        html_parts.append('<p>' + line + '</p>')
                        
            elif current_section == 'skills':
                # Handle skills section
                if line and not line.startswith('•') and not line.startswith('-'):
                    html_parts.append('<li>' + line + '</li>')
                    
            else:
                # Default handling for other lines
                if current_section == 'experience' and in_job_description:
                    html_parts.append('<p>' + line + '</p>')
                elif current_section == 'skills':
                    html_parts.append('<li>' + line + '</li>')
                else:
                    html_parts.append('<p>' + line + '</p>')
        
        # Close any open sections
        if current_section == 'experience' and in_job_description:
            html_parts.append('</div>')  # Close job description
        if current_section == 'skills':
            html_parts.append('</ul>')
            html_parts.append('</div>')  # Close skills section
        
        html_parts.extend(['</body>', '</html>'])
        
        return '\n'.join(html_parts)
