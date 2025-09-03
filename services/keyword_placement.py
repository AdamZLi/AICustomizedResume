"""
Intelligent keyword placement service for resumes
"""
import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class KeywordPlacement:
    keyword: str
    section: str
    suggested_location: str
    context: str
    confidence: float
    placement_type: str  # 'enhance', 'replace', 'add'

class KeywordPlacementService:
    def __init__(self):
        # Keyword categories for better placement
        self.keyword_categories = {
            'technical_skills': [
                'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'aws', 'docker',
                'kubernetes', 'machine learning', 'ai', 'data analysis', 'agile', 'scrum',
                'typescript', 'angular', 'vue', 'php', 'ruby', 'go', 'rust', 'c++', 'c#',
                'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'kafka',
                'spark', 'hadoop', 'tensorflow', 'pytorch', 'scikit-learn'
            ],
            'leadership': [
                'lead', 'manage', 'direct', 'supervise', 'mentor', 'team', 'strategy',
                'vision', 'executive', 'senior', 'principal', 'leadership', 'coordinate',
                'oversee', 'guide', 'facilitate', 'orchestrate'
            ],
            'metrics': [
                'increase', 'decrease', 'improve', 'reduce', 'grow', 'scale', 'optimize',
                'efficiency', 'performance', 'revenue', 'cost', 'time', 'quality',
                'productivity', 'throughput', 'accuracy', 'savings', 'growth'
            ],
            'methodologies': [
                'agile', 'scrum', 'kanban', 'waterfall', 'lean', 'six sigma', 'devops',
                'ci/cd', 'tdd', 'bdd', 'design thinking', 'sprint', 'retrospective',
                'standup', 'planning', 'estimation'
            ],
            'tools_platforms': [
                'jira', 'confluence', 'slack', 'teams', 'zoom', 'salesforce', 'hubspot',
                'tableau', 'power bi', 'excel', 'google analytics', 'github', 'gitlab',
                'bitbucket', 'jenkins', 'circleci', 'travis', 'terraform', 'ansible'
            ]
        }
        
        # Section-specific placement strategies
        self.section_strategies = {
            'summary': {
                'high_priority': ['leadership', 'technical_skills'],
                'placement': 'enhance_existing',
                'max_keywords': 3
            },
            'experience': {
                'high_priority': ['metrics', 'leadership', 'technical_skills'],
                'placement': 'enhance_bullets',
                'max_keywords': 5
            },
            'skills': {
                'high_priority': ['technical_skills', 'tools_platforms'],
                'placement': 'add_to_list',
                'max_keywords': 8
            },
            'projects': {
                'high_priority': ['technical_skills', 'metrics'],
                'placement': 'enhance_descriptions',
                'max_keywords': 4
            }
        }
    
    def analyze_keyword_placements(
        self, 
        resume_text: str, 
        keywords: List[str], 
        sections: Dict[str, str]
    ) -> List[KeywordPlacement]:
        """
        Analyze where keywords should be placed in the resume
        Returns: List of KeywordPlacement objects
        """
        placements = []
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Categorize the keyword
            category = self._categorize_keyword(keyword_lower)
            
            # Find best placement for this keyword
            best_placement = self._find_best_placement(
                keyword, category, sections, resume_text
            )
            
            if best_placement:
                placements.append(best_placement)
        
        # Sort by confidence and section priority
        placements.sort(key=lambda x: (x.confidence, self._get_section_priority(x.section)), reverse=True)
        
        logger.info(f"Found {len(placements)} keyword placements")
        return placements
    
    def _categorize_keyword(self, keyword: str) -> str:
        """Categorize a keyword based on its type"""
        keyword_lower = keyword.lower()
        
        for category, keywords in self.keyword_categories.items():
            if any(kw in keyword_lower or keyword_lower in kw for kw in keywords):
                return category
        return 'general'
    
    def _find_best_placement(
        self, 
        keyword: str, 
        category: str, 
        sections: Dict[str, str], 
        full_text: str
    ) -> Optional[KeywordPlacement]:
        """Find the best placement for a keyword"""
        best_placement = None
        best_score = 0
        
        for section_name, section_content in sections.items():
            if section_name not in self.section_strategies:
                continue
            
            strategy = self.section_strategies[section_name]
            
            # Check if keyword already exists in this section
            if keyword.lower() in section_content.lower():
                continue
            
            # Calculate placement score
            score = self._calculate_placement_score(
                keyword, category, section_name, section_content, strategy
            )
            
            if score > best_score:
                best_score = score
                best_placement = KeywordPlacement(
                    keyword=keyword,
                    section=section_name,
                    suggested_location=self._get_suggested_location(section_name, keyword),
                    context=self._get_context(section_content, keyword),
                    confidence=score,
                    placement_type=self._get_placement_type(section_name, keyword)
                )
        
        return best_placement
    
    def _calculate_placement_score(
        self, 
        keyword: str, 
        category: str, 
        section_name: str, 
        section_content: str, 
        strategy: Dict
    ) -> float:
        """Calculate how well a keyword fits in a section"""
        score = 0.0
        
        # Base score for section priority
        if category in strategy.get('high_priority', []):
            score += 0.3
        
        # Score based on section content relevance
        relevance_score = self._calculate_content_relevance(keyword, section_content)
        score += relevance_score * 0.25
        
        # Score based on section length (prefer sections with more content)
        length_score = min(len(section_content) / 1000, 1.0)  # Normalize to 0-1
        score += length_score * 0.15
        
        # Score based on keyword frequency in section (prefer sections with related terms)
        frequency_score = self._calculate_keyword_frequency(keyword, section_content)
        score += frequency_score * 0.1
        
        # Bonus for skills section for technical keywords
        if section_name == 'skills' and category in ['technical_skills', 'tools_platforms']:
            score += 0.2
        
        # Bonus for experience section for leadership and metrics keywords
        if section_name == 'experience' and category in ['leadership', 'metrics']:
            score += 0.2
        
        # Bonus for summary section for leadership keywords
        if section_name == 'summary' and category == 'leadership':
            score += 0.15
        
        return min(score, 1.0)
    
    def _calculate_content_relevance(self, keyword: str, content: str) -> float:
        """Calculate how relevant the content is to the keyword"""
        content_lower = content.lower()
        keyword_lower = keyword.lower()
        
        # Check for related terms
        related_terms = self._get_related_terms(keyword_lower)
        matches = sum(1 for term in related_terms if term in content_lower)
        
        return min(matches / len(related_terms), 1.0) if related_terms else 0.0
    
    def _calculate_keyword_frequency(self, keyword: str, content: str) -> float:
        """Calculate frequency of related keywords in content"""
        content_lower = content.lower()
        keyword_lower = keyword.lower()
        
        # Get related keywords
        related_terms = self._get_related_terms(keyword_lower)
        
        # Count occurrences
        total_occurrences = 0
        for term in related_terms:
            total_occurrences += len(re.findall(r'\b' + re.escape(term) + r'\b', content_lower))
        
        # Normalize by content length
        return min(total_occurrences / max(len(content.split()), 1), 1.0)
    
    def _get_related_terms(self, keyword: str) -> List[str]:
        """Get related terms for a keyword"""
        # This is a simplified version - could be expanded with synonyms
        related_terms = [keyword]
        
        # Add common variations
        if ' ' in keyword:
            related_terms.append(keyword.replace(' ', '-'))
            related_terms.append(keyword.replace(' ', '_'))
        
        # Add common abbreviations
        if keyword == 'machine learning':
            related_terms.extend(['ml', 'ai', 'artificial intelligence'])
        elif keyword == 'data analysis':
            related_terms.extend(['analytics', 'data science'])
        elif keyword == 'project management':
            related_terms.extend(['pm', 'program management'])
        
        return list(set(related_terms))
    
    def _get_suggested_location(self, section_name: str, keyword: str) -> str:
        """Get suggested location for keyword placement"""
        if section_name == 'summary':
            return "Enhance professional summary with keyword"
        elif section_name == 'experience':
            return "Add to relevant job description bullet points"
        elif section_name == 'skills':
            return "Add to technical skills section"
        elif section_name == 'projects':
            return "Enhance project descriptions"
        else:
            return f"Add to {section_name} section"
    
    def _get_context(self, content: str, keyword: str) -> str:
        """Get context around where keyword should be placed"""
        # Find the most relevant sentence or bullet point
        sentences = re.split(r'[.!?]+', content)
        
        best_sentence = ""
        best_score = 0
        
        for sentence in sentences:
            if len(sentence.strip()) < 10:
                continue
            
            # Calculate relevance score for this sentence
            relevance = self._calculate_content_relevance(keyword, sentence)
            if relevance > best_score:
                best_score = relevance
                best_sentence = sentence.strip()
        
        return best_sentence[:100] + "..." if len(best_sentence) > 100 else best_sentence
    
    def _get_placement_type(self, section_name: str, keyword: str) -> str:
        """Get the type of placement needed"""
        if section_name == 'skills':
            return 'add'
        elif section_name == 'summary':
            return 'enhance'
        else:
            return 'enhance'
    
    def _get_section_priority(self, section_name: str) -> int:
        """Get priority order for sections (lower = higher priority)"""
        priorities = {
            'summary': 1,
            'experience': 2,
            'skills': 3,
            'projects': 4,
            'education': 5,
            'certifications': 6,
            'additional': 7
        }
        return priorities.get(section_name, 8)
    
    def generate_placement_instructions(
        self, 
        placements: List[KeywordPlacement]
    ) -> Dict[str, List[str]]:
        """Generate specific instructions for each section"""
        instructions = {}
        
        for placement in placements:
            section = placement.section
            if section not in instructions:
                instructions[section] = []
            
            instruction = self._create_placement_instruction(placement)
            instructions[section].append(instruction)
        
        return instructions
    
    def _create_placement_instruction(self, placement: KeywordPlacement) -> str:
        """Create a specific instruction for placing a keyword"""
        if placement.section == 'summary':
            return f"Enhance the professional summary to include '{placement.keyword}' naturally"
        elif placement.section == 'experience':
            return f"Add '{placement.keyword}' to relevant job description bullet points"
        elif placement.section == 'skills':
            return f"Add '{placement.keyword}' to the skills section"
        elif placement.section == 'projects':
            return f"Incorporate '{placement.keyword}' into project descriptions"
        else:
            return f"Add '{placement.keyword}' to the {placement.section} section"
