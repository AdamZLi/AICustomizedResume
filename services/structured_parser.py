"""
Enhanced resume parser for structured data extraction
"""
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import uuid

from models_structured import (
    StructuredResume, Headline, WorkExperience, Entrepreneurship, 
    Education, AdditionalInfo, BulletPoint, SectionType
)

logger = logging.getLogger(__name__)

class StructuredResumeParser:
    """Parser for extracting structured data from resume files"""
    
    def __init__(self):
        # Section detection patterns (case-insensitive)
        self.section_patterns = {
            SectionType.WORK_EXPERIENCE: [
                r'^work(ing)?\s+experience',
                r'^professional\s+experience',
                r'^experience',
                r'^employment',
                r'^career\s+history'
            ],
            SectionType.ENTREPRENEURSHIP: [
                r'^entrepreneurship',
                r'^startup\s+experience',
                r'^founding\s+experience',
                r'^business\s+experience',
                r'^ventures'
            ],
            SectionType.EDUCATION: [
                r'^education',
                r'^academic\s+background',
                r'^qualifications',
                r'^degrees'
            ],
            SectionType.ADDITIONAL_INFO: [
                r'^additional\s+information',
                r'^other\s+information',
                r'^miscellaneous',
                r'^additional'
            ],
            SectionType.SKILLS: [
                r'^skills',
                r'^technical\s+skills',
                r'^core\s+competencies',
                r'^expertise',
                r'^technologies'
            ]
        }
        
        # Bullet point patterns
        self.bullet_patterns = [
            r'^[•\-\–\*]\s+(.+)',  # Standard bullet points
            r'^\d+\.\s+(.+)',      # Numbered lists
            r'^[a-zA-Z]\.\s+(.+)', # Lettered lists
            r'^>\s+(.+)',          # Arrow bullets
            r'^→\s+(.+)',          # Right arrow
        ]
        
        # Date patterns
        self.date_patterns = [
            r'(\w{3,9}\s+\d{4})\s*[-–—]\s*(\w{3,9}\s+\d{4}|present|current|now)',
            r'(\d{1,2}/\d{4})\s*[-–—]\s*(\d{1,2}/\d{4}|present|current|now)',
            r'(\d{4})\s*[-–—]\s*(\d{4}|present|current|now)',
        ]
    
    def parse_resume(self, text: str, filename: str = "resume.pdf") -> StructuredResume:
        """
        Parse resume text into structured data
        
        Args:
            text: Raw resume text
            filename: Original filename
            
        Returns:
            StructuredResume object
        """
        try:
            # Clean and normalize text
            cleaned_text = self._clean_text(text)
            
            # Extract sections
            sections = self._extract_sections(cleaned_text)
            
            # Parse headline
            headline = self._parse_headline(cleaned_text)
            
            # Parse work experience
            work_experience = self._parse_work_experience(sections.get(SectionType.WORK_EXPERIENCE, []))
            
            # Parse entrepreneurship
            entrepreneurship = self._parse_entrepreneurship(sections.get(SectionType.ENTREPRENEURSHIP, []))
            
            # Parse education
            education = self._parse_education(sections.get(SectionType.EDUCATION, []))
            
            # Parse additional info
            additional_info = self._parse_additional_info(sections.get(SectionType.ADDITIONAL_INFO, []))
            
            # Parse skills if found
            skills_section = sections.get(SectionType.SKILLS, [])
            if skills_section:
                skills_info = AdditionalInfo(
                    id=str(uuid.uuid4()),
                    category="Skills",
                    items=self._extract_skills_items(skills_section),
                    order=len(additional_info)
                )
                additional_info.append(skills_info)
            
            # Create structured resume
            resume = StructuredResume(
                id=str(uuid.uuid4()),
                original_filename=filename,
                headline=headline,
                work_experience=work_experience,
                entrepreneurship=entrepreneurship,
                education=education,
                additional_info=additional_info
            )
            
            logger.info(f"Successfully parsed resume with {len(work_experience)} work experiences, {len(education)} education entries")
            return resume
            
        except Exception as e:
            logger.error(f"Failed to parse resume: {e}")
            raise Exception(f"Resume parsing failed: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize resume text"""
        # Remove non-printable characters except newlines
        text = re.sub(r'[^\x20-\x7E\n]', '', text)
        
        # Normalize bullet points
        text = re.sub(r'[•\–\*]', '•', text)
        
        # Clean up excessive whitespace but preserve line structure
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove excessive spaces within each line
            cleaned_line = re.sub(r'\s+', ' ', line.strip())
            if cleaned_line:  # Only add non-empty lines
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_sections(self, text: str) -> Dict[SectionType, List[str]]:
        """Extract sections from resume text"""
        sections = {}
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line is a section header
            section_type = self._detect_section_header(line)
            
            if section_type:
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = current_content
                
                # Start new section
                current_section = section_type
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = current_content
        
        # Put unmatched content in additional info
        if not sections:
            sections[SectionType.ADDITIONAL_INFO] = lines
        
        return sections
    
    def _detect_section_header(self, line: str) -> Optional[SectionType]:
        """Detect if a line is a section header"""
        line_lower = line.lower().strip()
        
        for section_type, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.match(pattern, line_lower):
                    return section_type
        
        return None
    
    def _parse_headline(self, text: str) -> Headline:
        """Parse headline section (name, title, contact info)"""
        print("DEBUG: _parse_headline called with updated code")
        lines = text.split('\n')
        
        # Extract name (usually first non-empty line)
        name = ""
        title = ""
        contact = {}
        
        for line in lines[:10]:  # Look in first 10 lines
            line = line.strip()
            if not line:
                continue
            
            # Check if this looks like a name (title case, may have parentheses or middle names)
            if not name and re.match(r'^[A-Z][a-z]+(\s*\([^)]+\))?\s+[A-Z][a-z]+', line):
                # Extract just the name part (before any contact info)
                name_match = re.match(r'^([A-Z][a-z]+(?:\s*\([^)]+\))?\s+[A-Z][a-z]+)', line)
                if name_match:
                    name = name_match.group(1)
            
            # Check for contact info - handle combined contact lines
            if '@' in line or '|' in line:
                # Split by | and extract individual contact elements
                parts = line.split('|')
                for part in parts:
                    part = part.strip()
                    if '@' in part and not contact.get('email'):
                        contact['email'] = part
                    elif re.match(r'^\+?[\d\s\-\(\)]+$', part) and len(part.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) >= 10:
                        contact['phone'] = part
                    elif 'linkedin' in part.lower() and not contact.get('linkedin'):
                        contact['linkedin'] = part
                    elif 'medium' in part.lower() and not contact.get('medium'):
                        contact['medium'] = part
            elif re.match(r'^\+?[\d\s\-\(\)]+$', line) and len(line.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) >= 10:
                contact['phone'] = line
            elif 'linkedin.com' in line.lower():
                contact['linkedin'] = line
            elif not title and len(line) < 150 and not any(char in line for char in ['•', ':', '|']) and not re.match(r'^[A-Z\s]+$', line) and not line.startswith('-'):
                title = line
        
        return Headline(
            name=name or "Your Name",
            title=title or "Professional Title",
            contact=contact
        )
    
    def _parse_work_experience(self, section_lines: List[str]) -> List[WorkExperience]:
        """Parse work experience section"""
        experiences = []
        current_exp = None
        order = 0
        
        for line in section_lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a new experience entry
            if self._is_experience_header(line):
                # Save previous experience
                if current_exp:
                    experiences.append(current_exp)
                
                # Parse new experience
                current_exp = self._parse_experience_entry(line, order)
                order += 1
            elif current_exp and self._is_bullet_point(line):
                # Add bullet point
                bullet_text = self._extract_bullet_text(line)
                if bullet_text:
                    bullet = BulletPoint(
                        id=str(uuid.uuid4()),
                        text=bullet_text,
                        order=len(current_exp.bullets)
                    )
                    current_exp.bullets.append(bullet)
        
        # Add last experience
        if current_exp:
            experiences.append(current_exp)
        
        return experiences
    
    def _parse_entrepreneurship(self, section_lines: List[str]) -> List[Entrepreneurship]:
        """Parse entrepreneurship section (same structure as work experience)"""
        # Reuse work experience parsing logic
        work_experiences = self._parse_work_experience(section_lines)
        
        # Convert to entrepreneurship entries
        entrepreneurship = []
        for exp in work_experiences:
            ent = Entrepreneurship(
                id=exp.id,
                company=exp.company,
                title=exp.title,
                location=exp.location,
                start_date=exp.start_date,
                end_date=exp.end_date,
                is_current=exp.is_current,
                bullets=exp.bullets,
                order=exp.order
            )
            entrepreneurship.append(ent)
        
        return entrepreneurship
    
    def _parse_education(self, section_lines: List[str]) -> List[Education]:
        """Parse education section"""
        education = []
        current_edu = None
        order = 0
        
        for line in section_lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a new education entry
            if self._is_education_header(line):
                # Save previous education
                if current_edu:
                    education.append(current_edu)
                
                # Parse new education
                current_edu = self._parse_education_entry(line, order)
                order += 1
            elif current_edu and not self._is_bullet_point(line):
                # Add extra information
                current_edu.extras.append(line)
        
        # Add last education
        if current_edu:
            education.append(current_edu)
        
        return education
    
    def _parse_additional_info(self, section_lines: List[str]) -> List[AdditionalInfo]:
        """Parse additional information section"""
        additional_info = []
        current_category = None
        current_items = []
        order = 0
        
        for line in section_lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a category header
            if line.endswith(':') and len(line) < 50:
                # Save previous category
                if current_category and current_items:
                    info = AdditionalInfo(
                        id=str(uuid.uuid4()),
                        category=current_category,
                        items=current_items,
                        order=order
                    )
                    additional_info.append(info)
                    order += 1
                
                # Start new category
                current_category = line[:-1]  # Remove colon
                current_items = []
            elif current_category:
                # Add item to current category
                if self._is_bullet_point(line):
                    item_text = self._extract_bullet_text(line)
                    if item_text:
                        current_items.append(item_text)
                else:
                    current_items.append(line)
        
        # Save last category
        if current_category and current_items:
            info = AdditionalInfo(
                id=str(uuid.uuid4()),
                category=current_category,
                items=current_items,
                order=order
            )
            additional_info.append(info)
        
        return additional_info
    
    def _is_experience_header(self, line: str) -> bool:
        """Check if line is an experience entry header"""
        # Look for company name patterns
        if len(line) > 100:  # Too long for a header
            return False
        
        # Check for date patterns
        has_dates = any(re.search(pattern, line, re.IGNORECASE) for pattern in self.date_patterns)
        
        # Check for common experience patterns
        experience_indicators = [
            r'at\s+',  # "Software Engineer at Google"
            r',\s+',   # "Google, Software Engineer"
            r'\s+-\s+', # "Google - Software Engineer"
        ]
        
        has_indicators = any(re.search(pattern, line, re.IGNORECASE) for pattern in experience_indicators)
        
        return has_dates or has_indicators
    
    def _is_education_header(self, line: str) -> bool:
        """Check if line is an education entry header"""
        # Look for degree patterns
        degree_patterns = [
            r'bachelor',
            r'master',
            r'phd',
            r'doctorate',
            r'associate',
            r'certificate',
            r'diploma',
            r'university',
            r'college',
            r'school'
        ]
        
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in degree_patterns)
    
    def _is_bullet_point(self, line: str) -> bool:
        """Check if line is a bullet point"""
        return any(re.match(pattern, line) for pattern in self.bullet_patterns)
    
    def _extract_bullet_text(self, line: str) -> str:
        """Extract text from bullet point line"""
        for pattern in self.bullet_patterns:
            match = re.match(pattern, line)
            if match:
                return match.group(1).strip()
        return line.strip()
    
    def _parse_experience_entry(self, line: str, order: int) -> WorkExperience:
        """Parse a single experience entry"""
        # Extract dates
        dates = self._extract_dates(line)
        start_date, end_date, is_current = dates if dates else (None, None, False)
        
        # Extract company and title
        company, title = self._extract_company_title(line)
        
        return WorkExperience(
            id=str(uuid.uuid4()),
            company=company,
            title=title,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            order=order
        )
    
    def _parse_education_entry(self, line: str, order: int) -> Education:
        """Parse a single education entry"""
        # Extract dates
        dates = self._extract_dates(line)
        start_date, end_date, _ = dates if dates else (None, None, False)
        
        # Extract institution and degree
        institution, degree = self._extract_institution_degree(line)
        
        return Education(
            id=str(uuid.uuid4()),
            institution=institution,
            degree=degree,
            start_date=start_date,
            end_date=end_date,
            order=order
        )
    
    def _extract_dates(self, line: str) -> Optional[Tuple[str, str, bool]]:
        """Extract start and end dates from a line"""
        for pattern in self.date_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                start_date = match.group(1).strip()
                end_date = match.group(2).strip().lower()
                
                is_current = end_date in ['present', 'current', 'now']
                
                return start_date, end_date, is_current
        
        return None
    
    def _extract_company_title(self, line: str) -> Tuple[str, str]:
        """Extract company and title from experience line"""
        # Remove dates first
        line_no_dates = line
        for pattern in self.date_patterns:
            line_no_dates = re.sub(pattern, '', line_no_dates, flags=re.IGNORECASE)
        
        # Common patterns
        if ' at ' in line_no_dates.lower():
            parts = line_no_dates.split(' at ', 1)
            title = parts[0].strip()
            company = parts[1].strip()
        elif ' - ' in line_no_dates:
            parts = line_no_dates.split(' - ', 1)
            company = parts[0].strip()
            title = parts[1].strip()
        elif ', ' in line_no_dates:
            parts = line_no_dates.split(', ', 1)
            company = parts[0].strip()
            title = parts[1].strip()
        else:
            # Fallback: assume first part is company, rest is title
            words = line_no_dates.split()
            if len(words) > 2:
                company = words[0]
                title = ' '.join(words[1:])
            else:
                company = line_no_dates
                title = "Position"
        
        return company, title
    
    def _extract_institution_degree(self, line: str) -> Tuple[str, str]:
        """Extract institution and degree from education line"""
        # Remove dates first
        line_no_dates = line
        for pattern in self.date_patterns:
            line_no_dates = re.sub(pattern, '', line_no_dates, flags=re.IGNORECASE)
        
        # Common patterns
        if ', ' in line_no_dates:
            parts = line_no_dates.split(', ', 1)
            institution = parts[0].strip()
            degree = parts[1].strip()
        else:
            # Fallback: assume first part is institution, rest is degree
            words = line_no_dates.split()
            if len(words) > 2:
                institution = words[0]
                degree = ' '.join(words[1:])
            else:
                institution = line_no_dates
                degree = "Degree"
        
        return institution, degree
    
    def _extract_skills_items(self, section_lines: List[str]) -> List[str]:
        """Extract skills items from skills section"""
        items = []
        for line in section_lines:
            line = line.strip()
            if not line:
                continue
            
            # Split by common separators
            if ',' in line:
                skills = [skill.strip() for skill in line.split(',')]
                items.extend(skills)
            elif '|' in line:
                skills = [skill.strip() for skill in line.split('|')]
                items.extend(skills)
            elif self._is_bullet_point(line):
                skill = self._extract_bullet_text(line)
                if skill:
                    items.append(skill)
            else:
                items.append(line)
        
        return items
