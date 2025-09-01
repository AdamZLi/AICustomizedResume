"""
Section parsing service for resumes using deterministic heuristics
"""
import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class SectionParser:
    def __init__(self):
        # Section headings regex patterns (case-insensitive)
        self.section_patterns = {
            'summary': r'^(summary|professional summary|profile|objective|about)$',
            'experience': r'^(experience|work experience|employment|professional experience|career history)$',
            'projects': r'^(projects|project experience|key projects)$',
            'education': r'^(education|academic|academic background|qualifications)$',
            'certifications': r'^(certifications|certificates|licenses)$',
            'skills': r'^(skills|technologies|tech skills|technical skills|competencies|expertise)$',
            'additional': r'^(additional|other|miscellaneous|interests|hobbies|languages)$'
        }
        
        # Degree keywords for education classification
        self.degree_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'associate', 'diploma', 
            'degree', 'university', 'college', 'school', 'academy'
        ]
        
        # Date patterns for experience classification
        self.date_patterns = [
            r'\b\d{4}\b',  # Year
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',  # Month
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # MM/DD/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{2,4}\b'   # MM-DD-YYYY
        ]
        
        # Skills indicators
        self.skills_indicators = [
            r'[A-Za-z]+(?:\.js|\.py|\.java|\.cpp|\.net|\.sql|\.html|\.css)',
            r'\b[A-Z]{2,}\b',  # Acronyms like SQL, API, AWS
            r'[A-Za-z]+\s*[,;]\s*[A-Za-z]+'  # Comma/semicolon separated lists
        ]

    def split_resume_into_sections(self, text: str) -> Dict[str, str]:
        """
        Split resume text into logical sections using deterministic heuristics
        Returns: Dict[section_name, section_content]
        """
        lines = text.split('\n')
        sections = {}
        current_section = 'header'
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line is a section header
            section_name = self._identify_section_header(line)
            
            if section_name:
                # Save previous section
                if current_section != 'header' and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = section_name
                current_content = []
            else:
                # Add line to current section
                current_content.append(line)
        
        # Save the last section
        if current_section != 'header' and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # If no sections found, classify the entire text
        if not sections:
            sections = self._classify_entire_text(text)
        
        # Post-process sections
        sections = self._post_process_sections(sections)
        
        logger.info(f"Parsed resume into {len(sections)} sections: {list(sections.keys())}")
        return sections
    
    def _identify_section_header(self, line: str) -> str:
        """Identify if a line is a section header and return normalized section name"""
        line_upper = line.upper()
        
        # Check for exact matches with section patterns
        for section_name, pattern in self.section_patterns.items():
            if re.match(pattern, line_upper):
                return section_name
        
        return None
    
    def _classify_entire_text(self, text: str) -> Dict[str, str]:
        """Classify entire text when no clear sections are found"""
        text_lower = text.lower()
        
        # Check for education indicators
        if any(keyword in text_lower for keyword in self.degree_keywords):
            return {'education': text}
        
        # Check for experience indicators (dates)
        if any(re.search(pattern, text) for pattern in self.date_patterns):
            return {'experience': text}
        
        # Check for skills indicators
        if any(re.search(pattern, text) for pattern in self.skills_indicators):
            return {'skills': text}
        
        # Default to experience if no clear indicators
        return {'experience': text}
    
    def _post_process_sections(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Post-process sections to ensure quality and completeness"""
        processed_sections = {}
        
        for section_name, content in sections.items():
            if content and len(content.strip()) > 10:  # Minimum content threshold
                processed_sections[section_name] = content.strip()
        
        # Ensure we have at least one section
        if not processed_sections:
            processed_sections['experience'] = "No clear sections identified"
        
        return processed_sections
    
    def get_section_order(self) -> List[str]:
        """Get canonical section order for combining"""
        return ['summary', 'experience', 'projects', 'education', 'certifications', 'skills', 'additional']
    
    def get_section_header(self, section_name: str) -> str:
        """Get the display header for a section"""
        headers = {
            'summary': 'SUMMARY',
            'experience': 'WORKING EXPERIENCE',
            'projects': 'PROJECTS',
            'education': 'EDUCATION',
            'certifications': 'CERTIFICATIONS',
            'skills': 'SKILLS',
            'additional': 'ADDITIONAL INFORMATION'
        }
        return headers.get(section_name, section_name.upper())
