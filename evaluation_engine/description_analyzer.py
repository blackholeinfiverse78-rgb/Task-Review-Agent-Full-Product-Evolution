"""
Description Analyzer - Dynamic Scoring Module
Analyzes description quality based on measurable features
"""
import re
from typing import Dict, List, Any
import logging

logger = logging.getLogger("description_analyzer")

class DescriptionAnalyzer:
    def __init__(self):
        self.technical_terms = {
            'api', 'rest', 'graphql', 'database', 'sql', 'nosql', 'authentication', 'auth',
            'jwt', 'oauth', 'security', 'encryption', 'hash', 'bcrypt', 'microservice',
            'docker', 'kubernetes', 'ci/cd', 'pipeline', 'deployment', 'testing', 'unit',
            'integration', 'frontend', 'backend', 'fullstack', 'react', 'angular', 'vue',
            'node', 'python', 'java', 'golang', 'rust', 'typescript', 'javascript',
            'framework', 'library', 'sdk', 'cli', 'tool', 'system', 'service', 'server',
            'client', 'web', 'mobile', 'ios', 'android', 'cloud', 'aws', 'azure', 'gcp',
            'algorithm', 'optimization', 'performance', 'scalability', 'architecture',
            'design', 'pattern', 'solid', 'dry', 'kiss', 'mvc', 'mvp', 'mvvm'
        }
        
        self.step_indicators = [
            'step', 'phase', 'stage', 'first', 'second', 'third', 'next', 'then',
            'finally', 'objective', 'requirement', 'constraint', 'goal', 'target'
        ]
    
    def analyze(self, description: str) -> Dict[str, Any]:
        """Analyze description and return SIGNALS ONLY (no scoring)"""
        words = re.findall(r'\b\w+\b', description.lower())
        sentences = re.split(r'[.!?]+', description)
        
        word_count = len(words)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # Extract SIGNALS only - NO SCORING
        technical_terms_found = self._get_technical_terms(words)
        step_indicators_found = self._get_step_indicators(words)
        code_block_count = self._count_code_blocks(description)
        section_headers = self._count_section_headers(description)
        
        return {
            'signals': {
                'technical_terms_found': technical_terms_found,
                'step_indicators_found': step_indicators_found,
                'has_code_blocks': code_block_count > 0,
                'has_structure': section_headers > 0 or len(step_indicators_found) > 0,
                'code_block_count': code_block_count,
                'section_headers': section_headers
            },
            'metrics': {
                'word_count': word_count,
                'sentence_count': sentence_count,
                'technical_term_ratio': len(technical_terms_found) / max(word_count, 1),
                'step_indicator_count': len(step_indicators_found),
                'content_depth': min(word_count / 150, 1.0),
                'structure_score': min((section_headers + len(step_indicators_found)) / 8, 1.0),
                'technical_density': min((len(technical_terms_found) / max(word_count, 1)) / 0.25, 1.0)
            }
        }
    
    def _calculate_technical_ratio(self, words: List[str]) -> float:
        """Calculate ratio of technical terms to total words"""
        if not words:
            return 0.0
        technical_count = sum(1 for word in words if word in self.technical_terms)
        return technical_count / len(words)
    
    def _count_step_indicators(self, words: List[str], description: str = "") -> int:
        """Count step/process indicators including numbered list items"""
        word_hits = sum(1 for word in words if word in self.step_indicators)
        # Count numbered list lines: lines starting with '1.' '2.' etc.
        numbered_items = len(re.findall(r'^\s*\d+\.', description, re.MULTILINE))
        return word_hits + numbered_items
    
    def _count_code_blocks(self, description: str) -> int:
        """Count code blocks (``` or ` patterns)"""
        code_block_pattern = r'```[\s\S]*?```|`[^`]+`'
        return len(re.findall(code_block_pattern, description))
    
    def _count_section_headers(self, description: str) -> int:
        """Count section headers (# patterns or ALL CAPS lines)"""
        lines = description.split('\n')
        header_count = 0
        
        for line in lines:
            line = line.strip()
            # Markdown headers
            if line.startswith('#'):
                header_count += 1
            # ALL CAPS headers (> 5 chars)
            elif line.isupper() and len(line) > 5:
                header_count += 1
        
        return header_count
    
    def _calculate_clarity_score(self, sentence_count: int, word_count: int) -> float:
        """Calculate clarity based on sentence/word ratio"""
        if word_count == 0:
            return 0.0
        # Markdown descriptions have many short lines; use a wider acceptable band
        avg_words_per_sentence = word_count / max(sentence_count, 1)
        if 8 <= avg_words_per_sentence <= 30:
            return 1.0
        elif 5 <= avg_words_per_sentence < 8 or 30 < avg_words_per_sentence <= 40:
            return 0.7
        else:
            return 0.4
    
    def _get_technical_terms(self, words: List[str]) -> List[str]:
        """Get list of technical terms found"""
        return [word for word in words if word in self.technical_terms]
    
    def _get_step_indicators(self, words: List[str]) -> List[str]:
        """Get list of step indicators found"""
        return [word for word in words if word in self.step_indicators]