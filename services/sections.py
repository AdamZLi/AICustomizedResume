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
            'summary': r'^(summary|professional summary|profile|objective|about|executive summary)$',
            'experience': r'^(experience|work experience|employment|professional experience|career history|work history|employment history)$',
            'projects': r'^(projects|project experience|key projects|notable projects|selected projects)$',
            'education': r'^(education|academic|academic background|qualifications|academic qualifications)$',
            'certifications': r'^(certifications|certificates|licenses|professional certifications)$',
            'skills': r'^(skills|technologies|tech skills|technical skills|competencies|expertise|technical competencies|core competencies)$',
            'additional': r'^(additional|other|miscellaneous|interests|hobbies|languages|activities|volunteer)$'
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
        line_clean = re.sub(r'[^\w\s]', '', line_upper).strip()
        
        # Check for exact matches with section patterns
        for section_name, pattern in self.section_patterns.items():
            if re.match(pattern, line_upper) or re.match(pattern, line_clean):
                return section_name
        
        # Check for common variations and abbreviations
        if any(word in line_upper for word in ['EXP', 'WORK EXP', 'PROF EXP']):
            return 'experience'
        elif any(word in line_upper for word in ['SKILLS', 'TECH', 'TECHNOLOGIES']):
            return 'skills'
        elif any(word in line_upper for word in ['EDU', 'ACADEMIC']):
            return 'education'
        elif any(word in line_upper for word in ['PROJ', 'PROJECTS']):
            return 'projects'
        elif any(word in line_upper for word in ['CERT', 'CERTIFICATIONS']):
            return 'certifications'
        elif any(word in line_upper for word in ['SUMMARY', 'PROFILE', 'OBJECTIVE']):
            return 'summary'
        
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


class ResumeSectionService:
    def __init__(self):
        self.section_parser = SectionParser()
    
    def get_best_section_for_keywords(self, full_text: str, keywords: List[str]) -> Tuple[str, str]:
        """
        Find the best section for incorporating the given keywords
        
        Args:
            full_text: Full resume text
            keywords: Keywords to incorporate
            
        Returns:
            Tuple of (section_name, section_text)
        """
        try:
            # Parse sections
            sections = self.section_parser.split_resume_into_sections(full_text)
            
            if not sections:
                # Fallback: return the entire text as experience section
                return 'experience', full_text
            
            # Score each section based on keyword relevance
            section_scores = {}
            
            for section_name, section_text in sections.items():
                score = self._calculate_keyword_relevance(section_text, keywords)
                section_scores[section_name] = score
            
            # Find the section with highest score
            best_section = max(section_scores.items(), key=lambda x: x[1])
            
            # If no good match, prefer experience or skills sections
            if best_section[1] < 0.1:  # Low relevance threshold
                if 'experience' in sections:
                    return 'experience', sections['experience']
                elif 'skills' in sections:
                    return 'skills', sections['skills']
                else:
                    # Return first available section
                    first_section = list(sections.items())[0]
                    return first_section[0], first_section[1]
            
            return best_section[0], sections[best_section[0]]
            
        except Exception as e:
            logger.error(f"Error finding best section for keywords: {str(e)}")
            # Fallback: return experience section or entire text
            return 'experience', full_text
    
    def get_section_by_name(self, full_text: str, section_name: str) -> Tuple[str, str]:
        """
        Get a specific section by name
        
        Args:
            full_text: Full resume text
            section_name: Name of the section to retrieve
            
        Returns:
            Tuple of (section_name, section_text)
        """
        try:
            # Parse sections
            sections = self.section_parser.split_resume_into_sections(full_text)
            
            if section_name in sections:
                return section_name, sections[section_name]
            
            # If section not found, try to find similar sections
            for name, content in sections.items():
                if section_name.lower() in name.lower() or name.lower() in section_name.lower():
                    return name, content
            
            # If still not found, return the first available section
            if sections:
                first_section = list(sections.items())[0]
                return first_section[0], first_section[1]
            
            # Last resort: return entire text
            return 'content', full_text
            
        except Exception as e:
            logger.error(f"Error getting section by name: {str(e)}")
            return 'content', full_text
    
    def _calculate_keyword_relevance(self, section_text: str, keywords: List[str]) -> float:
        """
        Calculate how relevant a section is for the given keywords
        
        Args:
            section_text: Text content of the section
            keywords: Keywords to check relevance against
            
        Returns:
            Relevance score between 0 and 1
        """
        try:
            if not section_text or not keywords:
                return 0.0
            
            section_lower = section_text.lower()
            total_score = 0.0
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # Check for exact matches
                if keyword_lower in section_lower:
                    total_score += 1.0
                
                # Check for partial matches (word boundaries)
                words = section_lower.split()
                if any(keyword_lower in word or word in keyword_lower for word in words):
                    total_score += 0.5
                
                # Check for related terms (e.g., "Python" vs "Python developer")
                if any(word in keyword_lower or keyword_lower in word for word in words):
                    total_score += 0.3
            
            # Normalize score
            max_possible_score = len(keywords) * 1.8  # Max score per keyword
            if max_possible_score > 0:
                return min(total_score / max_possible_score, 1.0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating keyword relevance: {str(e)}")
            return 0.0

