"""
Title Analyzer - Dynamic Scoring Module
Analyzes title quality based on measurable signals
"""
import re
from typing import Dict, List, Any
import logging

logger = logging.getLogger("title_analyzer")

class TitleAnalyzer:
    def __init__(self):
        self.technical_keywords = {
            'api', 'rest', 'graphql', 'database', 'sql', 'nosql', 'authentication', 'auth',
            'jwt', 'oauth', 'security', 'encryption', 'hash', 'bcrypt', 'microservice',
            'docker', 'kubernetes', 'ci/cd', 'pipeline', 'deployment', 'testing', 'unit',
            'integration', 'frontend', 'backend', 'fullstack', 'react', 'angular', 'vue',
            'node', 'python', 'java', 'golang', 'rust', 'typescript', 'javascript',
            'framework', 'library', 'sdk', 'cli', 'tool', 'system', 'service', 'server',
            'client', 'web', 'mobile', 'ios', 'android', 'cloud', 'aws', 'azure', 'gcp'
        }
    
    def analyze(self, title: str, description: str) -> Dict[str, Any]:
        """Analyze title and return SIGNALS ONLY (no scoring)"""
        words = title.lower().split()
        word_count = len(words)
        
        technical_keywords_found = self._get_technical_terms(words)
        duplicate_words = self._get_duplicate_words(words)
        shared_keywords = self._get_shared_keywords(title, description)
        
        tech_keyword_ratio = len(technical_keywords_found) / max(word_count, 1)
        # domain_relevance: how much of the title overlaps with description content
        domain_relevance = min(len(shared_keywords) / max(word_count, 1), 1.0)
        # clarity: penalize very short (<3 words) or very long (>12 words) titles
        if word_count < 3:
            clarity_score = 0.3
        elif word_count <= 12:
            clarity_score = 0.7 + min(len(technical_keywords_found) * 0.1, 0.3)
        else:
            clarity_score = 0.5
        
        return {
            'signals': {
                'technical_keywords': technical_keywords_found,
                'duplicate_words': duplicate_words,
                'shared_keywords': shared_keywords,
                'word_count': word_count,
                'technical_keyword_count': len(technical_keywords_found),
                'duplicate_word_count': len(duplicate_words)
            },
            'metrics': {
                'title_word_count': word_count,
                'technical_keyword_ratio': tech_keyword_ratio,
                'duplicate_word_ratio': len(duplicate_words) / max(word_count, 1),
                'domain_relevance': domain_relevance,
                'clarity_score': clarity_score
            }
        }
    
    def _calculate_technical_ratio(self, words: List[str]) -> float:
        """Calculate ratio of technical terms to total words"""
        if not words:
            return 0.0
        technical_count = sum(1 for word in words if word in self.technical_keywords)
        return technical_count / len(words)
    
    def _calculate_duplicate_penalty(self, words: List[str]) -> float:
        """Calculate penalty for repeated words"""
        if not words:
            return 0.0
        unique_words = set(words)
        repeated_count = len(words) - len(unique_words)
        return repeated_count / len(words)
    
    def _calculate_alignment_score(self, title: str, description: str) -> float:
        """Calculate alignment between title and description keywords"""
        title_words = set(re.findall(r'\b\w+\b', title.lower()))
        desc_words = set(re.findall(r'\b\w+\b', description.lower()))
        
        if not title_words:
            return 0.0
        
        shared_count = len(title_words.intersection(desc_words))
        return min(shared_count / len(title_words), 1.0)
    
    def _get_technical_terms(self, words: List[str]) -> List[str]:
        """Get list of technical terms found in title"""
        return [word for word in words if word in self.technical_keywords]
    
    def _get_duplicate_words(self, words: List[str]) -> List[str]:
        """Get list of duplicate words"""
        seen = set()
        duplicates = []
        for word in words:
            if word in seen and word not in duplicates:
                duplicates.append(word)
            seen.add(word)
        return duplicates
    
    def _get_shared_keywords(self, title: str, description: str) -> List[str]:
        """Get keywords shared between title and description"""
        title_words = set(re.findall(r'\b\w+\b', title.lower()))
        desc_words = set(re.findall(r'\b\w+\b', description.lower()))
        return list(title_words.intersection(desc_words))